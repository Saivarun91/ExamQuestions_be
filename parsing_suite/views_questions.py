"""Input Questions view: list, update, delete parsed questions."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from common.middleware import authenticate, restrict
from bson import ObjectId

from .models import ParsedInputQuestion


@api_view(['GET'])
@authenticate
@restrict(['admin'])
def get_input_questions(request):
    """Return parsed input questions for the current document (latest batch) only."""
    try:
        latest = ParsedInputQuestion.objects.order_by("-created_at").first()
        if not latest:
            return Response({
                "success": True,
                "questions": [],
                "count": 0,
                "batch_id": "",
            })
        batch_id = (getattr(latest, "batch_id", None) or "").strip()
        if not batch_id:
            qs = ParsedInputQuestion.objects.all().order_by("-created_at")
        else:
            qs = ParsedInputQuestion.objects(batch_id=batch_id).order_by("created_at")
        out = []
        for q in qs:
            opts = getattr(q, 'options', []) or []
            opts = [o.get("text", str(o)) if isinstance(o, dict) else str(o) for o in opts]
            flag = getattr(q, 'parsing_flag', None) or "VALID"
            if str(flag).upper() not in ("VALID", "INVALID"):
                flag = "VALID"
            out.append({
                "id": str(q.id),
                "question_text": q.question_text,
                "options": opts,
                "parsing_flag": str(flag).upper(),
            })
        return Response({
            "success": True,
            "questions": out,
            "count": len(out),
            "batch_id": batch_id or "",
        })
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_question_by_id(question_id):
    """Get ParsedInputQuestion by id; return None if invalid."""
    try:
        return ParsedInputQuestion.objects(id=ObjectId(question_id)).first()
    except Exception:
        return None


@api_view(['PUT', 'PATCH'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def update_parsed_question(request, question_id):
    """Update a parsed question: question_text, options (list of strings), parsing_flag."""
    try:
        q = _get_question_by_id(question_id)
        if not q:
            return JsonResponse({"success": False, "error": "Question not found."}, status=404)
        data = request.data
        if "question_text" in data and data["question_text"] is not None:
            q.question_text = (data["question_text"] or "").strip() or q.question_text
        if "options" in data and isinstance(data["options"], list):
            q.options = [str(o.get("text", o) if isinstance(o, dict) else o) for o in data["options"]]
        if "parsing_flag" in data and data["parsing_flag"] is not None:
            flag = (data["parsing_flag"] or "").strip().upper()
            q.parsing_flag = flag if flag in ("VALID", "INVALID") else q.parsing_flag
        q.save()
        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def delete_parsed_question(request, question_id):
    """Delete a parsed question."""
    try:
        q = _get_question_by_id(question_id)
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
def bulk_delete_parsed_questions(request):
    """Delete multiple parsed questions by ids."""
    try:
        data = request.data
        ids = data.get("ids") or []
        if not isinstance(ids, list):
            return JsonResponse({"success": False, "error": "ids must be a list."}, status=400)
        deleted = 0
        for qid in ids:
            q = _get_question_by_id(qid)
            if q:
                q.delete()
                deleted += 1
        return JsonResponse({"success": True, "deleted_count": deleted})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
