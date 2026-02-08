"""Generate questions from input (OpenAI) and list generated questions."""
import json
import re
import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from common.middleware import authenticate, restrict
from bson import ObjectId

from .models import GeneratedQuestion
from .helpers import get_openai_key, parse_generated_response


def _get_generated_by_id(question_id):
    """Get GeneratedQuestion by id; return None if invalid."""
    try:
        return GeneratedQuestion.objects(id=ObjectId(question_id)).first()
    except Exception:
        return None


def _question_type_from_correct_answers(correct_answers):
    """Return 'single-correct' or 'multiple-correct' from correct_answers length."""
    n = len(correct_answers) if correct_answers else 0
    return "multiple-correct" if n > 1 else "single-correct"


def _correct_answers_to_option_numbers(options, correct_answers):
    """
    Map correct_answers (option text or "1"/"2" or "A"/"B") to option numbers 1, 2, 3...
    Returns a string like "1, 3" or "2" so the frontend can show exactly what OpenAI meant.
    """
    if not correct_answers:
        return ""
    opts = []
    print("options:", options)
    
    for o in (options or []):
        if isinstance(o, dict):
            opts.append((o.get("text") or o.get("value") or "").strip())
        else:
            opts.append(str(o).strip())
    numbers = []
    for ans in correct_answers:
        s = (str(ans) or "").strip()
        if not s:
            continue
        # Exact or normalized match (whitespace, case)
        def _norm(txt):
            if not txt:
                return ""
            return re.sub(r"\s+", " ", str(txt).strip().lower().replace("\n", " ").replace("\r", " "))
        norm_s = _norm(s)
        for i, t in enumerate(opts):
            if t == s or _norm(t) == norm_s:
                numbers.append(i + 1)
                break
        else:
            # Substring match
            for i, t in enumerate(opts):
                if t and s and (norm_s in _norm(t) or _norm(t) in norm_s):
                    numbers.append(i + 1)
                    break
            else:
                # Digit: treat as 1-based option number
                if s.isdigit():
                    num = int(s)
                    if 1 <= num <= len(opts):
                        numbers.append(num)
                # Single letter A,B,C
                elif len(s) == 1 and s.isalpha():
                    num = ord(s.upper()) - 64
                    if 1 <= num <= len(opts):
                        numbers.append(num)
    unique = sorted(set(n for n in numbers if 1 <= n <= len(opts)))
    return ", ".join(str(n) for n in unique) if unique else ""


def _get_input_questions_for_session(session_id):
    """Get input questions from parsing_suite for given batch_id."""
    from parsing_suite.models import ParsedInputQuestion
    if not (session_id or "").strip():
        latest = ParsedInputQuestion.objects.order_by("-created_at").first()
        session_id = (getattr(latest, "session_id", None) or "").strip()
    if not session_id:
        return [], None
    qs = ParsedInputQuestion.objects(session_id=session_id).order_by("created_at")
    out = []
    for q in qs:
        opts = getattr(q, 'options', []) or []
        opts = [o.get("text", str(o)) if isinstance(o, dict) else str(o) for o in opts]
        out.append({
            "id": str(q.id),          # <-- ADD THIS LINE
            "question_text": q.question_text,
            "options": opts
        })

    return out, session_id


import random

