"""Run validation (Gemini gets question+options only; compare with OpenAI answer) and list validated questions."""
import json
import uuid
from bson import ObjectId
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from common.middleware import authenticate, restrict

from .models import ValidatedQuestion
from .helpers import parse_gemini_answer_response, gemini_text_answers_to_indices, answers_match
from django.http import JsonResponse, HttpResponse
import csv


def remap_openai_answers_to_current_options(openai_answers, options_text):
    """
    Remap OpenAI stored indices to CURRENT option positions using text match.
    """
    remapped = []

    for ans in openai_answers:
        try:
            old_idx = int(ans) - 1  # OpenAI is 1-based
            if 0 <= old_idx < len(options_text):
                correct_text = options_text[old_idx].strip().lower()

                # find this text in CURRENT options
                for i, opt in enumerate(options_text):
                    if opt.strip().lower() == correct_text:
                        remapped.append(str(i + 1))  # keep 1-based
                        break
        except Exception:
            pass

    return remapped



def _get_validated_by_id(validated_id):
    """Get ValidatedQuestion by id; return None if invalid."""
    try:
        return ValidatedQuestion.objects(id=ObjectId(validated_id)).first()
    except Exception:
        return None


def _get_generated_questions_for_validation(ids=None):
    """Get GeneratedQuestion list by ids or latest batch. Returns list of GeneratedQuestion docs."""
    from question_generator.models import GeneratedQuestion
    if ids:
        from bson import ObjectId
        qs = []
        for qid in ids:
            try:
                q = GeneratedQuestion.objects(id=ObjectId(qid)).first()
                if q:
                    qs.append(q)
            except Exception:
                pass
        qs.sort(key=lambda x: x.created_at)
        return qs
    latest = GeneratedQuestion.objects.order_by("-created_at").first()
    if not latest:
        return []
    batch_id = getattr(latest, "batch_id", None) or ""
    if not batch_id:
        return list(GeneratedQuestion.objects.order_by("-created_at")[:100])
    return list(GeneratedQuestion.objects(batch_id=batch_id).order_by("created_at"))



