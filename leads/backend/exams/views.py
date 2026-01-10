from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mongoengine import DoesNotExist
import json

from .models import Exam


# ----------------------------
# CREATE EXAM
# ----------------------------
@csrf_exempt
def create_exam(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST request required"}, status=400)

    data = json.loads(request.body)

    exam = Exam(
        provider=data.get("provider"),
        title=data.get("title"),
        code=data.get("code"),
        badge=data.get("badge", ""),
        practiceExams=data.get("practiceExams", 0),
        questions=data.get("questions", 0)
    )

    exam.save()
    return JsonResponse({"message": "Exam created successfully"}, status=201)


# ----------------------------
# LIST ALL EXAMS
# ----------------------------
def list_exams(request):
    exams = Exam.objects.all()

    data = [
        {
            "id": str(exam.id),
            "provider": exam.provider,
            "title": exam.title,
            "code": exam.code,
            "badge": exam.badge,
            "practiceExams": exam.practiceExams,
            "questions": exam.questions,
            "provider_slug": exam.provider_slug,
            "code_slug": exam.code_slug,
        }
        for exam in exams
    ]

    return JsonResponse(data, safe=False)


# ----------------------------
# GET SINGLE EXAM BY SLUGS
# URL example: /api/exams/aws/saa-c03/
# ----------------------------
def get_exam(request, provider_slug, code_slug):
    try:
        exam = Exam.objects.get(provider_slug=provider_slug, code_slug=code_slug)
    except DoesNotExist:
        return JsonResponse({"error": "Exam not found"}, status=404)

    data = {
        "id": str(exam.id),
        "provider": exam.provider,
        "title": exam.title,
        "code": exam.code,
        "badge": exam.badge,
        "practiceExams": exam.practiceExams,
        "questions": exam.questions,
        "provider_slug": exam.provider_slug,
        "code_slug": exam.code_slug,
    }

    return JsonResponse(data)


# ----------------------------
# UPDATE EXAM
# ----------------------------
@csrf_exempt
def update_exam(request, exam_id):
    if request.method != "PUT":
        return JsonResponse({"error": "PUT request required"}, status=400)

    try:
        exam = Exam.objects.get(id=exam_id)
    except DoesNotExist:
        return JsonResponse({"error": "Exam not found"}, status=404)

    data = json.loads(request.body)

    exam.provider = data.get("provider", exam.provider)
    exam.title = data.get("title", exam.title)
    exam.code = data.get("code", exam.code)
    exam.badge = data.get("badge", exam.badge)
    exam.practiceExams = data.get("practiceExams", exam.practiceExams)
    exam.questions = data.get("questions", exam.questions)

    exam.save()
    return JsonResponse({"message": "Exam updated successfully"})


# ----------------------------
# DELETE EXAM
# ----------------------------
@csrf_exempt
def delete_exam(request, exam_id):
    if request.method != "DELETE":
        return JsonResponse({"error": "DELETE request required"}, status=400)

    try:
        exam = Exam.objects.get(id=exam_id)
    except DoesNotExist:
        return JsonResponse({"error": "Exam not found"}, status=404)

    exam.delete()
    return JsonResponse({"message": "Exam deleted successfully"})