def shuffle_options_and_correct(options, correct_answers):
    """
    options: list of {"text": "...", "explanation": "..."}
    correct_answers: list of 1-based indexes
    Returns: shuffled_options, new_correct_answers
    """
    indexed = list(enumerate(options, start=1))
    random.shuffle(indexed)

    new_options = []
    new_correct = []

    for new_idx, (old_idx, opt) in enumerate(indexed, start=1):
        new_options.append(opt)
        if old_idx in correct_answers:
            new_correct.append(new_idx)

    return new_options, new_correct


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def generate_from_input(request):
    """Generate new questions from input questions using OpenAI. Prompt is dynamic (prompt2 from config)."""
    try:
        from settings_app.models import AdminSettings
        import openai
        import json
        import uuid
        import random

        settings_obj = AdminSettings.objects.first() or AdminSettings()
        api_key = get_openai_key(settings_obj)
        if not api_key:
            return JsonResponse({"success": False, "error": "OPENAI_API_KEY not set."}, status=400)

        prompts = getattr(settings_obj, 'prompts', {}) or {}
        prompt2 = prompts.get('prompt2', {})
        generate_prompt = (prompt2.get('prompt', '') if prompt2 else '').strip()
        if not generate_prompt:
            return JsonResponse({"success": False, "error": "Please set Prompt 2 in Configuration."}, status=400)

        session_id = (request.data.get("session_id") or "").strip() if request.data else ""
        print("session_id : ",session_id)
        input_list, session_id = _get_input_questions_for_session(session_id if session_id else None)
        if not input_list:
            return JsonResponse({"success": False, "error": "No input questions found. Parse a document first."}, status=400)
        input_questions_count = len(input_list)        

        model = getattr(settings_obj, 'model_selector', 'gpt-4') or 'gpt-4'
        temperature = float(getattr(settings_obj, 'temperature', 0.3))

        user_content = (
            generate_prompt
            + "\n\nInput questions to transform:\n"
            + json.dumps(input_list, indent=2)
        )

        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_content}],
            temperature=temperature,
        )

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return JsonResponse({"success": False, "error": "Empty response from OpenAI."}, status=500)

        generated_list = parse_generated_response(text)
        if not generated_list:
            return JsonResponse({"success": False, "error": "Could not parse generated questions from OpenAI."}, status=500)

        if len(generated_list) < input_questions_count:
            return JsonResponse({
                "success": False,
                "error": f"Document has {input_questions_count} question(s) but OpenAI returned only {len(generated_list)}.",
                "input_count": input_questions_count,
                "generated_count": len(generated_list),
            }, status=500)

        # run_batch_id = (batch_id or "").strip() or str(uuid.uuid4())
        saved = 0

        def _to_option_dict(o):
            if o is None:
                return {"text": "", "explanation": ""}
            if isinstance(o, dict):
                return {
                    "text": str(o.get("text", "")).strip(),
                    "explanation": str(o.get("explanation", "")).strip(),
                }
            return {"text": str(o).strip(), "explanation": ""}

        for idx, g in enumerate(generated_list):
            if not isinstance(g, dict):
                continue

            raw_opts = g.get("options", [])
            if not isinstance(raw_opts, list) or len(raw_opts) < 2:
                print(f"Skipping invalid options at index {idx}")
                continue

            opts = [_to_option_dict(o) for o in raw_opts]
            options_len = len(opts)

            question_text = (g.get("question_text") or g.get("question") or "").strip()
            if not question_text:
                print(f"Skipping empty question_text at index {idx}")
                continue

            correct_raw = g.get("correct_answers", [])
            if not isinstance(correct_raw, list):
                print(f"Invalid correct_answers format at index {idx}")
                continue

            # --- Validate correct_answers ---
            correct = []
            for x in correct_raw:
                if isinstance(x, int) and 1 <= x <= options_len:
                    correct.append(x)
                elif isinstance(x, str) and x.strip().isdigit():
                    xi = int(x.strip())
                    if 1 <= xi <= options_len:
                        correct.append(xi)

            if not correct:
                print(f"Skipping question {idx}: no valid correct_answers → {correct_raw}")
                continue

            # --- Shuffle safely ---
            opts, correct = shuffle_options_and_correct(opts, correct)

            question_type = g.get("question_type")
            if question_type not in ("single", "multiple"):
                question_type = "multiple" if len(correct) > 1 else "single"

            # ✅ GUARANTEED overall explanation
            overall_explanation = (
                g.get("overall_explanation")
                or g.get("explanation")
                or ""
            ).strip()

            if not overall_explanation:
                # fallback: build from correct option explanations
                overall_explanation = " ".join(
                    opts[i - 1]["explanation"]
                    for i in correct
                    if 1 <= i <= len(opts)
                )

            GeneratedQuestion(
                question_text=question_text,
                question_type=question_type,
                options=opts,
                correct_answers=[str(c) for c in correct],
                explanation=overall_explanation,
                session_id = session_id,
                # batch_id=run_batch_id,
            ).save()

            saved += 1

        return JsonResponse({
            "success": True,
            "message": f"Generated and saved {saved} question(s) from {input_questions_count} input question(s).",
            "input_count": input_questions_count,
            "generated_count": len(generated_list),
            "saved_count": saved,
            "session_id": session_id,
            "count": saved,
            # "batch_id": run_batch_id,
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)




# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# def get_generated_questions(request):
#     """Return generated questions for the given batch_id only (current document). No batch_id or empty = return [] so count is not from previous uploads."""
#     try:
#         batch_id = (request.GET.get("batch_id") or "").strip()
#         if not batch_id:
#             return Response({"success": True, "questions": [], "count": 0})
#         qs = GeneratedQuestion.objects(batch_id=batch_id).order_by("created_at")
#         def _normalize_option(o):
#             """Ensure each option is a dict with 'text' and 'explanation'. Handles dict, SON, and list-of-strings from DB."""
#             if o is None:
#                 return {"text": "", "explanation": ""}
#             # MongoEngine may return SON or dict-like; support any mapping
#             if hasattr(o, "get") and callable(getattr(o, "get")):
#                 text = (o.get("text") or o.get("value") or o.get("option") or o.get("label") or "")
#                 expl = (o.get("explanation") or o.get("reason") or o.get("desc") or "")
#                 return {"text": str(text).strip() if text else "", "explanation": str(expl).strip() if expl else ""}
#             # e.g. option stored as plain string
#             return {"text": str(o).strip(), "explanation": ""}

#         out = []
#         for q in qs:
#             correct = getattr(q, "correct_answers", []) or []
#             raw_options = getattr(q, "options", []) or []
#             options = [_normalize_option(o) for o in raw_options]
#             # Pad to at least 4 options so all columns have a value (no empty cells from missing keys)
#             while len(options) < 4:
#                 options.append({"text": "", "explanation": ""})
#             def get_opt(idx, field):
#                 try:
#                     val = options[idx].get(field, "")
#                     return "" if val is None else str(val).strip()
#                 except (IndexError, KeyError, TypeError):
#                     return ""
#             # Option numbers (1, 2, 3...) for UI. correct_answers may be stored as ints or numeric strings.
#             nums_str = _correct_answers_to_option_numbers(options, correct)
#             if nums_str:
#                 correct_answer_numbers = [n.strip() for n in nums_str.split(",") if n.strip()]
#             else:
#                 correct_answer_numbers = [str(x).strip() for x in correct if x is not None and str(x).strip()]
#             question_text_val = (getattr(q, "question_text", None) or "").strip()
#             explanation_val = (getattr(q, "explanation", None) or "").strip()
#             out.append({
#                 "id": str(q.id),
#                 "question_text": question_text_val if question_text_val else "",
#                 "question_type": (getattr(q, "question_type", None) or _question_type_from_correct_answers(correct)) or "single-correct",
#                 # Flattened options for UI – always 4 columns with string values
#                 "option1": get_opt(0, "text"),
#                 "option1_explanation": get_opt(0, "explanation"),
#                 "option2": get_opt(1, "text"),
#                 "option2_explanation": get_opt(1, "explanation"),
#                 "option3": get_opt(2, "text"),
#                 "option3_explanation": get_opt(2, "explanation"),
#                 "option4": get_opt(3, "text"),
#                 "option4_explanation": get_opt(3, "explanation"),
#                 "options": options,
#                 "correct_answers": _correct_answers_to_option_numbers(options, correct).split(", ") if _correct_answers_to_option_numbers(options, correct) else [],
#                 "correct_answer_numbers": correct_answer_numbers if correct_answer_numbers else [],
#                 "explanation": explanation_val if explanation_val else "",
#             })
#         return Response({"success": True, "questions": out, "count": len(out)})
#     except Exception as e:
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authenticate
@restrict(['admin'])
def get_generated_questions(request):
    """Return generated questions for the given batch_id only (current document). No batch_id or empty = return [] so count is not from previous uploads."""
    try:
        session_id = (request.GET.get("session_id")).strip()
        print("session_id : ",session_id)
        if not session_id:
            return Response({"success": True, "questions": [], "count": 0})

        qs = GeneratedQuestion.objects(session_id=session_id).order_by("created_at")
        print("qs : ",qs)
        def _normalize_option(o):
            if o is None:
                return {"text": "", "explanation": ""}
            if hasattr(o, "get") and callable(getattr(o, "get")):
                text = (o.get("text") or o.get("value") or o.get("option") or o.get("label") or "")
                expl = (o.get("explanation") or o.get("reason") or o.get("desc") or "")
                return {"text": str(text).strip() if text else "", "explanation": str(expl).strip() if expl else ""}
            return {"text": str(o).strip(), "explanation": ""}

        out = []
        for q in qs:
            correct = getattr(q, "correct_answers", []) or []
            raw_options = getattr(q, "options", []) or []
            options = [_normalize_option(o) for o in raw_options]

            while len(options) < 4:
                options.append({"text": "", "explanation": ""})

            def get_opt(idx, field):
                try:
                    val = options[idx].get(field, "")
                    return "" if val is None else str(val).strip()
                except (IndexError, KeyError, TypeError):
                    return ""

            # ✅ Convert correct answers → option numbers ONCE
            nums_str = _correct_answers_to_option_numbers(options, correct)
            correct_numbers = nums_str.split(", ") if nums_str else []

            question_text_val = (getattr(q, "question_text", None) or "").strip()
            explanation_val = (getattr(q, "explanation", None) or "").strip()

            out.append({
                "id": str(q.id),
                "question_text": question_text_val if question_text_val else "",
                "question_type": (getattr(q, "question_type", None) or _question_type_from_correct_answers(correct)) or "single-correct",
                "option1": get_opt(0, "text"),
                "option1_explanation": get_opt(0, "explanation"),
                "option2": get_opt(1, "text"),
                "option2_explanation": get_opt(1, "explanation"),
                "option3": get_opt(2, "text"),
                "option3_explanation": get_opt(2, "explanation"),
                "option4": get_opt(3, "text"),
                "option4_explanation": get_opt(3, "explanation"),
                "options": options,
                "correct_answers": correct_numbers,          # ✅ UI column now correct
                "correct_answer_numbers": correct_numbers,  # ✅ keep backward compatibility
                "explanation": explanation_val if explanation_val else "",
            })

        return Response({"success": True, "questions": out, "count": len(out), "session_id": session_id})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT', 'PATCH'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def update_generated_question(request, question_id):
    """Update a generated question: question_text, options [{text, explanation}], correct_answers, explanation."""
    try:
        q = _get_generated_by_id(question_id)
        if not q:
            return JsonResponse({"success": False, "error": "Question not found."}, status=404)
        data = request.data
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
        if "correct_answers" in data and isinstance(data["correct_answers"], list):
            q.correct_answers = [str(a) for a in data["correct_answers"]]
        elif "correct_answers" in data and data["correct_answers"] is not None:
            q.correct_answers = [str(data["correct_answers"])]
        q.question_type = _question_type_from_correct_answers(q.correct_answers)
        if "explanation" in data and data["explanation"] is not None:
            q.explanation = str(data["explanation"] or "")
        q.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def delete_generated_question(request, question_id):
    """Delete a generated question."""
    try:
        q = _get_generated_by_id(question_id)
        if not q:
            return JsonResponse({"success": False, "error": "Question not found."}, status=404)
        q.delete()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def bulk_delete_generated_questions(request):
    """Delete multiple generated questions by ids."""
    try:
        data = request.data or {}
        ids = data.get("ids") or []
        if not isinstance(ids, list):
            return JsonResponse({"success": False, "error": "ids must be a list."}, status=400)
        deleted = 0
        for qid in ids:
            q = _get_generated_by_id(qid)
            if q:
                q.delete()
                deleted += 1
        return JsonResponse({"success": True, "deleted_count": deleted})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def regenerate_questions(request):
    """Regenerate selected generated questions into entirely new questions using Prompt2."""
    try:
        from settings_app.models import AdminSettings
        import openai, json

        data = request.data or {}
        ids = data.get("ids") or []
        if not isinstance(ids, list):
            ids = [ids] if ids else []

        qs = [_get_generated_by_id(qid) for qid in ids if _get_generated_by_id(qid)]
        if not qs:
            return JsonResponse({"success": True, "message": "No questions to regenerate.", "regenerated_count": 0})

        settings_obj = AdminSettings.objects.first() or AdminSettings()
        api_key = get_openai_key(settings_obj)
        if not api_key:
            return JsonResponse({"success": False, "error": "OPENAI_API_KEY not set."}, status=400)

        prompts = getattr(settings_obj, "prompts", {}) or {}
        prompt2 = prompts.get("prompt2", {})
        generate_prompt = (prompt2.get("prompt", "") if prompt2 else "").strip()
        if not generate_prompt:
            return JsonResponse({"success": False, "error": "Prompt2 is empty in Admin Settings."}, status=400)

        model = getattr(settings_obj, "model_selector", "gpt-4") or "gpt-4"
        temperature = float(getattr(settings_obj, "temperature", 0.3))

        # 🔥 We only pass the ORIGINAL QUESTION TEXT as seed
        input_list = [
            {"question_text": q.question_text}
            for q in qs
        ]

        user_content = (
            generate_prompt
            + "\n\nGenerate NEW questions based on these seeds:\n"
            + json.dumps(input_list, indent=2)
        )

        client = openai.OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_content}],
            temperature=temperature,
        )

        text = (resp.choices[0].message.content or "").strip()
        if not text:
            return JsonResponse({"success": False, "error": "Empty response from OpenAI."}, status=500)

        generated_list = parse_generated_response(text)
        if len(generated_list) != len(qs):
            return JsonResponse({
                "success": False,
                "error": f"Expected {len(qs)} questions but OpenAI returned {len(generated_list)}.",
                "raw_response_preview": text[:1000],
            }, status=400)

        # ✅ Overwrite existing records
        for i, q in enumerate(qs):
            g = generated_list[i]

            q.question_text = (g.get("question_text") or "").strip()
            q.options = g.get("options") or []
            q.correct_answers = [str(x) for x in (g.get("correct_answers") or [])]
            q.explanation = (g.get("explanation") or "").strip()
            q.question_type = _question_type_from_correct_answers(q.correct_answers)
            q.save()

        return JsonResponse({
            "success": True,
            "message": f"Regenerated {len(qs)} question(s).",
            "regenerated_count": len(qs),
        })

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