@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def run_validation(request):
    """
    Validate generated questions with Gemini.
    For each question: send ONLY question_text + options to Gemini (Prompt 3). Do NOT send OpenAI answer.
    Gemini returns its answer. Compare with OpenAI correct_answers. Save to ValidatedQuestion.
    Body: { ids?: string[] }. If ids omitted, use latest generated batch.
    """
    try:
        from settings_app.models import AdminSettings
        from parsing_suite.helpers import get_gemini_key, get_valid_gemini_model
        import uuid

        data = request.data or {}  # ← move this up!
        print("data from frontend : ",data)
        session_id = data.get("session_id")
        print("session_id : ",session_id)
        settings_obj = AdminSettings.objects.first() or AdminSettings()
        key = get_gemini_key(settings_obj)
        if not key:
            return JsonResponse({
                "success": False,
                "error": "GEMINI_API_KEY not set. Set it in Admin Settings or .env.",
            }, status=400)

        prompts = getattr(settings_obj, "prompts", {}) or {}
        prompt3 = prompts.get("prompt3", {})
        validation_prompt = (prompt3.get("prompt", "") if prompt3 else "").strip()
        if not validation_prompt:
            return JsonResponse({
                "success": False,
                "error": "Prompt 3 (Validate Generated Answer) is not set. Set it in Admin / Configuration.",
            }, status=400)

        data = request.data or {}
        ids = data.get("ids")
        if ids is not None and not isinstance(ids, list):
            ids = [ids]
        qs = _get_generated_questions_for_validation(ids)
        if not qs:
            return JsonResponse({
                "success": True,
                "message": "No generated questions to validate.",
                "validated_count": 0,
                "batch_id": "",
            })

        # When revalidating selected: update existing latest batch (delete old, add new). Otherwise new batch.
        # run_batch_id = str(uuid.uuid4())
        if ids:
            latest = ValidatedQuestion.objects(session_id=session_id).order_by("-validated_at").first()
            if latest:
                session_id = getattr(latest, "session_id", None) or ""
                if session_id:
                    gen_ids = [str(q.id) for q in qs]
                    ValidatedQuestion.objects(session_id=session_id, generated_question_id__in=gen_ids).delete()

        try:
            import google.generativeai as genai
        except ImportError:
            return JsonResponse({
                "success": False,
                "error": "Gemini API not available. Install google-generativeai.",
            }, status=500)

        genai.configure(api_key=key)
        model_name = get_valid_gemini_model(
            getattr(settings_obj, "gemini_model_selector", None), genai
        )
        if not model_name.startswith("models/"):
            model_name = f"models/{model_name}"
        model = genai.GenerativeModel(model_name)
        temp = float(getattr(settings_obj, "temperature", 0.3))
        # 🔥 ensure session exists (ADD THIS BLOCK)
        # if not request.session.session_key:
        #     request.session.create()

        # session_id = request.session.session_key
        # session_name = request.session.get("session_name", "validation_session")
        print(f"Session ID: {session_id}")

        saved = 0
        for q in qs:
            # 🔹 Use GeneratedQuestion itself for validation
            question_text = getattr(q, "question_text", "") or ""
            options = getattr(q, "options", []) or []
            # 🔹 Build options text for OpenAI/Gemini remapping
            # options_text = [str(o) for o in options]
            # If options are dicts with 'text' + 'explanation'
            options_text = [o.get("text", str(o)) if isinstance(o, dict) else str(o) for o in options]
            # Build a numbered options string for Gemini
            options_str = "\n".join([f"{i+1}. {text}" for i, text in enumerate(options_text)])
            
            # 🔹 Remap OpenAI answers against input question options
            raw_openai_answers = list(getattr(q, "correct_answers", []) or [])
            openai_answers = remap_openai_answers_to_current_options(
                raw_openai_answers,
                options_text
            )
            
            # Now you can build Gemini prompt with input question
            prompt = (
                validation_prompt
                + "\n\nQuestion:\n"
                + question_text
                + "\n\nOptions:\n"
                + options_str
            )

            # 🔹 Print the prompt being sent to Gemini
            print("=== Gemini Prompt ===") 
            print(prompt)
            print("====================\n")

            try:
                response = model.generate_content(prompt, generation_config={"temperature": temp})
                text = (response.text or "").strip() if hasattr(response, "text") else ""
                if not text and hasattr(response, "candidates") and response.candidates:
                    part = response.candidates[0].content.parts[0] if response.candidates[0].content.parts else None
                    text = (part.text if part else "").strip()
            except Exception as e:
                text = ""
                print(f"Error from Gemini: {e}")

            # 🔹 Print raw Gemini response
            print("=== Raw Gemini Response ===")
            print(text)
            print("===========================\n")

            # gemini_texts = parse_gemini_answer_response(text) if text else []
            # # Gemini returns option text(s); convert to 1-based indices to compare with OpenAI
            # gemini_answers = gemini_text_answers_to_indices(gemini_texts, options_text)

            gemini_answers = parse_gemini_answer_response(text)

           
            # 🔹 Print parsed a answers and comparison
            print("OpenAI Answers:", openai_answers)
            print("Gemini Answers (indices):", gemini_answers)
            print("Match:", answers_match(openai_answers, gemini_answers))
            print("---------------------------\n")

            is_valid = answers_match(openai_answers, gemini_answers)
            explanation = getattr(q, "explanation", "") or ""
            ValidatedQuestion(
                generated_question_id=str(q.id),
                question_text=question_text,
                options=options,
                openai_answers=openai_answers,
                session_id=session_id,
                gemini_answers=gemini_answers,
                explanation=explanation,
                is_valid=is_valid,
                # batch_id=run_batch_id,
                # session_name=session_name
                
            ).save()
            saved += 1

        return JsonResponse({
            "success": True,
            "message": f"Validated {saved} question(s). Open Validated Questions tab to see OpenAI vs Gemini answers.",
            "validated_count": saved,
            "session_id": session_id,
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['GET'])
@authenticate
@restrict(['admin'])
def get_validated_questions(request):
    """Return validated questions (latest batch first). Optional ?batch_id= for a specific run."""
    try:
        session_id = (request.GET.get("session_id")).strip()
        print("session_id : ",session_id)
        if session_id:
            qs = ValidatedQuestion.objects(session_id=session_id).order_by("validated_at")
        else:
            latest = ValidatedQuestion.objects(session_id=session_id).order_by("-validated_at").first()
            if not latest:
                return Response({"success": True, "questions": [], "count": 0})
            session_id = getattr(latest, "session_id", None) or ""
            if not session_id:
                return Response({"success": True, "questions": [], "count": 0})
            else:
                qs = ValidatedQuestion.objects(session_id=session_id).order_by("validated_at")
        out = []
        for q in qs:
            explanation = getattr(q, "explanation", "") or ""
            gen_id = getattr(q, "generated_question_id", "") or ""
            if not explanation and gen_id:
                try:
                    from question_generator.models import GeneratedQuestion
                    gen_q = GeneratedQuestion.objects(id=ObjectId(gen_id)).first()
                    if gen_q:
                        explanation = getattr(gen_q, "explanation", "") or ""
                except Exception:
                    pass
            out.append({
                "id": str(q.id),
                "generated_question_id": gen_id,
                "question_text": getattr(q, "question_text", "") or "",
                "options": getattr(q, "options", []) or [],
                "openai_answers": getattr(q, "openai_answers", []) or [],
                "gemini_answers": getattr(q, "gemini_answers", []) or [],
                "explanation": explanation,
                "is_valid": getattr(q, "is_valid", False),
                "validated_at": getattr(q, "validated_at", None),
                "session_id": getattr(q, "session_id", None),
            })
        return Response({"success": True, "questions": out, "count": len(out)})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def update_validated_question(request, validated_id):
    """Update a validated question: question_text, options, openai_answers, gemini_answers, explanation, is_valid."""
    try:
        q = _get_validated_by_id(validated_id)
        if not q:
            return JsonResponse({"success": False, "error": "Validated question not found."}, status=404)
        data = request.data or {}
        if "question_text" in data and data["question_text"] is not None:
            q.question_text = (data["question_text"] or "").strip() or q.question_text
        if "options" in data and isinstance(data["options"], list):
            opts_clean = []
            for o in data["options"]:
                if isinstance(o, dict):
                    opts_clean.append({
                        "text": str(o.get("text", "") or ""),
                        "explanation": str(o.get("explanation", "") or ""),
                    })
                else:
                    opts_clean.append({"text": str(o), "explanation": ""})
            q.options = opts_clean
        if "openai_answers" in data and isinstance(data["openai_answers"], list):
            q.openai_answers = [str(a) for a in data["openai_answers"]]
        if "gemini_answers" in data and isinstance(data["gemini_answers"], list):
            q.gemini_answers = [str(a) for a in data["gemini_answers"]]
        if "explanation" in data and data["explanation"] is not None:
            q.explanation = str(data["explanation"] or "")
        if "is_valid" in data:
            q.is_valid = bool(data["is_valid"])
        q.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def delete_validated_question(request, validated_id):
    """Delete a validated question."""
    try:
        q = _get_validated_by_id(validated_id)
        if not q:
            return JsonResponse({"success": False, "error": "Validated question not found."}, status=404)
        q.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def bulk_delete_validated_questions(request):
    """Delete multiple validated questions by ids."""
    try:
        data = request.data or {}
        ids = data.get("ids") or []
        if not isinstance(ids, list):
            return JsonResponse({"success": False, "error": "ids must be a list."}, status=400)
        deleted = 0
        for vid in ids:
            q = _get_validated_by_id(vid)
            if q:
                q.delete()
                deleted += 1
        return JsonResponse({"success": True, "deleted_count": deleted})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)