def _parse_validation_response(text, id_list):
    """Parse Gemini validation response into list of { id, valid, feedback }."""
    if not text or not id_list:
        return []
    raw = (text or "").strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    start = raw.find("[")
    if start == -1:
        start = raw.find("{")
        if start != -1:
            raw = "[" + raw[start:] + "]"
            start = 0
    if start == -1:
        return []
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] in "[{":
            depth += 1
        elif raw[i] in "]}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return []
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []
    id_set = set(str(x) for x in id_list)
    out = []
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        qid = item.get("id") or (id_list[i] if i < len(id_list) else None)
        if qid is not None:
            qid = str(qid)
        if qid and qid in id_set:
            out.append({
                "id": qid,
                "valid": bool(item.get("valid", item.get("is_valid", True))),
                "feedback": str(item.get("feedback", item.get("message", "")) or ""),
            })
    return out


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def validate_with_gemini(request):
    """Validate generated questions with Gemini AI. Body: { ids?: string[] }. If ids omitted, use latest batch."""
    try:
        from settings_app.models import AdminSettings
        from parsing_suite.helpers import get_gemini_key, get_valid_gemini_model

        settings_obj = AdminSettings.objects.first() or AdminSettings()
        key = get_gemini_key(settings_obj)
        if not key:
            return JsonResponse({
                "success": False,
                "error": "GEMINI_API_KEY not set. Set it in Admin Settings or .env.",
            }, status=400)
        data = request.data or {}
        ids = data.get("ids")
        if ids is not None and not isinstance(ids, list):
            ids = [ids]
        if ids:
            qs = []
            for qid in ids:
                q = _get_generated_by_id(qid)
                if q:
                    qs.append(q)
            qs.sort(key=lambda x: x.created_at)
        else:
            latest = GeneratedQuestion.objects.order_by("-created_at").first()
            if not latest:
                return JsonResponse({
                    "success": True,
                    "results": [],
                    "message": "No generated questions to validate.",
                })
            batch_id = getattr(latest, "batch_id", None) or ""
            qs = list(GeneratedQuestion.objects(batch_id=batch_id).order_by("created_at"))

        if not qs:
            return JsonResponse({"success": True, "results": [], "message": "No questions to validate."})
        id_list = [str(q.id) for q in qs]
        payload = []
        for q in qs:
            opts = getattr(q, "options", []) or []
            payload.append({
                "id": str(q.id),
                "question_text": q.question_text,
                "options": opts,
                "correct_answers": getattr(q, "correct_answers", []) or [],
                "explanation": getattr(q, "explanation", "") or "",
            })
        # 🔹 Load prompts dynamically
        prompts = getattr(settings_obj, "prompts", {}) or {}
        validate_prompt_cfg = prompts.get("prompt_validate_gemini")

        if not validate_prompt_cfg or not isinstance(validate_prompt_cfg, dict):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Gemini validation prompt not configured in Admin Settings."
                },
                status=400
            )
        validate_prompt = (validate_prompt_cfg.get("prompt") or "").strip()

        if not validate_prompt:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Gemini validation prompt is empty. Please configure it in Admin Settings."
                },
                status=400
            )
        # 🔹 Final prompt sent to Gemini
        prompt = (
            validate_prompt
            + "\n\nQuestions to validate:\n"
            + json.dumps(payload, indent=2)
        )


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
        response = model.generate_content(prompt, generation_config={"temperature": temp})
        text = (response.text or "").strip() if hasattr(response, "text") else ""
        if not text and hasattr(response, "candidates") and response.candidates:
            part = response.candidates[0].content.parts[0] if response.candidates[0].content.parts else None
            text = (part.text if part else "").strip()

        results = _parse_validation_response(text, id_list)

        return JsonResponse({
            "success": True,
            "results": results,
            "count": len(results),
        })
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