from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view
import csv

@api_view(['GET'])
@authenticate
@restrict(['admin'])
def download_validated_questions_csv(request):
    """
    Download validated questions as CSV (session-based).
    Safe: won't crash if options are missing or session_name is missing.
    """
    # Ensure session exists
    session_id = request.GET.get("session_id")
    print(f"Session ID: {session_id}")

    # Fetch validated questions for this session
    questions = list(ValidatedQuestion.objects.filter(session_id=session_id))

    if not questions:
        return JsonResponse(
            {"error": "No validated questions for this session"},
            status=404
        )

    # Use session_id as filename (always exists)
    # session_name = getattr(questions[0], "session_name", None) or session_id

    # Helper function for question type
    def get_question_type(q):
        answers = q.openai_answers or q.gemini_answers or []
        return "single-correct" if len(answers) <= 1 else "multiple-correct"

    # Create CSV response
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="validated_questions_{session_id}.csv"'
    )

    writer = csv.writer(response)

    # Safe: find max number of options
    max_options = max(len(q.options or []) for q in questions)

    # Header
    header = ["question_text", "question_type"]
    for i in range(1, max_options + 1):
        header.extend([f"option{i}", f"option{i}_explanation"])
    header.extend(["correct_answers", "overall_explanation"])
    writer.writerow(header)

    # Rows
    for q in questions:
        row = [q.question_text or "", get_question_type(q)]

        options = q.options or []
        for opt in options:
            if isinstance(opt, dict):
                row.append(opt.get("text", ""))
                row.append(opt.get("explanation", ""))
            else:
                row.append(str(opt))
                row.append("")

        # Pad missing options
        for _ in range(max_options - len(options)):
            row.extend(["", ""])

        correct_answers = q.openai_answers or q.gemini_answers or []
        row.append(",".join(map(str, correct_answers)))
        row.append(q.explanation or "")

        writer.writerow(row)

    return response
