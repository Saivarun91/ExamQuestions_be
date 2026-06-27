from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from bson import ObjectId
from .models import Question
from courses.models import Course
from courses.counts import sync_course_counts
from .serializers import QuestionSerializer
from common.middleware import authenticate, restrict
import csv
import io
import datetime
import json
import re
import logging

logger = logging.getLogger(__name__)


# # Try to import google.generativeai at module level for better error handling
# try:
#     import google.generativeai as genai
#     GEMINI_AVAILABLE = True
#     print("[views.py] Successfully imported google.generativeai at module level")
# except ImportError as e:
#     GEMINI_AVAILABLE = False
#     genai = None
#     print(
#         f"[views.py] Failed to import google.generativeai at module level: {e}")

# # Try to import openai at module level for better error handling
# try:
#     import openai
#     OPENAI_AVAILABLE = True


#     print("[views.py] Successfully imported openai at module level")
# except ImportError as e:
#     OPENAI_AVAILABLE = False
#     openai = None
#     print(f"[views.py] Failed to import openai at module level: {e}")


# def get_available_gemini_models(genai_client):
#     """
#     Get list of available Gemini models from the API.
#     Returns a list of tuples: (full_name, short_name) for models that support generateContent.
#     """
#     try:
#         models = genai_client.list_models()
#         available_models = []
#         for model in models:
#             # Filter for models that support generateContent
#             if 'generateContent' in model.supported_generation_methods:
#                 full_name = model.name  # e.g., "models/gemini-1.5-flash"
#                 # Extract just the model name (remove 'models/' prefix if present)
#                 if '/' in full_name:
#                     short_name = full_name.split('/')[-1]
#                 else:
#                     short_name = full_name
#                 available_models.append((full_name, short_name))
#         return available_models
#     except Exception as e:
#         print(f"[get_available_gemini_models] Error listing models: {e}")
#         return []


# def get_valid_gemini_model(model_name=None, genai_client=None):
#     """
#     Get a valid Gemini model name by checking available models from the API.
#     Returns a valid Gemini model name that supports generateContent.
#     """
#     available_models = []

#     # Try to get available models from API
#     available_models_list = []  # List of (full_name, short_name) tuples
#     try:
#         if genai_client:
#             available_models_list = get_available_gemini_models(genai_client)
#         elif genai and hasattr(genai, 'list_models'):
#             # If genai is configured, try to list models directly
#             try:
#                 models = genai.list_models()
#                 for model in models:
#                     if 'generateContent' in model.supported_generation_methods:
#                         full_name = model.name
#                         if '/' in full_name:
#                             short_name = full_name.split('/')[-1]
#                         else:
#                             short_name = full_name
#                         available_models_list.append((full_name, short_name))
#             except Exception as e:
#                 print(f"[get_valid_gemini_model] Error listing models: {e}")
#     except Exception as e:
#         print(f"[get_valid_gemini_model] Error getting available models: {e}")

#     if available_models_list:
#         # Extract just short names for easier matching
#         short_names = [short for _, short in available_models_list]
#         print(f"[get_valid_gemini_model] Available models: {short_names}")

#         # Priority list of models to try (in order of preference)
#         preferred_models = [
#             'gemini-2.5-flash',
#             'gemini-2.5-pro',
#             'gemini-1.5-flash-latest',
#             'gemini-1.5-pro-latest',
#             'gemini-1.5-flash-001',
#             'gemini-1.5-pro-001',
#             'gemini-1.5-flash',
#             'gemini-1.5-pro',
#             'gemini-pro',
#         ]

#         # If specific model requested, check if it's available
#         if model_name:
#             # Check exact match in short names
#             for full_name, short_name in available_models_list:
#                 if model_name == short_name or model_name == full_name:
#                     # Return short name (GenerativeModel accepts both, but short is cleaner)
#                     return short_name

#             # Smart matching for "latest" variants
#             # e.g., gemini-1.5-flash-latest should match gemini-flash-latest
#             if '-latest' in model_name:
#                 # Extract the type (flash/pro) from requested model
#                 model_parts = model_name.split('-')
#                 model_type = None
#                 if 'flash' in model_parts:
#                     model_type = 'flash'
#                 elif 'pro' in model_parts:
#                     model_type = 'pro'
                
#                 # Try to find matching latest model with same type
#                 # Check that the type appears as a separate part, not as substring
#                 if model_type:
#                     for full_name, short_name in available_models_list:
#                         if '-latest' in short_name:
#                             short_parts = short_name.split('-')
#                             # Check if the model type is in the parts (exact match in parts)
#                             if model_type in short_parts:
#                                 return short_name

#             # Smart matching for versioned models (e.g., gemini-2.5-flash)
#             # Extract version and type from requested model
#             model_parts = model_name.split('-')
#             if len(model_parts) >= 3:
#                 # Try to find model with same version and type
#                 requested_version = None
#                 requested_type = None
#                 for i, part in enumerate(model_parts):
#                     if part in ['1.5', '2.0', '2.5', '3']:
#                         requested_version = part
#                         if i + 1 < len(model_parts):
#                             requested_type = model_parts[i + 1]
#                         break
                
#                 if requested_version and requested_type:
#                     for full_name, short_name in available_models_list:
#                         available_parts = short_name.split('-')
#                         if requested_version in available_parts and requested_type in available_parts:
#                             return short_name

#             # Fallback: Check if model name (without version/latest) matches
#             # Extract core parts (gemini, flash/pro)
#             model_parts = model_name.split('-')
#             core_parts = [p for p in model_parts if p in ['gemini', 'flash', 'pro']]
#             if len(core_parts) >= 2:
#                 for full_name, short_name in available_models_list:
#                     short_parts = short_name.split('-')
#                     short_core = [p for p in short_parts if p in ['gemini', 'flash', 'pro']]
#                     if len(short_core) >= 2 and core_parts[-2:] == short_core[-2:]:
#                         return short_name

#         # Try preferred models in order
#         for preferred in preferred_models:
#             for full_name, short_name in available_models_list:
#                 if preferred == short_name or preferred in short_name:
#                     return short_name

#         # Use first available model as fallback (return short name)
#         if available_models_list:
#             return available_models_list[0][1]  # Return short name

#     # Fallback: return common model names (will be validated by API call)
#     if model_name:
#         return model_name

#     # Default fallback - try common model names
#     return 'gemini-1.5-flash'


# ✅ Get all questions for a course (Admin)
@api_view(['GET'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def get_questions_by_course(request, course_id):
    """Admin: Get all questions for a specific course"""
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=ObjectId(course_id))
        questions = Question.objects(course=course).order_by('-created_at')

        serializer = QuestionSerializer(questions, many=True)
        return Response({
            "success": True,
            "count": len(questions),
            "data": serializer.data
        })
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Get questions for test (Public - for test player)
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_test_questions(request, course_id, test_id):
    """Public: Get questions for a specific test"""
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=ObjectId(course_id))

        # Get test details from practice_tests references
        from practice_tests.models import PracticeTest
        current_test = None
        print(
            f"[get_test_questions] Looking for test_id: {test_id}, course_id: {course_id}")

        try:
            # Try to find by slug first (SEO-friendly)
            current_test = PracticeTest.objects(
                slug=test_id, course=course).first()
            if current_test:
                print(
                    f"[get_test_questions] Found test by slug: {current_test.title}")
            else:
                # Try to find by slug without ObjectId hash (e.g., "test-name" matches "test-name-694e3de3")
                import re
                # Match slug that starts with test_id and optionally has hash suffix
                slug_pattern = re.compile(
                    f"^{re.escape(test_id)}(-[a-f0-9]{{8}})?$", re.IGNORECASE)
                current_test = PracticeTest.objects(
                    course=course).filter(slug=slug_pattern).first()
                if current_test:
                    print(
                        f"[get_test_questions] Found test by slug pattern (without hash): {current_test.title}")
            if not current_test:
                # Try by ObjectId
                if ObjectId.is_valid(test_id):
                    print(
                        f"[get_test_questions] test_id is valid ObjectId, searching...")
                    try:
                        current_test = PracticeTest.objects.get(
                            id=ObjectId(test_id), course=course)
                        print(
                            f"[get_test_questions] Found test by ObjectId: {current_test.title}")
                    except PracticeTest.DoesNotExist:
                        # Try without course filter in case course reference is wrong
                        try:
                            current_test = PracticeTest.objects.get(
                                id=ObjectId(test_id))
                            print(
                                f"[get_test_questions] Found test by ObjectId (without course filter): {current_test.title}")
                            # Verify it belongs to the course
                            if str(current_test.course.id) != str(course.id):
                                print(
                                    f"[get_test_questions] Warning: Test belongs to different course")
                                current_test = None
                        except PracticeTest.DoesNotExist:
                            print(
                                f"[get_test_questions] Test with ObjectId {test_id} not found")
                            current_test = None
                else:
                    # Try by index (1-based) for backward compatibility
                    try:
                        print(
                            f"[get_test_questions] test_id is not ObjectId or slug, trying as index...")
                        test_index = int(test_id) - 1
                        practice_tests = list(
                            course.practice_tests) if course.practice_tests else []
                        print(
                            f"[get_test_questions] Course has {len(practice_tests)} practice tests in reference list")

                        if test_index >= 0 and test_index < len(practice_tests):
                            current_test = practice_tests[test_index]
                            print(
                                f"[get_test_questions] Found test by index from reference list: {current_test.title}")
                        else:
                            # Fallback: query directly from database
                            all_tests = list(PracticeTest.objects(
                                course=course).order_by('created_at'))
                            print(
                                f"[get_test_questions] Found {len(all_tests)} tests in database for course")
                            if test_index >= 0 and test_index < len(all_tests):
                                current_test = all_tests[test_index]
                                print(
                                    f"[get_test_questions] Found test by index from database: {current_test.title}")
                    except (ValueError, TypeError):
                        print(
                            f"[get_test_questions] test_id is not a valid index, slug, or ObjectId")
                        current_test = None
        except Exception as e:
            print(f"[get_test_questions] Error finding test: {e}")
            import traceback
            traceback.print_exc()
            current_test = None

        if not current_test:
            return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

        # Questions are linked to Course, not PracticeTest
        # Query questions by course
        questions = Question.objects(course=course).order_by('created_at')

        # Check if we should also filter by PracticeTest (if questions have category field)
        # First, try to get questions linked to this PracticeTest via category
        try:
            from exams.models import Question as ExamQuestion
            exam_questions = ExamQuestion.objects(
                category=current_test).order_by('created_at')
            if exam_questions.count() > 0:
                # Use questions from exams app (linked to PracticeTest)
                questions = exam_questions
                print(
                    f"[get_test_questions] Found {exam_questions.count()} questions linked to PracticeTest")
        except Exception as e:
            print(
                f"[get_test_questions] No questions in exams app, using questions app: {e}")
            # Continue with questions from questions app (linked to Course)
            pass

        # Limit questions based on test configuration (if specified)
        test_questions_count = getattr(current_test, 'questions', 0)
        questions_list = list(questions)

        if test_questions_count > 0 and len(questions_list) > test_questions_count:
            # Shuffle and limit if test specifies a limit
            import random
            random.shuffle(questions_list)
            questions_list = questions_list[:test_questions_count]

        print(
            f"[get_test_questions] Returning {len(questions_list)} questions for test {current_test.id}")

        # Check if we have any questions
        if len(questions_list) == 0:
            print(
                f"[get_test_questions] No questions found for course {course.id}")
            return Response({
                "success": False,
                "error": "No questions available for this test. Please add questions to the course first.",
                "test": {
                    'id': str(current_test.id),
                    'title': getattr(current_test, 'title', ''),
                },
                "questions": [],
                "total": 0
            }, status=status.HTTP_200_OK)  # Return 200 but with success: false

        # Don't send correct answers to frontend (for security)
        questions_data = []
        for q in questions_list:
            # Process options to handle both dict and string formats
            processed_options = []
            if q.options:
                if isinstance(q.options, list):
                    for opt in q.options:
                        if isinstance(opt, dict):
                            processed_options.append(dict(opt))
                        elif isinstance(opt, str):
                            processed_options.append({'text': opt})
                        else:
                            processed_options.append({'text': str(opt)})
                elif isinstance(q.options, str):
                    try:
                        options_data = json.loads(q.options)
                        processed_options = options_data if isinstance(
                            options_data, list) else []
                    except:
                        processed_options = [{'text': q.options}]

            # Handle question_image: exams app uses GridFS FileField — never str(FileField)
            question_image = None
            try:
                from exams.models import Question as ExamQuestion
                is_exam_question = isinstance(q, ExamQuestion)
            except Exception:
                is_exam_question = False

            if is_exam_question:
                try:
                    ext = getattr(q, "question_image_external_url", None)
                    if (
                        isinstance(ext, str)
                        and ext.strip().startswith(("http://", "https://"))
                    ):
                        question_image = ext.strip()
                    elif getattr(q, 'question_image', None):
                        fi = q.question_image
                        if fi:
                            question_image = request.build_absolute_uri(
                                f"/api/exams/questions/{q.id}/image/"
                            )
                except Exception:
                    question_image = None
            else:
                qi = getattr(q, 'question_image', None)
                if isinstance(qi, str) and qi.strip():
                    question_image = qi.strip()
                    if question_image.startswith('/') and not question_image.startswith('//'):
                        question_image = request.build_absolute_uri(question_image)
                elif qi:
                    question_image = None

            for opt in processed_options:
                if not isinstance(opt, dict):
                    continue
                iu = opt.get('image_url') or opt.get('image')
                if isinstance(iu, str):
                    t = iu.strip()
                    if 'GridFS' in t or 'gridfs' in t.lower():
                        opt.pop('image_url', None)
                        opt.pop('image', None)
                    elif t.startswith('/') and not t.startswith('//'):
                        opt['image_url'] = request.build_absolute_uri(t)
                        opt.pop('image', None)

            questions_data.append({
                'id': str(q.id),
                '_id': str(q.id),  # For compatibility
                'question_text': getattr(q, 'question_text', '') or '',
                # Default to 'single' for questions app
                'question_type': getattr(q, 'question_type', 'single'),
                'options': processed_options,
                'correct_answers': q.correct_answers,   # 🔥 ADD THIS FOR TEST SCORING
                'question_image': question_image,
                'marks': getattr(q, 'marks', 1),
                'explanation': getattr(q, 'explanation', '') or '',
                'tags': getattr(q, 'tags', []) or [],
            })

        # Serialize test data
        test_data = {
            'id': str(current_test.id),
            'title': getattr(current_test, 'title', ''),
            'slug': getattr(current_test, 'slug', ''),
            'questions': getattr(current_test, 'questions', len(questions_list)),
            'duration': getattr(current_test, 'duration', 0),
            'difficulty_level': getattr(current_test, 'difficulty_level', 'Intermediate'),
            'overview': getattr(current_test, 'overview', ''),
        }

        return Response({
            "success": True,
            "test": test_data,
            "questions": questions_data,
            "total": len(questions_data)
        })
    except Course.DoesNotExist:
        return Response({"error": "Course not found", "success": False}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        import traceback
        print(f"[get_test_questions] Error: {e}")
        print(traceback.format_exc())
        return Response({"error": str(e), "success": False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Create question (Admin)
@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def create_question(request):
    """Admin: Create a new question"""
    try:
        data = request.data

        if not ObjectId.is_valid(data.get('course_id')):
            return Response({"error": "Invalid course ID"}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.get(id=ObjectId(data['course_id']))

        question = Question(
            course=course,
            question_text=data['question_text'],
            question_type=data['question_type'],
            options=data.get('options', []),
            correct_answers=data.get('correct_answers', []),
            explanation=data.get('explanation', ''),
            question_image=data.get('question_image', None),
            marks=data.get('marks', 1),
            tags=data.get('tags', [])
        )
        question.save()

        sync_course_counts(course)

        serializer = QuestionSerializer(question)
        return Response({
            "success": True,
            "message": "Question created successfully",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Update question (Admin)
@api_view(['PUT'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def update_question(request, question_id):
    """Admin: Update a question"""
    try:
        if not ObjectId.is_valid(question_id):
            return Response({"error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST)

        question = Question.objects.get(id=ObjectId(question_id))
        data = request.data

        # Update fields
        if 'question_text' in data:
            question.question_text = data['question_text']
        if 'question_type' in data:
            question.question_type = data['question_type']
        if 'options' in data:
            question.options = data['options']
        if 'correct_answers' in data:
            question.correct_answers = data['correct_answers']
        if 'explanation' in data:
            question.explanation = data['explanation']
        if 'question_image' in data:
            question.question_image = data['question_image']
        if 'marks' in data:
            question.marks = data['marks']
        if 'tags' in data:
            question.tags = data['tags']

        question.updated_at = datetime.datetime.utcnow()
        question.save()

        if question.course:
            sync_course_counts(question.course)

        serializer = QuestionSerializer(question)
        return Response({
            "success": True,
            "message": "Question updated successfully",
            "data": serializer.data
        })
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Delete question (Admin)
@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def delete_question(request, question_id):
    """Admin: Delete a question"""
    try:
        if not ObjectId.is_valid(question_id):
            return Response({"error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST)

        question = Question.objects.get(id=ObjectId(question_id))
        course = question.course
        question.delete()

        if course:
            sync_course_counts(course)

        return Response({
            "success": True,
            "message": "Question deleted successfully"
        })
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Bulk delete questions (Admin)
@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def bulk_delete_questions(request):
    """Admin: Delete multiple questions"""
    try:
        question_ids = request.data.get('question_ids', [])

        if not question_ids:
            return Response({"error": "No question IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

        deleted_count = 0
        courses_to_update = set()

        for qid in question_ids:
            if ObjectId.is_valid(qid):
                try:
                    question = Question.objects.get(id=ObjectId(qid))
                    if question.course:
                        courses_to_update.add(question.course)
                    question.delete()
                    deleted_count += 1
                except Question.DoesNotExist:
                    continue

        for course in courses_to_update:
            sync_course_counts(course)

        return Response({
            "success": True,
            "message": f"{deleted_count} questions deleted successfully",
            "deleted_count": deleted_count
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Upload questions via CSV (Admin)
@csrf_exempt
def upload_questions_csv(request):
    """Admin: Upload questions via CSV file"""
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed", "success": False}, status=405)

    try:
        course_id = request.POST.get('course_id')
        csv_file = request.FILES.get('file') or request.FILES.get('csv_file')

        print("📝 Upload CSV Request")
        print(f"   course_id: {course_id}")
        print(f"   file: {csv_file}")

        if not course_id or not ObjectId.is_valid(course_id):
            return JsonResponse({"error": "Invalid or missing Course ID", "success": False}, status=400)

        if not csv_file:
            return JsonResponse({"error": "CSV file is required", "success": False}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))

        # ----------------------------
        # Read CSV (encoding safe)
        # ----------------------------
        csv_file.seek(0)
        raw = csv_file.read()
        decoded = None

        for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                decoded = raw.decode(enc)
                print(f"✅ CSV decoded with {enc}")
                break
            except Exception:
                continue

        if not decoded:
            return JsonResponse({"error": "CSV encoding not supported", "success": False}, status=400)

        reader = csv.DictReader(io.StringIO(decoded))
        # print("📋 CSV Headers:", reader.fieldnames)

        if not reader.fieldnames:
            return JsonResponse({"error": "CSV must contain headers", "success": False}, status=400)

        print(f"📋 CSV Headers: {[h.strip() for h in reader.fieldnames]}")

        created_count = 0
        errors = []
        row_count = 0

        def get_row_value(row, keys):
            normalized = {k.strip().lower(): v for k, v in row.items() if k}
            for key in keys:
                if key.lower() in normalized:
                    return normalized[key.lower()]
            return None

        for row_num, row in enumerate(reader, start=2):
            row_count += 1
            try:
                if not row or all(not str(v).strip() for v in row.values() if v):
                    continue

                question_text = str(
                    get_row_value(row, ['question', 'question text'])
                ).strip()

                if not question_text:
                    errors.append(f"Row {row_num}: Question text missing")
                    continue
                # ----------------------------
                # Parse options
                # ----------------------------
                options = []
                for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                    opt = get_row_value(
                        row, [f'answer option {letter}', f'option {letter}'])
                # for idx, letter in enumerate(['A', 'B', 'C', 'D', 'E', 'F'], start=1):
                #     opt = get_row_value(
                #         row, [
                #             f'answer option {letter}',
                #             f'option {letter}',
                #             f'option{idx}',          # 👈 supports option1, option2
                #         ]
                #     )
                    exp = get_row_value(row, [f'explanation {letter}'])
                    if opt and str(opt).strip():
                        option_data = {"text": str(opt).strip()}
                        if exp and str(exp).strip():
                            option_data["explanation"] = str(exp).strip()
                        options.append(option_data)

                if not options:
                    errors.append(f"Row {row_num}: No options found")
                    continue

                # ----------------------------
                # Parse correct answers
                # ----------------------------
                correct_raw = get_row_value(
                    row, ['correct answers', 'correct answer']
                )

                if not correct_raw:
                    errors.append(f"Row {row_num}: Correct answers missing")
                    continue

                correct_raw = str(correct_raw).strip()
                correct_answers = [
                    ans.strip().upper()
                    for ans in correct_raw.replace('|', ',').split(',')
                    if ans.strip()
                ]

                option_texts = [o['text'] for o in options]
                option_letters = ['A', 'B', 'C', 'D', 'E'][:len(options)]

                mapped_correct = []
                for ans in correct_answers:
                    if ans in option_letters:
                        mapped_correct.append(
                            option_texts[option_letters.index(ans)])
                    else:
                        for opt in option_texts:
                            if opt.lower() == ans.lower():
                                mapped_correct.append(opt)
                                break

                if not mapped_correct:
                    errors.append(
                        f"Row {row_num}: Correct answers do not match options")
                    continue

                correct_answers = mapped_correct

                # ----------------------------
                # 🧠 AUTO-DETECT QUESTION TYPE
                # ----------------------------
                csv_type = get_row_value(
                    row, ['question type', 'type']
                )
                csv_type = str(csv_type).strip(
                ).lower() if csv_type else 'auto'

                correct_count = len(correct_answers)

                if correct_count == 1:
                    question_type = 'single'
                else:
                    question_type = 'multiple'

                # 🔍 DEBUG STATEMENT
                print(
                    f"🧠 Question Type Debug | "
                    f"Row={row_num} | "
                    f"CSV='{csv_type}' | "
                    f"Correct={correct_count} | "
                    f"Final='{question_type}'"
                )

                # Safety validation
                if question_type == 'single' and correct_count != 1:
                    raise ValueError(
                        "Single choice must have exactly 1 correct answer")

                if question_type == 'multiple' and correct_count < 2:
                    raise ValueError(
                        "Multiple choice must have 2+ correct answers")

                explanation = str(
                    get_row_value(
                        row, ['overall explanation', 'explanation']) or ''
                ).strip()

                tags_raw = get_row_value(row, ['domain', 'tags'])
                tags = [t.strip()
                        for t in tags_raw.split(',')] if tags_raw else []

                # ----------------------------
                # Save Question
                # ----------------------------
                Question(
                    course=course,
                    question_text=question_text,
                    question_type=question_type,
                    options=options,
                    correct_answers=correct_answers,
                    explanation=explanation,
                    tags=tags
                ).save()

                created_count += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")

        sync_course_counts(course)

        return JsonResponse({
            "success": created_count > 0,
            "created_count": created_count,
            "errors": errors,
            "rows_processed": row_count
        })

    except Exception as e:
        return JsonResponse({"error": str(e), "success": False}, status=500)


# ✅ Get single question (Admin)
@api_view(['GET'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def get_question(request, question_id):
    """Admin: Get a single question"""
    try:
        if not ObjectId.is_valid(question_id):
            return Response({"error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST)

        question = Question.objects.get(id=ObjectId(question_id))
        serializer = QuestionSerializer(question)

        return Response({
            "success": True,
            "data": serializer.data
        })
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get configuration (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def get_configuration(request):
#     """Admin: Get parsing configuration and prompts"""
#     try:
#         from settings_app.models import AdminSettings

#         # Get or create AdminSettings
#         settings_obj = AdminSettings.objects.first()
#         if not settings_obj:
#             return JsonResponse({
#                 "success": False,
#                 "error": "Admin Settings not configured. Please save prompts in Admin panel."
#             }, status=400)

#         # Retrieve saved configuration from AdminSettings
#         # Since AdminSettings has strict=False, we can store additional fields
#         saved_prompts = getattr(settings_obj, 'prompts', None)

#         # Ensure prompts is a dictionary
#         if saved_prompts is None:
#             saved_prompts = {}
#         elif not isinstance(saved_prompts, dict):
#             # If it's not a dict, try to convert it
#             try:
#                 if isinstance(saved_prompts, str):
#                     saved_prompts = json.loads(saved_prompts)
#                 else:
#                     saved_prompts = {}
#             except Exception as e:
#                 print(f"[get_configuration] Error parsing saved_prompts: {e}")
#                 saved_prompts = {}

#         print(
#             f"[get_configuration] Saved prompts from database (type: {type(saved_prompts)}): {saved_prompts}")

#         # Default prompts structure with descriptions and versions
#         default_prompts = {
#             "prompt1": {
#                 "prompt": "",
#                 "version": "v2.1.0",
#                 "description": "Extract individual questions from uploaded document",
#                 "lastUpdated": ""
#             },
#             "prompt2": {
#                 "prompt": "",
#                 "version": "v1.8.0",
#                 "description": "Create new questions based on parsed content",
#                 "lastUpdated": ""
#             },
#             "prompt3": {
#                 "prompt": "",
#                 "version": "v1.5.2",
#                 "description": "Verify accuracy of generated questions",
#                 "lastUpdated": ""
#             }
#         }

#         # Return saved prompts exactly as they are, only fill in defaults for missing fields
#         final_prompts = {}
#         for key in ['prompt1', 'prompt2', 'prompt3']:
#             try:
#                 if key in saved_prompts and isinstance(saved_prompts[key], dict):
#                     # Use saved data as-is, only fill missing fields with defaults
#                     final_prompts[key] = saved_prompts[key].copy()

#                     # Only use defaults if the field is missing or empty
#                     if 'prompt' not in final_prompts[key]:
#                         final_prompts[key]['prompt'] = ''
#                     elif final_prompts[key]['prompt'] is None:
#                         final_prompts[key]['prompt'] = ''

#                     if 'version' not in final_prompts[key] or not final_prompts[key]['version']:
#                         final_prompts[key]['version'] = default_prompts[key].get(
#                             'version', '')
#                     elif final_prompts[key]['version'] is None:
#                         final_prompts[key]['version'] = default_prompts[key].get(
#                             'version', '')

#                     if 'description' not in final_prompts[key] or not final_prompts[key]['description']:
#                         final_prompts[key]['description'] = default_prompts[key].get(
#                             'description', '')
#                     elif final_prompts[key]['description'] is None:
#                         final_prompts[key]['description'] = default_prompts[key].get(
#                             'description', '')

#                     if 'lastUpdated' not in final_prompts[key]:
#                         final_prompts[key]['lastUpdated'] = ''
#                     elif final_prompts[key]['lastUpdated'] is None:
#                         final_prompts[key]['lastUpdated'] = ''
#                 else:
#                     # No saved data, use defaults
#                     final_prompts[key] = {
#                         'prompt': '',
#                         'version': default_prompts[key].get('version', ''),
#                         'description': default_prompts[key].get('description', ''),
#                         'lastUpdated': ''
#                     }
#             except Exception as prompt_error:
#                 print(
#                     f"[get_configuration] Error processing {key}: {prompt_error}")
#                 # Use defaults if there's an error
#                 final_prompts[key] = {
#                     'prompt': '',
#                     'version': default_prompts[key].get('version', ''),
#                     'description': default_prompts[key].get('description', ''),
#                     'lastUpdated': ''
#                 }

#         # Get other config values with proper defaults
#         parsing_instructions = getattr(
#             settings_obj, 'parsing_instructions', None)
#         if parsing_instructions is None:
#             parsing_instructions = ''

#         max_retry_count = getattr(settings_obj, 'max_retry_count', None)
#         if max_retry_count is None:
#             max_retry_count = 3
#         else:
#             max_retry_count = int(max_retry_count)

#         temperature = getattr(settings_obj, 'temperature', None)
#         if temperature is None:
#             temperature = 0.0
#         else:
#             temperature = float(temperature)

#         model_selector = getattr(settings_obj, 'model_selector', None)
#         if model_selector is None:
#             model_selector = 'gpt-4'

#         gemini_model_selector = getattr(settings_obj, 'gemini_model_selector', None)
#         if gemini_model_selector is None:
#             gemini_model_selector = 'gemini-1.5-flash-latest'

#         # Get new model parameters
#         top_p = getattr(settings_obj, 'top_p', None)
#         if top_p is None:
#             top_p = 1.0
#         else:
#             top_p = float(top_p)

#         frequency_penalty = getattr(settings_obj, 'frequency_penalty', None)
#         if frequency_penalty is None:
#             frequency_penalty = 0.0
#         else:
#             frequency_penalty = float(frequency_penalty)

#         presence_penalty = getattr(settings_obj, 'presence_penalty', None)
#         if presence_penalty is None:
#             presence_penalty = 0.0
#         else:
#             presence_penalty = float(presence_penalty)

#         max_output_tokens = getattr(settings_obj, 'max_output_tokens', None)
#         if max_output_tokens is None:
#             max_output_tokens = 2000
#         else:
#             max_output_tokens = int(max_output_tokens)

#         # Get API keys (for display/validation, but don't send full keys for security)
#         gemini_api_key = getattr(settings_obj, 'gemini_api_key', '') or ''
#         openai_api_key = getattr(settings_obj, 'openai_api_key', '') or ''

#         # Only send masked keys (show first 4 and last 4 characters for verification)
#         def mask_api_key(key):
#             if not key or len(key) < 8:
#                 return ''
#             return f"{key[:4]}...{key[-4:]}" if len(key) > 8 else '***'

#         config = {
#             "parsing_instructions": parsing_instructions or '',
#             "max_retry_count": max_retry_count,
#             "temperature": temperature,
#             "model_selector": model_selector or 'gpt-4',
#             "gemini_model_selector": gemini_model_selector or 'gemini-1.5-flash-latest',
#             "top_p": top_p,
#             "frequency_penalty": frequency_penalty,
#             "presence_penalty": presence_penalty,
#             "max_output_tokens": max_output_tokens,
#             "prompts": final_prompts,
#             # Masked for security
#             "gemini_api_key": mask_api_key(gemini_api_key),
#             # Masked for security
#             "openai_api_key": mask_api_key(openai_api_key),
#             # Boolean to show if key is set
#             "gemini_api_key_set": bool(gemini_api_key),
#             # Boolean to show if key is set
#             "openai_api_key_set": bool(openai_api_key)
#         }

#         try:
#             print(
#                 f"[get_configuration] Returning config with prompts: {json.dumps(final_prompts, indent=2, default=str)}")
#         except Exception as log_error:
#             print(f"[get_configuration] Error logging prompts: {log_error}")

#         return Response({
#             "success": True,
#             "config": config
#         })
#     except Exception as e:
#         import traceback
#         error_msg = str(e)
#         print(f"[get_configuration] ERROR: {error_msg}")
#         print(traceback.format_exc())
#         return Response({"success": False, "error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Save configuration (Admin)
# @api_view(['POST'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def save_configuration(request):
#     """Admin: Save parsing configuration and prompts"""
#     try:
#         from settings_app.models import AdminSettings
#         import json

#         data = request.data

#         # DEBUG: Log what we're receiving
#         print(f"[save_configuration] ===== DEBUG START =====")
#         print(f"[save_configuration] Request data type: {type(data)}")
#         print(
#             f"[save_configuration] Request data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
#         print(
#             f"[save_configuration] Full request data: {json.dumps(data, indent=2, default=str)}")

#         # Check if prompts are in the request
#         if 'prompts' in data:
#             print(f"[save_configuration] ✅ 'prompts' key found in request data")
#             print(
#                 f"[save_configuration] Prompts data type: {type(data.get('prompts'))}")
#             print(
#                 f"[save_configuration] Prompts data: {json.dumps(data.get('prompts'), indent=2, default=str)}")
#         else:
#             print(f"[save_configuration] ❌ 'prompts' key NOT found in request data")
#             print(
#                 f"[save_configuration] Available keys: {list(data.keys()) if isinstance(data, dict) else 'N/A'}")

#         # Get or create AdminSettings
#         settings_obj = AdminSettings.objects.first()
#         if not settings_obj:
#             settings_obj = AdminSettings()
#             print(f"[save_configuration] Created new AdminSettings object")
#         else:
#             print(f"[save_configuration] Found existing AdminSettings object")

#         # Save configuration fields (AdminSettings has strict=False, so we can add these fields)
#         if 'parsing_instructions' in data:
#             settings_obj.parsing_instructions = data.get(
#                 'parsing_instructions', '') or ''
#         # Save all configuration parameters with proper validation
#         # Always save these values if they're in the request (even if 0)
#         if 'max_retry_count' in data:
#             try:
#                 retry_val = data.get('max_retry_count')
#                 if retry_val is not None:
#                     settings_obj.max_retry_count = int(retry_val)
#             except (ValueError, TypeError):
#                 settings_obj.max_retry_count = 3
        
#         if 'temperature' in data:
#             try:
#                 temp_val = data.get('temperature')
#                 if temp_val is not None:
#                     temp_value = float(temp_val)
#                     settings_obj.temperature = max(0.0, min(2.0, temp_value))  # Clamp between 0 and 2
#             except (ValueError, TypeError):
#                 settings_obj.temperature = 0.0
        
#         if 'model_selector' in data:
#             model_val = data.get('model_selector')
#             if model_val is not None:
#                 settings_obj.model_selector = model_val or 'gpt-4'
        
#         if 'gemini_model_selector' in data:
#             gemini_val = data.get('gemini_model_selector')
#             if gemini_val is not None:
#                 settings_obj.gemini_model_selector = gemini_val or 'gemini-1.5-flash-latest'
        
#         if 'top_p' in data:
#             try:
#                 top_p_val = data.get('top_p')
#                 # Handle None, empty string, and valid values (including 0)
#                 if top_p_val is not None and top_p_val != '':
#                     top_p_value = float(top_p_val)
#                     settings_obj.top_p = max(0.0, min(1.0, top_p_value))  # Clamp between 0 and 1
#                     print(f"[save_configuration] ✅ Saved top_p: {settings_obj.top_p} (received: {top_p_val}, type: {type(top_p_val)})")
#                 else:
#                     print(f"[save_configuration] ⚠️ top_p is None or empty, skipping save")
#             except (ValueError, TypeError) as e:
#                 print(f"[save_configuration] ❌ Error saving top_p: {e}")
#                 # Don't set default on error, keep existing value
        
#         if 'frequency_penalty' in data:
#             try:
#                 freq_val = data.get('frequency_penalty')
#                 # Handle None, empty string, and valid values (including 0)
#                 if freq_val is not None and freq_val != '':
#                     freq_value = float(freq_val)
#                     settings_obj.frequency_penalty = max(-2.0, min(2.0, freq_value))  # Clamp between -2 and 2
#                     print(f"[save_configuration] ✅ Saved frequency_penalty: {settings_obj.frequency_penalty} (received: {freq_val}, type: {type(freq_val)})")
#                 else:
#                     print(f"[save_configuration] ⚠️ frequency_penalty is None or empty, skipping save")
#             except (ValueError, TypeError) as e:
#                 print(f"[save_configuration] ❌ Error saving frequency_penalty: {e}")
#                 # Don't set default on error, keep existing value
        
#         if 'presence_penalty' in data:
#             try:
#                 pres_val = data.get('presence_penalty')
#                 # Handle None, empty string, and valid values (including 0)
#                 if pres_val is not None and pres_val != '':
#                     pres_value = float(pres_val)
#                     settings_obj.presence_penalty = max(-2.0, min(2.0, pres_value))  # Clamp between -2 and 2
#                     print(f"[save_configuration] ✅ Saved presence_penalty: {settings_obj.presence_penalty} (received: {pres_val}, type: {type(pres_val)})")
#                 else:
#                     print(f"[save_configuration] ⚠️ presence_penalty is None or empty, skipping save")
#             except (ValueError, TypeError) as e:
#                 print(f"[save_configuration] ❌ Error saving presence_penalty: {e}")
#                 # Don't set default on error, keep existing value
        
#         if 'max_output_tokens' in data:
#             try:
#                 tokens_val = data.get('max_output_tokens')
#                 # Handle None, empty string, and valid values (including 0, but clamp to at least 1)
#                 if tokens_val is not None and tokens_val != '':
#                     tokens_value = int(tokens_val)
#                     settings_obj.max_output_tokens = max(1, tokens_value)  # Ensure at least 1
#                     print(f"[save_configuration] ✅ Saved max_output_tokens: {settings_obj.max_output_tokens} (received: {tokens_val}, type: {type(tokens_val)})")
#                 else:
#                     print(f"[save_configuration] ⚠️ max_output_tokens is None or empty, skipping save")
#             except (ValueError, TypeError) as e:
#                 print(f"[save_configuration] ❌ Error saving max_output_tokens: {e}")
#                 # Don't set default on error, keep existing value
#         if 'gemini_api_key' in data:
#             settings_obj.gemini_api_key = data.get('gemini_api_key', '') or ''
#         if 'openai_api_key' in data:
#             settings_obj.openai_api_key = data.get('openai_api_key', '') or ''
#         if 'prompts' in data:
#             # DEBUG: Log prompts processing
#             print(f"[save_configuration] ===== PROCESSING PROMPTS =====")

#             # Ensure prompts is a dictionary
#             prompts_data = data.get('prompts', {})
#             print(
#                 f"[save_configuration] Raw prompts_data type: {type(prompts_data)}")
#             print(f"[save_configuration] Raw prompts_data: {prompts_data}")

#             if isinstance(prompts_data, str):
#                 # If it's a string, try to parse it as JSON
#                 print(
#                     f"[save_configuration] Prompts data is a string, attempting to parse JSON...")
#                 try:
#                     prompts_data = json.loads(prompts_data)
#                     print(
#                         f"[save_configuration] ✅ Successfully parsed prompts string to dict")
#                 except Exception as parse_error:
#                     print(
#                         f"[save_configuration] ❌ Error parsing prompts string: {parse_error}")
#                     prompts_data = {}
#             elif isinstance(prompts_data, dict):
#                 print(f"[save_configuration] ✅ Prompts data is already a dict")
#             else:
#                 print(
#                     f"[save_configuration] ⚠️ Prompts data is unexpected type: {type(prompts_data)}")
#                 prompts_data = {}

#             print(
#                 f"[save_configuration] Processed prompts_data type: {type(prompts_data)}")
#             print(
#                 f"[save_configuration] Processed prompts_data keys: {list(prompts_data.keys()) if isinstance(prompts_data, dict) else 'N/A'}")
#             print(
#                 f"[save_configuration] Processed prompts_data: {json.dumps(prompts_data, indent=2, default=str)}")

#             # Get existing prompts to preserve metadata
#             existing_prompts = getattr(settings_obj, 'prompts', {}) or {}
#             if not isinstance(existing_prompts, dict):
#                 try:
#                     if isinstance(existing_prompts, str):
#                         existing_prompts = json.loads(existing_prompts)
#                     else:
#                         existing_prompts = {}
#                 except:
#                     existing_prompts = {}

#             # Default prompts structure (only for version and description if not provided)
#             default_prompts = {
#                 "prompt1": {"version": "v2.1.0", "description": "Extract individual questions from uploaded document"},
#                 "prompt2": {"version": "v1.8.0", "description": "Create new questions based on parsed content"},
#                 "prompt3": {"version": "v1.5.2", "description": "Verify accuracy of generated questions"}
#             }

#             # Save prompts exactly as received from frontend, preserving only version/description if not provided
#             merged_prompts = {}
#             current_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

#             for key in ['prompt1', 'prompt2', 'prompt3']:
#                 # Start with existing saved data (if any)
#                 if key in existing_prompts and isinstance(existing_prompts[key], dict):
#                     merged_prompts[key] = existing_prompts[key].copy()
#                 else:
#                     merged_prompts[key] = {}

#                 # Now update with new data from request (new data takes priority)
#                 # Save all fields exactly like version is saved - directly and simply
#                 if key in prompts_data and isinstance(prompts_data[key], dict):
#                     print(
#                         f"[save_configuration] Processing {key} from prompts_data...")
#                     print(
#                         f"[save_configuration] {key} data: {json.dumps(prompts_data[key], indent=2, default=str)}")

#                     # Save prompt text exactly as received (same simple logic as version - save directly)
#                     if 'prompt' in prompts_data[key]:
#                         prompt_value = prompts_data[key].get(
#                             'prompt', '') or ''
#                         old_prompt_value = merged_prompts[key].get(
#                             'prompt', '') or ''
#                         print(
#                             f"[save_configuration] {key}: old_prompt='{old_prompt_value[:50] if old_prompt_value else ''}...', new_prompt='{prompt_value[:50] if prompt_value else ''}...'")
#                         merged_prompts[key]['prompt'] = prompt_value
#                         print(
#                             f"[save_configuration] {key}: Set prompt in merged_prompts, value length={len(prompt_value)}")
#                         # Update timestamp if prompt text changed and is not empty
#                         if prompt_value != old_prompt_value:
#                             if prompt_value and str(prompt_value).strip():
#                                 merged_prompts[key]['lastUpdated'] = current_time
#                                 print(
#                                     f"[save_configuration] {key}: Updated lastUpdated to {current_time}")
#                     else:
#                         print(
#                             f"[save_configuration] {key}: 'prompt' key NOT found in prompts_data[{key}]")

#                     # Update version if provided (same simple logic - save directly)
#                     if 'version' in prompts_data[key]:
#                         version_value = prompts_data[key].get('version', '')
#                         if version_value:
#                             merged_prompts[key]['version'] = version_value
#                             print(
#                                 f"[save_configuration] {key}: Set version to {version_value}")

#                     # Update description if provided
#                     if 'description' in prompts_data[key]:
#                         desc_value = prompts_data[key].get('description', '')
#                         if desc_value:
#                             merged_prompts[key]['description'] = desc_value

#                     # Update lastUpdated if explicitly provided
#                     if 'lastUpdated' in prompts_data[key] and prompts_data[key]['lastUpdated']:
#                         merged_prompts[key]['lastUpdated'] = prompts_data[key]['lastUpdated']

#                     print(
#                         f"[save_configuration] {key}: Final merged_prompts[{key}] = {json.dumps(merged_prompts[key], indent=2, default=str)}")
#                 else:
#                     print(
#                         f"[save_configuration] {key}: NOT in prompts_data or not a dict")

#                 # Ensure required fields exist (use defaults only if not set)
#                 if 'version' not in merged_prompts[key] or not merged_prompts[key]['version']:
#                     merged_prompts[key]['version'] = default_prompts[key].get(
#                         'version', '')
#                 if 'description' not in merged_prompts[key] or not merged_prompts[key]['description']:
#                     merged_prompts[key]['description'] = default_prompts[key].get(
#                         'description', '')
#                 if 'prompt' not in merged_prompts[key]:
#                     merged_prompts[key]['prompt'] = ''
#                 if 'lastUpdated' not in merged_prompts[key]:
#                     merged_prompts[key]['lastUpdated'] = ''

#             print(f"[save_configuration] ===== FINAL MERGED PROMPTS =====")
#             print(
#                 f"[save_configuration] Final merged prompts: {json.dumps(merged_prompts, indent=2, default=str)}")
#             print(
#                 f"[save_configuration] Final merged prompts type: {type(merged_prompts)}")
#             print(
#                 f"[save_configuration] Final merged prompts keys: {list(merged_prompts.keys())}")

#             # DEBUG: Check each prompt before saving
#             for key in ['prompt1', 'prompt2', 'prompt3']:
#                 if key in merged_prompts:
#                     prompt_obj = merged_prompts[key]
#                     print(
#                         f"[save_configuration] {key}: prompt='{prompt_obj.get('prompt', '')[:50]}...', version='{prompt_obj.get('version', '')}', lastUpdated='{prompt_obj.get('lastUpdated', '')}'")

#             # Save merged prompts
#             print(f"[save_configuration] Setting prompts on settings_obj...")
#             settings_obj.prompts = merged_prompts
#             print(f"[save_configuration] ✅ Prompts set on settings_obj")

#             # Store merged_prompts for response (before saving)
#             saved_prompts_for_response = merged_prompts.copy()

#         print(f"[save_configuration] ===== SAVING TO DATABASE =====")
#         print(f"[save_configuration] About to save settings_obj...")
#         print(f"[save_configuration] Values before save:")
#         print(f"[save_configuration]   top_p: {getattr(settings_obj, 'top_p', 'NOT SET')}")
#         print(f"[save_configuration]   frequency_penalty: {getattr(settings_obj, 'frequency_penalty', 'NOT SET')}")
#         print(f"[save_configuration]   presence_penalty: {getattr(settings_obj, 'presence_penalty', 'NOT SET')}")
#         print(f"[save_configuration]   max_output_tokens: {getattr(settings_obj, 'max_output_tokens', 'NOT SET')}")
#         print(f"[save_configuration]   temperature: {getattr(settings_obj, 'temperature', 'NOT SET')}")
#         print(f"[save_configuration]   max_retry_count: {getattr(settings_obj, 'max_retry_count', 'NOT SET')}")
#         settings_obj.save()
#         print(f"[save_configuration] ✅ Settings saved to database")

#         # Use the prompts we just saved (merged_prompts) for response instead of re-fetching
#         # This ensures we return exactly what we saved
#         if 'prompts' in data:
#             saved_prompts_response = saved_prompts_for_response
#             print(f"[save_configuration] Using saved merged_prompts for response")
#         else:
#             # Re-fetch from database only if prompts weren't in the request
#             print(
#                 f"[save_configuration] Re-fetching from database (prompts not in request)...")
#             settings_obj = AdminSettings.objects.first()
#             saved_prompts_response = getattr(settings_obj, 'prompts', {}) or {}
#             print(f"[save_configuration] ✅ Re-fetched settings_obj from database")

#         print(f"[save_configuration] ===== VERIFYING PROMPTS FOR RESPONSE =====")
#         print(
#             f"[save_configuration] Saved prompts for response type: {type(saved_prompts_response)}")
#         print(
#             f"[save_configuration] Saved prompts for response: {json.dumps(saved_prompts_response, indent=2, default=str)}")

#         # Verify each prompt
#         for key in ['prompt1', 'prompt2', 'prompt3', 'prompt4']:
#             if key in saved_prompts_response and isinstance(saved_prompts_response[key], dict):
#                 prompt_obj = saved_prompts_response[key]
#                 prompt_text = prompt_obj.get('prompt', '')
#                 print(
#                     f"[save_configuration] ✅ {key}: prompt length={len(prompt_text)}, version='{prompt_obj.get('version', '')}', has_prompt_text={bool(prompt_text)}")
#             else:
#                 print(
#                     f"[save_configuration] ⚠️ {key} NOT found in saved prompts or not a dict")

#         if not isinstance(saved_prompts_response, dict):
#             try:
#                 if isinstance(saved_prompts_response, str):
#                     saved_prompts_response = json.loads(saved_prompts_response)
#                 else:
#                     saved_prompts_response = {}
#             except:
#                 saved_prompts_response = {}

#         # Ensure all prompts are in the response with proper structure
#         response_prompts = {}
#         default_prompts = {
#             "prompt1": {"version": "v2.1.0", "description": "Extract individual questions from uploaded document"},
#             "prompt2": {"version": "v1.8.0", "description": "Create new questions based on parsed content"},
#             "prompt3": {"version": "v1.5.2", "description": "Verify accuracy of generated questions"}
#         }

#         for key in ['prompt1', 'prompt2', 'prompt3']:
#             if key in saved_prompts_response and isinstance(saved_prompts_response[key], dict):
#                 response_prompts[key] = saved_prompts_response[key].copy()
#                 # Ensure all fields exist with proper defaults (but don't overwrite existing values)
#                 if 'prompt' not in response_prompts[key] or response_prompts[key]['prompt'] is None:
#                     response_prompts[key]['prompt'] = ''
#                 if 'version' not in response_prompts[key] or not response_prompts[key]['version']:
#                     response_prompts[key]['version'] = default_prompts[key].get(
#                         'version', '')
#                 if 'description' not in response_prompts[key] or not response_prompts[key]['description']:
#                     response_prompts[key]['description'] = default_prompts[key].get(
#                         'description', '')
#                 if 'lastUpdated' not in response_prompts[key] or response_prompts[key]['lastUpdated'] is None:
#                     response_prompts[key]['lastUpdated'] = ''
#             else:
#                 # Use defaults if not saved
#                 response_prompts[key] = {
#                     'prompt': '',
#                     'version': default_prompts[key].get('version', ''),
#                     'description': default_prompts[key].get('description', ''),
#                     'lastUpdated': ''
#                 }

#         print(f"[save_configuration] ===== RETURNING RESPONSE =====")
#         print(
#             f"[save_configuration] Returning prompts in response: {json.dumps(response_prompts, indent=2, default=str)}")

#         # Re-fetch settings to get all saved values for response
#         settings_obj = AdminSettings.objects.first()
#         print(f"[save_configuration] Re-fetched settings_obj, checking saved values...")
        
#         # Get all saved configuration values (handle 0 values correctly)
#         top_p_val = getattr(settings_obj, 'top_p', None)
#         print(f"[save_configuration] Retrieved top_p from DB: {top_p_val} (type: {type(top_p_val)})")
#         if top_p_val is None:
#             top_p_val = 1.0
#         else:
#             top_p_val = float(top_p_val)
#         print(f"[save_configuration] Final top_p_val for response: {top_p_val}")
        
#         freq_penalty_val = getattr(settings_obj, 'frequency_penalty', None)
#         print(f"[save_configuration] Retrieved frequency_penalty from DB: {freq_penalty_val} (type: {type(freq_penalty_val)})")
#         if freq_penalty_val is None:
#             freq_penalty_val = 0.0
#         else:
#             freq_penalty_val = float(freq_penalty_val)
#         print(f"[save_configuration] Final freq_penalty_val for response: {freq_penalty_val}")
        
#         pres_penalty_val = getattr(settings_obj, 'presence_penalty', None)
#         print(f"[save_configuration] Retrieved presence_penalty from DB: {pres_penalty_val} (type: {type(pres_penalty_val)})")
#         if pres_penalty_val is None:
#             pres_penalty_val = 0.0
#         else:
#             pres_penalty_val = float(pres_penalty_val)
#         print(f"[save_configuration] Final pres_penalty_val for response: {pres_penalty_val}")
        
#         max_tokens_val = getattr(settings_obj, 'max_output_tokens', None)
#         print(f"[save_configuration] Retrieved max_output_tokens from DB: {max_tokens_val} (type: {type(max_tokens_val)})")
#         if max_tokens_val is None:
#             max_tokens_val = 2000
#         else:
#             max_tokens_val = int(max_tokens_val)
#         print(f"[save_configuration] Final max_tokens_val for response: {max_tokens_val}")
        
#         temp_val = getattr(settings_obj, 'temperature', None)
#         if temp_val is None:
#             temp_val = 0.0
#         else:
#             temp_val = float(temp_val)
        
#         max_retry_val = getattr(settings_obj, 'max_retry_count', None)
#         if max_retry_val is None:
#             max_retry_val = 3
#         else:
#             max_retry_val = int(max_retry_val)
        
#         saved_config = {
#             "parsing_instructions": getattr(settings_obj, 'parsing_instructions', '') or '',
#             "max_retry_count": max_retry_val,
#             "temperature": temp_val,
#             "model_selector": getattr(settings_obj, 'model_selector', 'gpt-4') or 'gpt-4',
#             "gemini_model_selector": getattr(settings_obj, 'gemini_model_selector', 'gemini-1.5-flash-latest') or 'gemini-1.5-flash-latest',
#             "top_p": top_p_val,
#             "frequency_penalty": freq_penalty_val,
#             "presence_penalty": pres_penalty_val,
#             "max_output_tokens": max_tokens_val,
#         }
#         print(f"[save_configuration] Final saved_config for response: {json.dumps(saved_config, indent=2, default=str)}")

#         response_data = {
#             "success": True,
#             "message": "Configuration saved successfully",
#             "prompts": response_prompts,  # Return saved prompts so frontend can update immediately
#             "config": saved_config  # Return saved config values so frontend can update immediately
#         }

#         print(
#             f"[save_configuration] Full response data: {json.dumps(response_data, indent=2, default=str)}")
#         print(f"[save_configuration] ===== DEBUG END =====")

#         return Response(response_data)
#     except Exception as e:
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Download CSV (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def download_csv(request):
#     """Admin: Download questions as CSV file"""
#     try:
#         from django.http import HttpResponse

#         # Get query parameters
#         question_type = request.GET.get('type', 'generated')
#         session_id = request.GET.get('session_id', None)

#         print(
#             f"[download_csv] Requested type: {question_type}, session_id: {session_id}")

#         # Validate question type
#         if question_type not in ['input', 'generated', 'manual_review']:
#             return Response({
#                 "success": False,
#                 "error": "Invalid question type. Must be 'input', 'generated', or 'manual_review'"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # Build query - match the logic from get_questions_by_type
#         if question_type == 'input':
#             base_query = CraftsmanQuestion.objects(status='input')
#         elif question_type == 'generated':
#             # Show all generated questions (both validated and not validated)
#             base_query = CraftsmanQuestion.objects(status__in=['generated', 'manual_review'])
#         elif question_type == 'manual_review':
#             # Manual review CSV = all Gemini-generated questions
#             # including manually edited ones, but ONLY for this document
#             base_query = CraftsmanQuestion.objects(
#                 status__in=[
#                     'generated',
#                     'manual_review',
#                     'approved',
#                     'pending',
#                     'rejected'
#                 ]
#             )

#         # Filter by session if provided
#         if session_id:
#             if not ObjectId.is_valid(session_id):
#                 return Response({
#                     "success": False,
#                     "error": "Invalid session_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 parsing_session = ParsingSession.objects.get(
#                     id=ObjectId(session_id))
#                 questions = base_query.filter(
#                     parsing_session=parsing_session).order_by('-created_at')
#             except ParsingSession.DoesNotExist:
#                 questions = base_query.none()
#         else:
#             # If no session_id, return empty for input/generated (new session)
#             if question_type == 'manual_review':
#                 # Manual review is session-specific - need session_id to show questions
#                 questions = base_query.none()
#             else:
#                 questions = base_query.none()

#         # Create CSV
#         response = HttpResponse(content_type='text/csv')
#         response['Content-Disposition'] = f'attachment; filename="questions_{question_type}_{datetime.datetime.utcnow().strftime("%Y%m%d")}.csv"'

#         writer = csv.writer(response)

#         # Write header - different formats for different question types
#         if question_type == 'input':
#             # Input: Only Question and Answer Options (no explanations, no correct answers, no question type, no domain)
#             writer.writerow([
#                 'Question',
#                 'Answer Option A',
#                 'Answer Option B',
#                 'Answer Option C',
#                 'Answer Option D',
#                 'Answer Option E',
#                 'Answer Option F'
#             ])
#         elif question_type == 'manual_review':
#             # Manual Review: Everything including explanations (no Domain column)
#             writer.writerow([
#                 'Question',
#                 'Answer Option A', 'Explanation A',
#                 'Answer Option B', 'Explanation B',
#                 'Answer Option C', 'Explanation C',
#                 'Answer Option D', 'Explanation D',
#                 'Answer Option E', 'Explanation E',
#                 'Answer Option F', 'Explanation F',
#                 'Correct Answers',
#                 'Overall Explanation',
#                 'Question Type'
#             ])
#         else:
#             # Generated: Everything including explanations (no Domain column)
#             writer.writerow([
#                 'Question',
#                 'Answer Option A', 'Explanation A',
#                 'Answer Option B', 'Explanation B',
#                 'Answer Option C', 'Explanation C',
#                 'Answer Option D', 'Explanation D',
#                 'Answer Option E', 'Explanation E',
#                 'Answer Option F', 'Explanation F',
#                 'Correct Answers',
#                 'Overall Explanation',
#                 'Question Type'
#             ])

#         # Write questions
#         for question in questions:
#             # Get options
#             options = question.options or []
#             option_data = []
#             for i in range(6):  # A through F
#                 if i < len(options):
#                     opt = options[i]
#                     if isinstance(opt, dict):
#                         option_data.append({
#                             'text': opt.get('text', ''),
#                             'explanation': opt.get('explanation', '')
#                         })
#                     else:
#                         option_data.append({
#                             'text': str(opt) if opt else '',
#                             'explanation': ''
#                         })
#                 else:
#                     option_data.append({'text': '', 'explanation': ''})

#             # Map correct answers to option numbers (1,2,3,4,5,6)
#             correct_answers_numbers = []
#             option_texts = [opt['text'] for opt in option_data if opt['text']]

#             for correct_answer in (question.correct_answers or []):
#                 correct_text = str(correct_answer).strip().lower()
#                 found = False

#                 # Check if answer is in "option_a", "option_b" format
#                 option_letter_match = re.match(r'^option[_\s]*([a-f])$', correct_text)
#                 if option_letter_match:
#                     letter = option_letter_match.group(1).lower()
#                     letter_idx = ord(letter) - ord('a')  # a=0, b=1, etc.
#                     if letter_idx < len(option_texts):
#                         correct_answers_numbers.append(str(letter_idx + 1))
#                         found = True

#                 # Try to match by option text (case-insensitive)
#                 if not found:
#                     for idx, opt_text in enumerate(option_texts):
#                         if opt_text.strip().lower() == correct_text:
#                             correct_answers_numbers.append(str(idx + 1))
#                             found = True
#                             break

#                 # Try to match by number (if answer is already a number)
#                 if not found:
#                     try:
#                         num = int(correct_text)
#                         if 1 <= num <= len(option_texts):
#                             correct_answers_numbers.append(str(num))
#                             found = True
#                     except ValueError:
#                         pass

#                 # Try to match by letter (a, b, c, d, e, f)
#                 if not found:
#                     option_letters = ['a', 'b', 'c', 'd', 'e', 'f']
#                     if correct_text in option_letters:
#                         letter_idx = option_letters.index(correct_text)
#                         if letter_idx < len(option_texts):
#                             correct_answers_numbers.append(str(letter_idx + 1))
#                             found = True

#             # Format question type: "single-correct" or "multi-correct"
#             question_type_display = question.question_type or 'single'
#             if question_type_display == 'single':
#                 question_type_display = 'single-correct'
#             elif question_type_display == 'multiple':
#                 question_type_display = 'multi-correct'
#             else:
#                 # Fallback: determine from number of correct answers
#                 if len(correct_answers_numbers) == 1:
#                     question_type_display = 'single-correct'
#                 else:
#                     question_type_display = 'multi-correct'

#             # Write row - different formats for different question types
#             if question_type == 'input':
#                 # Input: Only Question and Answer Options (no explanations, no correct answers, no question type, no domain)
#                 writer.writerow([
#                     question.question_text or '',
#                     option_data[0]['text'],
#                     option_data[1]['text'],
#                     option_data[2]['text'],
#                     option_data[3]['text'],
#                     option_data[4]['text'],
#                     option_data[5]['text']
#                 ])
#             elif question_type == 'manual_review':
#                 # Manual Review: All columns except Domain
#                 writer.writerow([
#                     question.question_text or '',
#                     option_data[0]['text'], option_data[0]['explanation'],
#                     option_data[1]['text'], option_data[1]['explanation'],
#                     option_data[2]['text'], option_data[2]['explanation'],
#                     option_data[3]['text'], option_data[3]['explanation'],
#                     option_data[4]['text'], option_data[4]['explanation'],
#                     option_data[5]['text'], option_data[5]['explanation'],
#                     (', '.join(sorted(set(correct_answers_numbers), key=int)) if correct_answers_numbers else ''),
#                     (question.explanation or '').strip(),
#                     question_type_display
#                 ])
#             else:
#                 # Generated: All columns except Domain
#                 writer.writerow([
#                     question.question_text or '',
#                     option_data[0]['text'], option_data[0]['explanation'],
#                     option_data[1]['text'], option_data[1]['explanation'],
#                     option_data[2]['text'], option_data[2]['explanation'],
#                     option_data[3]['text'], option_data[3]['explanation'],
#                     option_data[4]['text'], option_data[4]['explanation'],
#                     option_data[5]['text'], option_data[5]['explanation'],
#                     (', '.join(sorted(set(correct_answers_numbers), key=int)) if correct_answers_numbers else ''),
#                     (question.explanation or '').strip(),
#                     question_type_display
#                 ])

#         print(
#             f"[download_csv] Generated CSV with {questions.count()} questions")
#         return response

#     except Exception as e:
#         print(f"[download_csv] Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get counts (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def get_counts(request):
#     """Admin: Get CraftsmanQuestion counts by type, optionally filtered by session_id"""
#     try:
#         # Get optional session_id from query parameters
#         session_id = request.GET.get('session_id', None)

#         print(
#             f"[get_counts] Getting CraftsmanQuestion counts from craftsman_questions collection...")
#         if session_id:
#             print(f"[get_counts] Filtering by session_id: {session_id}")

#         # If session_id is provided, filter by session; otherwise return 0 for input/generated (new session)
#         if session_id:
#             if not ObjectId.is_valid(session_id):
#                 return Response({
#                     "success": False,
#                     "error": "Invalid session_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 parsing_session = ParsingSession.objects.get(
#                     id=ObjectId(session_id))
#                 # Count questions from this session
#                 input_count = CraftsmanQuestion.objects(
#                     status='input' or 'approved' or 'rejected' or 'pending' or 'validated', parsing_session=parsing_session).count()
#                 # Count all generated questions (both validated and not validated)
#                 generated_count = CraftsmanQuestion.objects(
#                     status__in=['generated', 'manual_review','approved','rejected','pending','validated'], parsing_session=parsing_session).count()
#             except ParsingSession.DoesNotExist:
#                 # Session doesn't exist, return 0
#                 input_count = 0
#                 generated_count = 0
#         else:
#             # No session_id provided - new session, so return 0 for input and generated
#             input_count = 0
#             generated_count = 0
#             print(
#                 f"[get_counts] No session_id provided - returning 0 for input and generated (new session)")

#         # Manual review queue is session-specific - show only questions from current session
#         # Count questions that were validated by Gemini AI (both passed and failed) for this session
#         if session_id and ObjectId.is_valid(session_id):
#             try:
#                 parsing_session = ParsingSession.objects.get(id=ObjectId(session_id))
#                 manual_review_statuses = ['generated', 'manual_review','pending', 'needs_review','clean','approved','rejected','validated']
#                 manual_review_count = CraftsmanQuestion.objects(
#                     status__in=manual_review_statuses,
#                     parsing_session=parsing_session
#                 ).count()
#             except ParsingSession.DoesNotExist:
#                 manual_review_count = 0
#         else:
#             # No session_id - return 0 for manual review (session-specific)
#             manual_review_count = 0

#         print(
#             f"[get_counts] Counted: input={input_count}, generated={generated_count}, manual_review={manual_review_count}")

#         counts = {
#             "input_questions": input_count,
#             "generated_questions": generated_count,
#             "manual_review_queue": manual_review_count
#         }

#         print(f"[get_counts] Returning counts: {counts}")

#         return Response({
#             "success": True,
#             "counts": counts
#         })
#     except Exception as e:
#         print(f"[get_counts] Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get questions by type (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def get_questions_by_type(request, question_type):
#     """Admin: Get CraftsmanQuestions by type (input, generated, manual_review), optionally filtered by session_id"""
#     try:
#         # Get optional session_id from query parameters
#         session_id = request.GET.get('session_id', None)

#         print(
#             f"[get_questions_by_type] Requested question_type: {question_type}")
#         if session_id:
#             print(
#                 f"[get_questions_by_type] Filtering by session_id: {session_id}")

#         # CraftsmanQuestion has status as a proper field, so we can query directly
#         print(f"[get_questions_by_type] Fetching CraftsmanQuestions from craftsman_questions collection...")

#         # Build base query with status filter
#         if question_type == 'input':
#             print(f"[get_questions_by_type] Filtering for status='input'")
#             base_query = CraftsmanQuestion.objects(status='input')
#         elif question_type == 'generated':
#             # All AI-generated questions (both validated and not validated by Gemini AI)
#             # This includes questions with status='generated' (validated/passed) and status='manual_review' (validated/failed)
#             print("[get_questions_by_type] Filtering for status in ['generated', 'manual_review'] (All AI-generated questions)")
#             base_query = CraftsmanQuestion.objects(status__in=['generated', 'manual_review'])

#         elif question_type == 'manual_review':
#             # Questions that Gemini has already validated (both passed and failed)
#             # Manual review queue shows all generated questions (both 'generated' and 'manual_review' status)
#             print("[get_questions_by_type] Filtering for status in ['generated', 'manual_review'] (Gemini validated)")
#             base_query = CraftsmanQuestion.objects(status__in=['generated', 'manual_review','approved','rejected','pending','validated','needs_review','clean'])

#         else:
#             return Response({
#                 "success": False,
#                 "error": "Invalid question type"
#             }, status=status.HTTP_400_BAD_REQUEST)

#         # If session_id is provided, filter by session
#         if session_id:
#             if not ObjectId.is_valid(session_id):
#                 return Response({
#                     "success": False,
#                     "error": "Invalid session_id"
#                 }, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 parsing_session = ParsingSession.objects.get(
#                     id=ObjectId(session_id))
#                 print(f"[get_questions_by_type] Filtering by session: {session_id}, Session name: {parsing_session.session_name}")
#                 # Debug: Check total questions with this status before session filter
#                 total_before_filter = base_query.count()
#                 print(f"[get_questions_by_type] Total questions with this status (before session filter): {total_before_filter}")
                
#                 # Try filtering by ObjectId directly as well for debugging
#                 session_obj_id = ObjectId(session_id)
#                 filtered_by_id = base_query.filter(parsing_session=session_obj_id).count()
#                 print(f"[get_questions_by_type] Questions filtered by ObjectId: {filtered_by_id}")
                
#                 filtered_questions = base_query.filter(
#                     parsing_session=parsing_session).order_by('-updated_at','-created_at')
#                 total_after_filter = filtered_questions.count()
#                 print(f"[get_questions_by_type] Questions after session filter (by object): {total_after_filter}")
                
#                 # If filtering by object doesn't work, try by ObjectId
#                 if total_after_filter == 0 and total_before_filter > 0:
#                     print(f"[get_questions_by_type] WARNING: Filtering by object returned 0, trying by ObjectId directly...")
#                     filtered_questions = base_query.filter(
#                         parsing_session=session_obj_id).order_by('-updated_at','-created_at')
#                     total_after_filter = filtered_questions.count()
#                     print(f"[get_questions_by_type] Questions after session filter (by ObjectId): {total_after_filter}")
#             except ParsingSession.DoesNotExist:
#                 # Session doesn't exist, return empty list
#                 filtered_questions = base_query.none()
#         else:
#             # No session_id provided - return empty list for all types (session-specific)
#             if question_type == 'manual_review':
#                 # Manual review is session-specific - need session_id to show questions
#                 filtered_questions = base_query.none()
#                 print(f"[get_questions_by_type] No session_id provided - returning empty list for manual_review (session-specific)")
#             else:
#                 filtered_questions = base_query.none()
#                 print(
#                     f"[get_questions_by_type] No session_id provided - returning empty list for {question_type} (new session)")

#         total_count = filtered_questions.count()
#         # Log the actual query being used for better debugging
#         if question_type == 'generated' or question_type == 'manual_review':
#             print(f"[get_questions_by_type] Found {total_count} CraftsmanQuestions with status in ['generated', 'manual_review']")
#         else:
#             print(f"[get_questions_by_type] Found {total_count} CraftsmanQuestions with status='{question_type}'")

#         # Convert to list for serialization
#         questions_list = list(filtered_questions)
#         # ✅ Input tab = parsing only, always OK, no status logic
#         if question_type == 'input':
#             for q in questions_list:
#                 q.parsing_flag = 'ok'     # always OK
#                 q.status = None           # remove status from API response



#         # Serialize questions
#         serializer = QuestionSerializer(questions_list, many=True)
#         print(
#             f"[get_questions_by_type] Serialized {len(serializer.data)} questions")
    
#         return Response({
#             "success": True,
#             "questions": serializer.data
#         })
#     except Exception as e:
#         print(f"[get_questions_by_type] Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Parse document (Admin) - Using Gemini API
# @api_view(['POST'])
# @authenticate
# @restrict(['admin'])
# @parser_classes([MultiPartParser, FormParser])
# @csrf_exempt
# def parse_document(request):
#     """Admin: Parse document and extract questions using Gemini API"""
#     try:
#         from settings_app.models import AdminSettings
#         import os
#         import base64
#         from django.core.files.storage import default_storage
#         from django.core.files.base import ContentFile

#         # Get configuration
#         settings_obj = AdminSettings.objects.first()
#         if not settings_obj:
#             settings_obj = AdminSettings()

#         # Get model parameters
#         temperature = getattr(settings_obj, 'temperature', 0)
#         top_p = getattr(settings_obj, 'top_p', 1.0)

#         # Get prompts
#         saved_prompts = getattr(settings_obj, 'prompts', {}) or {}
#         prompt1 = saved_prompts.get('prompt1', {})
#         parsing_prompt = prompt1.get('prompt', '') if prompt1 else ''

#         # Get file
#         file = request.FILES.get('file')
#         if not file:
#             return JsonResponse({"success": False, "error": "No file provided"}, status=400)

#         # Get parameters
#         parsing_instructions = request.POST.get('parsing_instructions', '')
#         test_mode = request.POST.get('test_mode', 'false').lower() == 'true'
#         try:
#             limit = int(request.POST.get('limit', 5)) if test_mode else None
#         except (ValueError, TypeError):
#             limit = 5 if test_mode else None

#         # Check if Gemini is available
#         if not GEMINI_AVAILABLE or not genai:
#             return JsonResponse({"success": False, "error": "Gemini API not available. Please install google-generativeai package."}, status=500)

#         # Initialize Gemini - Check database first, then environment variables
#         # Try to load .env file if not already loaded (settings.py loads it, but ensure it's accessible)
#         try:
#             from dotenv import load_dotenv
#             from pathlib import Path
#             # Use same BASE_DIR calculation as settings.py
#             # settings.py: Path(__file__).resolve().parent.parent where __file__ is backend/backend/settings.py
#             # So BASE_DIR = backend/
#             # From views.py (backend/questions/views.py), parent.parent = backend/
#             BASE_DIR = Path(__file__).resolve().parent.parent
#             env_file = os.path.join(BASE_DIR, '.env')
#             print(f"[parse_document] Looking for .env at: {env_file}")
#             print(f"[parse_document] .env exists: {os.path.exists(env_file)}")
#             if os.path.exists(env_file):
#                 # Use override=True to reload
#                 load_dotenv(env_file, override=True)
#                 print(f"[parse_document] Loaded .env file")
#         except Exception as e:
#             print(f"[parse_document] Warning: Could not load .env file: {e}")

#         # Check for API key: database first, then environment variables, then Django settings
#         gemini_api_key = None

#         # First check database
#         db_key = getattr(settings_obj, 'gemini_api_key', None)
#         print(
#             f"[parse_document] Database key found: {bool(db_key and str(db_key).strip())}")
#         if db_key and str(db_key).strip():
#             gemini_api_key = str(db_key).strip()
#             print(f"[parse_document] Using API key from database")

#         # Then check environment variables (already loaded by settings.py)
#         if not gemini_api_key:
#             env_key = os.environ.get('GEMINI_API_KEY', '')
#             print(
#                 f"[parse_document] Environment variable GEMINI_API_KEY exists: {bool(env_key)}")
#             if env_key:
#                 gemini_api_key = env_key.strip()
#                 print(f"[parse_document] Using API key from environment")

#         # Also try Django settings if available
#         if not gemini_api_key:
#             try:
#                 from django.conf import settings as django_settings
#                 if hasattr(django_settings, 'GEMINI_API_KEY') and django_settings.GEMINI_API_KEY:
#                     gemini_api_key = django_settings.GEMINI_API_KEY.strip()
#                     print(f"[parse_document] Using API key from Django settings")
#             except Exception as e:
#                 print(
#                     f"[parse_document] Could not get key from Django settings: {e}")

#         if not gemini_api_key:
#             return JsonResponse({
#                 "success": False,
#                 "error": "GEMINI_API_KEY not found. Please add it to AdminSettings (gemini_api_key field) or set GEMINI_API_KEY=your_key in .env file in backend directory."
#             }, status=500)

#         genai.configure(api_key=gemini_api_key)

#         # Get the selected Gemini model from settings
#         gemini_model_selector = getattr(settings_obj, 'gemini_model_selector', None)
#         if gemini_model_selector is None:
#             gemini_model_selector = 'gemini-1.5-flash-latest'
        
#         # Get a valid model name by checking available models
#         model_name = get_valid_gemini_model(gemini_model_selector, genai)
#         print(f"[parse_document] Using Gemini model: {model_name} (selected: {gemini_model_selector})")

#         # Read file content
#         file_content = file.read()
#         file_ext = file.name.split('.')[-1].lower()

#         # Prepare prompt - use only dynamic prompt from configuration
#         # Check if prompt is provided - if not, return error (no parse, no questions in tabs)
#         if not parsing_prompt or not parsing_prompt.strip():
#             return JsonResponse({
#                 "success": False,
#                 "error": "Please provide the prompt."
#             }, status=400)
        
#         # Use user's prompt exactly as provided
#         full_prompt = parsing_prompt
#         if parsing_instructions:
#             full_prompt += f"\n\nAdditional instructions: {parsing_instructions}"

#         # Use Gemini to parse document - try multiple model name formats
#         model = None
#         model_error_msg = None

#         # Try different model name formats
#         model_name_variants = [
#             model_name,  # Original name
#             model_name.replace('-latest', ''),  # Without -latest suffix
#             f'models/{model_name}',  # With models/ prefix
#             # With prefix, without -latest
#             f'models/{model_name.replace("-latest", "")}',
#         ]

#         for variant in model_name_variants:
#             try:
#                 print(f"[parse_document] Trying model name: {variant}")
#                 model = genai.GenerativeModel(variant)
#                 # Test if model is valid by checking if it has the method
#                 if hasattr(model, 'generate_content'):
#                     print(
#                         f"[parse_document] Successfully initialized model: {variant}")
#                     model_name = variant
#                     break
#             except Exception as e:
#                 model_error_msg = str(e)
#                 print(f"[parse_document] Model {variant} failed: {e}")
#                 continue

#         # If all variants failed, try to get a valid model from API
#         if model is None:
#             print(
#                 f"[parse_document] All model name variants failed, querying API for available models...")
#             try:
#                 models = genai.list_models()
#                 valid_model_short = None
#                 valid_model_full = None
#                 available_model_names = []

#                 for m in models:
#                     if 'generateContent' in m.supported_generation_methods:
#                         # Try both full name and short name
#                         full_name = m.name
#                         short_name = m.name.split(
#                             '/')[-1] if '/' in m.name else m.name
#                         available_model_names.append((full_name, short_name))

#                         # Prefer flash or pro models
#                         if not valid_model_short:
#                             if 'flash' in short_name.lower() or 'pro' in short_name.lower():
#                                 valid_model_short = short_name
#                                 valid_model_full = full_name

#                 # If no flash/pro found, use first available
#                 if not valid_model_short and available_model_names:
#                     valid_model_full, valid_model_short = available_model_names[0]

#                 if valid_model_short:
#                     print(
#                         f"[parse_document] Using API-discovered model: {valid_model_short}")
#                     # Try short name first (preferred)
#                     try:
#                         model = genai.GenerativeModel(valid_model_short)
#                         model_name = valid_model_short
#                         print(
#                             f"[parse_document] Successfully initialized with short name: {valid_model_short}")
#                     except Exception as short_err:
#                         print(
#                             f"[parse_document] Short name failed: {short_err}, trying full name: {valid_model_full}")
#                         # Try full name as fallback
#                         try:
#                             model = genai.GenerativeModel(valid_model_full)
#                             model_name = valid_model_full
#                             print(
#                                 f"[parse_document] Successfully initialized with full name: {valid_model_full}")
#                         except Exception as full_err:
#                             # Try other available models
#                             for full_name, short_name in available_model_names:
#                                 try:
#                                     model = genai.GenerativeModel(short_name)
#                                     model_name = short_name
#                                     print(
#                                         f"[parse_document] Successfully initialized with: {short_name}")
#                                     break
#                                 except:
#                                     continue

#                 if model is None:
#                     error_details = f"Available models: {[m.name for m in models]}"
#                     raise Exception(
#                         f"No valid Gemini model found. {error_details}. Last error: {model_error_msg}")
#             except Exception as e:
#                 return JsonResponse({
#                     "success": False,
#                     "error": f"Failed to initialize Gemini model: {str(e)}. Please check your API key and model availability."
#                 }, status=500)

#         # Prepare generation config for Gemini
#         generation_config = {
#             'temperature': temperature,
#             'top_p': top_p
#         }

#         try:
#             if file_ext == 'pdf':
#                 # For PDF, send as base64
#                 import base64
#                 file_base64 = base64.b64encode(file_content).decode('utf-8')
#                 file_part = {
#                     "mime_type": "application/pdf",
#                     "data": file_base64
#                 }
#                 try:
#                     response = model.generate_content(
#                         [full_prompt, file_part],
#                         generation_config=generation_config
#                     )
#                     # Verify response is valid
#                     if response is None:
#                         return JsonResponse({
#                             "success": False,
#                             "error": f"Model {model_name} returned None response. Please try again or use a different model."
#                         }, status=500)
#                 except Exception as gen_error:
#                     # If generate_content fails, it might be a model compatibility issue
#                     import traceback
#                     error_msg = str(gen_error)
#                     print(f"[parse_document] Error generating content: {error_msg}")
#                     print(traceback.format_exc())
#                     if 'not found' in error_msg.lower() or 'not supported' in error_msg.lower():
#                         return JsonResponse({
#                             "success": False,
#                             "error": f"Model {model_name} is not available or not supported. Error: {error_msg}. Please check your Gemini API configuration."
#                         }, status=500)
#                     return JsonResponse({
#                         "success": False,
#                         "error": f"Failed to generate content with model {model_name}: {error_msg}"
#                     }, status=500)
#             elif file_ext == 'docx':
#                 # For DOCX, convert to text first
#                 try:
#                     try:
#                         from docx import Document
#                         doc = Document(io.BytesIO(file_content))
#                         text_content = "\n".join(
#                             [para.text for para in doc.paragraphs])
#                         response = model.generate_content(
#                             f"{full_prompt}\n\nDocument content:\n{text_content}",
#                             generation_config=generation_config
#                         )
#                         # Verify response is valid
#                         if response is None:
#                             return JsonResponse({
#                                 "success": False,
#                                 "error": f"Model {model_name} returned None response. Please try again or use a different model."
#                             }, status=500)
#                     except ImportError:
#                         # python-docx not installed, try alternative
#                         text_content = file_content.decode(
#                             'utf-8', errors='ignore')
#                         response = model.generate_content(
#                             f"{full_prompt}\n\nDocument content:\n{text_content}",
#                             generation_config=generation_config
#                         )
#                         # Verify response is valid
#                         if response is None:
#                             return JsonResponse({
#                                 "success": False,
#                                 "error": f"Model {model_name} returned None response. Please try again or use a different model."
#                             }, status=500)
#                 except Exception as e:
#                     import traceback
#                     error_msg = str(e)
#                     print(f"[parse_document] Error processing DOCX: {error_msg}")
#                     print(traceback.format_exc())
#                     return JsonResponse({"success": False, "error": f"Failed to process DOCX file: {error_msg}"}, status=400)
#             else:
#                 return JsonResponse({"success": False, "error": "Unsupported file type. Please upload PDF or DOCX."}, status=400)
#         except Exception as e:
#             import traceback
#             error_msg = str(e)
#             print(f"[parse_document] Error in content generation: {error_msg}")
#             print(traceback.format_exc())
#             if 'not found' in error_msg.lower() or 'not supported' in error_msg.lower():
#                 return JsonResponse({
#                     "success": False,
#                     "error": f"Gemini model error: {error_msg}. The model may not be available for your API key or region."
#                 }, status=500)
#             return JsonResponse({"success": False, "error": f"Failed to generate content from AI: {error_msg}"}, status=500)

#         # Parse response
#         try:
#             if response is None:
#                 return JsonResponse({"success": False, "error": "No response received from Gemini model"}, status=500)
            
#             # Check for finish_reason first to handle blocked/filtered responses
#             finish_reason = None
#             finish_reason_name = None
#             if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                 candidate = response.candidates[0]
#                 if hasattr(candidate, 'finish_reason'):
#                     finish_reason = candidate.finish_reason
#                     # Map finish_reason codes to names
#                     finish_reason_map = {
#                         0: "FINISH_REASON_UNSPECIFIED",
#                         1: "STOP",  # Normal completion
#                         2: "MAX_TOKENS",  # Hit token limit
#                         3: "SAFETY",  # Blocked by safety filters
#                         4: "RECITATION",  # Blocked due to recitation
#                         5: "OTHER"
#                     }
#                     finish_reason_name = finish_reason_map.get(finish_reason, f"UNKNOWN({finish_reason})")
#                     print(f"[parse_document] Finish reason: {finish_reason} ({finish_reason_name})")
                    
#                     # Handle blocked/filtered responses
#                     if finish_reason == 3:  # SAFETY
#                         safety_ratings = []
#                         safety_details = []
#                         if hasattr(candidate, 'safety_ratings'):
#                             safety_ratings = candidate.safety_ratings
#                             # Extract safety rating details
#                             for rating in safety_ratings:
#                                 if hasattr(rating, 'category') and hasattr(rating, 'probability'):
#                                     category = getattr(rating, 'category', 'UNKNOWN')
#                                     probability = getattr(rating, 'probability', 'UNKNOWN')
#                                     # Only include HIGH or MEDIUM probability ratings
#                                     if hasattr(probability, 'name'):
#                                         prob_name = probability.name
#                                         if prob_name in ['HIGH', 'MEDIUM']:
#                                             safety_details.append(f"{category.name if hasattr(category, 'name') else str(category)}: {prob_name}")
                        
#                         error_msg = "Content was blocked by Gemini safety filters."
#                         if safety_details:
#                             error_msg += f" Blocked categories: {', '.join(safety_details)}."
#                         error_msg += " Please review your document content and try again."
                        
#                         return JsonResponse({
#                             "success": False,
#                             "error": error_msg
#                         }, status=400)
#                     elif finish_reason == 4:  # RECITATION
#                         return JsonResponse({
#                             "success": False,
#                             "error": "Content was blocked due to potential recitation of copyrighted material. Please ensure your document contains original content."
#                         }, status=400)
#                     # Note: For MAX_TOKENS (2), we still try to extract partial content
#                     # Don't return error immediately - let the extraction logic handle it
            
#             # Try different ways to get response text
#             # IMPORTANT: Don't use hasattr() on response.text as it triggers the property getter
#             # Instead, check finish_reason first, then try to access text in try-except
#             response_text = None
            
#             # For MAX_TOKENS, check candidates first as text property may fail
#             if finish_reason == 2:
#                 # Try to extract from candidates first for MAX_TOKENS
#                 if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                     try:
#                         candidate = response.candidates[0]
#                         if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
#                             parts = candidate.content.parts
#                             if parts and len(parts) > 0:
#                                 response_text = ''.join([part.text for part in parts if hasattr(part, 'text') and part.text])
#                                 if response_text:
#                                     print(f"[parse_document] Extracted content from candidates for MAX_TOKENS response")
#                     except Exception as candidate_error:
#                         print(f"[parse_document] Error accessing candidates for MAX_TOKENS: {candidate_error}")
                
#                 # If MAX_TOKENS and no content extracted, silently use higher default
#                 # Don't show error - just log and continue (will be handled gracefully below)
#                 if response_text is None:
#                     print(f"[parse_document] MAX_TOKENS detected with no content. This may indicate the response was too large. Continuing with graceful handling...")
#                     # Continue to normal flow - will be handled gracefully
            
#             # If we don't have text yet and it's not MAX_TOKENS, try the text property (but catch the error)
#             if response_text is None:
#                 try:
#                     # Directly access text property - will raise ValueError if no valid Part
#                     response_text = response.text
#                 except (ValueError, AttributeError) as text_error:
#                     error_msg = str(text_error)
#                     print(f"[parse_document] Error accessing response.text: {error_msg}")
                    
#                     # Check if error is about missing Part
#                     if "requires the response to contain a valid" in error_msg or "none were returned" in error_msg:
#                         if finish_reason == 3:
#                             return JsonResponse({
#                                 "success": False,
#                                 "error": "Content was blocked by Gemini safety filters. Please review your document content."
#                             }, status=400)
#                         elif finish_reason == 4:
#                             return JsonResponse({
#                                 "success": False,
#                                 "error": "Content was blocked due to potential recitation. Please ensure your document contains original content."
#                             }, status=400)
#                         elif finish_reason == 2:
#                             # For MAX_TOKENS, don't return error - continue to try candidates
#                             print(f"[parse_document] MAX_TOKENS: response.text failed, trying candidates...")
#                         else:
#                             return JsonResponse({
#                                 "success": False,
#                                 "error": f"Response does not contain valid content. Finish reason: {finish_reason_name or 'Unknown'}. Please try again or use a different model."
#                             }, status=400)
                    
#                     # Try alternative methods (candidates) if text property failed
#                     if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                         try:
#                             candidate = response.candidates[0]
#                             if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
#                                 parts = candidate.content.parts
#                                 if parts and len(parts) > 0:
#                                     response_text = ''.join([part.text for part in parts if hasattr(part, 'text') and part.text])
#                         except Exception as candidate_error:
#                             print(f"[parse_document] Error accessing candidates: {candidate_error}")
#                 except Exception as other_error:
#                     # Catch any other exceptions
#                     error_msg = str(other_error)
#                     print(f"[parse_document] Unexpected error accessing response.text: {error_msg}")
#                     # Try candidates as fallback
#                     if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                         try:
#                             candidate = response.candidates[0]
#                             if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
#                                 parts = candidate.content.parts
#                                 if parts and len(parts) > 0:
#                                     response_text = ''.join([part.text for part in parts if hasattr(part, 'text') and part.text])
#                         except Exception as candidate_error:
#                             print(f"[parse_document] Error accessing candidates: {candidate_error}")
            
#             # If still no text, try candidates directly
#             if response_text is None and hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                 try:
#                     candidate = response.candidates[0]
#                     if hasattr(candidate, 'content'):
#                         if hasattr(candidate.content, 'parts'):
#                             parts = candidate.content.parts
#                             if parts and len(parts) > 0:
#                                 response_text = ''.join([part.text for part in parts if hasattr(part, 'text') and part.text])
#                 except Exception as candidate_error:
#                     print(f"[parse_document] Error accessing candidates: {candidate_error}")
            
#             if response_text is None:
#                 # Check if we have a finish_reason that explains why
#                 if finish_reason == 3:
#                     return JsonResponse({
#                         "success": False,
#                         "error": "Content was blocked by Gemini safety filters. Please review your document content."
#                     }, status=400)
#                 elif finish_reason == 4:
#                     return JsonResponse({
#                         "success": False,
#                         "error": "Content was blocked due to potential recitation. Please ensure your document contains original content."
#                     }, status=400)
#                 elif finish_reason == 2:  # MAX_TOKENS
#                     # For MAX_TOKENS, try one more time to extract from candidates directly
#                     if hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
#                         candidate = response.candidates[0]
#                         if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
#                             parts = candidate.content.parts
#                             if parts and len(parts) > 0:
#                                 try:
#                                     response_text = ''.join([part.text for part in parts if hasattr(part, 'text') and part.text])
#                                     if response_text:
#                                         print(f"[parse_document] Warning: Response was truncated (MAX_TOKENS) but extracted partial content")
#                                         # Continue processing with partial content
#                                 except Exception as e:
#                                     print(f"[parse_document] Error extracting from parts: {e}")
                    
#                     # If still no content after all attempts, continue to empty response handling
#                     # Don't return error for MAX_TOKENS - let it be handled gracefully
#                     if response_text is None:
#                         print(f"[parse_document] MAX_TOKENS: No content could be extracted after all attempts. Continuing...")
#                 elif finish_reason is not None:
#                     return JsonResponse({
#                         "success": False,
#                         "error": f"Could not extract text from Gemini response. Finish reason: {finish_reason_name or 'Unknown'}. Please try again or use a different model."
#                     }, status=500)
                
#                 # Last resort: convert to string
#                 try:
#                     response_text = str(response)
#                 except Exception as str_error:
#                     print(f"[parse_document] Error converting response to string: {str_error}")
#                     return JsonResponse({"success": False, "error": "Could not extract text from Gemini response. Please try again or use a different model."}, status=500)
            
#             if not response_text or len(response_text.strip()) == 0:
#                 if finish_reason == 3:
#                     return JsonResponse({
#                         "success": False,
#                         "error": "Content was blocked by Gemini safety filters. Please review your document content."
#                     }, status=400)
#                 elif finish_reason == 2:
#                     # For MAX_TOKENS, provide a helpful but non-blocking message
#                     print(f"[parse_document] MAX_TOKENS: Empty response. The document may be too large.")
#                     return JsonResponse({
#                         "success": False,
#                         "error": "The document is too large to process. Please try with a smaller document or split it into multiple parts."
#                     }, status=400)
#                 return JsonResponse({"success": False, "error": "Empty response received from Gemini model. Please try again or use a different model."}, status=500)
            
#             # Log warning if response was truncated but we have content
#             if finish_reason == 2:
#                 print(f"[parse_document] Warning: Response was truncated (MAX_TOKENS) but processing available content ({len(response_text)} chars)")
                
#         except Exception as e:
#             import traceback
#             print(f"[parse_document] Error getting response text: {str(e)}")
#             print(traceback.format_exc())
#             return JsonResponse({"success": False, "error": f"Failed to get response text: {str(e)}"}, status=500)

#         # Extract JSON from response
#         try:
#             # Try to find JSON in the response
#             import re
#             print(
#                 f"[parse_document] Response text length: {len(response_text)}")
#             print(
#                 f"[parse_document] Response preview: {response_text[:500]}...")

#             # Clean the response text - remove markdown code block markers
#             cleaned_text = response_text.strip()
            
#             # Remove markdown code block markers if present
#             if cleaned_text.startswith('```json'):
#                 cleaned_text = cleaned_text[7:]  # Remove ```json
#             elif cleaned_text.startswith('```'):
#                 cleaned_text = cleaned_text[3:]  # Remove ```
            
#             if cleaned_text.endswith('```'):
#                 cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
#             cleaned_text = cleaned_text.strip()
            
#             # If MAX_TOKENS and content is very short, it's likely incomplete
#             if finish_reason == 2 and len(cleaned_text) < 100:
#                 return JsonResponse({
#                     "success": False,
#                     "error": "Response was truncated and the content is too incomplete to parse. The document may be too large. Please try with a smaller document or split it into multiple parts."
#                 }, status=400)
            
#             # Try to find JSON array in the cleaned text
#             # First, try to find a complete JSON array by matching brackets
#             json_str = None
            
#             # Try to find the outermost array brackets
#             bracket_start = cleaned_text.find('[')
#             if bracket_start != -1:
#                 # Find matching closing bracket
#                 bracket_count = 0
#                 bracket_end = -1
#                 for i in range(bracket_start, len(cleaned_text)):
#                     if cleaned_text[i] == '[':
#                         bracket_count += 1
#                     elif cleaned_text[i] == ']':
#                         bracket_count -= 1
#                         if bracket_count == 0:
#                             bracket_end = i
#                             break
                
#                 if bracket_end != -1:
#                     json_str = cleaned_text[bracket_start:bracket_end + 1]
#                     print(f"[parse_document] Found JSON array from position {bracket_start} to {bracket_end}, length: {len(json_str)}")
            
#             # Fallback to regex if bracket matching didn't work
#             if not json_str:
#                 json_match = re.search(r'\[.*?\]', cleaned_text, re.DOTALL)
#                 if json_match:
#                     # Try to find the complete array by matching brackets
#                     json_str = json_match.group()
#                     # Check if it's a complete array by counting brackets
#                     if json_str.count('[') == json_str.count(']'):
#                         print(f"[parse_document] Found JSON array via regex, length: {len(json_str)}")
#                     else:
#                         # Try to find the complete array manually
#                         bracket_start = cleaned_text.find('[')
#                         if bracket_start != -1:
#                             bracket_count = 0
#                             bracket_end = -1
#                             for i in range(bracket_start, len(cleaned_text)):
#                                 if cleaned_text[i] == '[':
#                                     bracket_count += 1
#                                 elif cleaned_text[i] == ']':
#                                     bracket_count -= 1
#                                     if bracket_count == 0:
#                                         bracket_end = i
#                                         break
#                             if bracket_end != -1:
#                                 json_str = cleaned_text[bracket_start:bracket_end + 1]
#                                 print(f"[parse_document] Found complete JSON array manually, length: {len(json_str)}")
            
#             if json_str:
#                 print(f"[parse_document] Extracted JSON array, length: {len(json_str)}")
#                 print(f"[parse_document] JSON preview (first 500 chars): {json_str[:500]}")
#                 try:
#                     questions_data = json.loads(json_str)
#                     print(f"[parse_document] Successfully parsed JSON array with {len(questions_data) if isinstance(questions_data, list) else 1} question(s)")
#                 except json.JSONDecodeError as json_err:
#                     # If the JSON is incomplete, try to fix common issues
#                     print(f"[parse_document] JSON parse error, attempting to fix: {json_err}")
                    
#                     # If MAX_TOKENS and JSON is incomplete, try to repair it
#                     if finish_reason == 2:
#                         # Try to fix incomplete JSON by closing strings, objects, and arrays
#                         repaired_json = json_str
#                         in_string = False
#                         escape_next = False
#                         bracket_count = 0
#                         brace_count = 0
                        
#                         # First, find where we are in the JSON structure
#                         for i, char in enumerate(json_str):
#                             if escape_next:
#                                 escape_next = False
#                                 continue
#                             if char == '\\':
#                                 escape_next = True
#                                 continue
#                             if char == '"' and not escape_next:
#                                 in_string = not in_string
#                             if not in_string:
#                                 if char == '[':
#                                     bracket_count += 1
#                                 elif char == ']':
#                                     bracket_count -= 1
#                                 elif char == '{':
#                                     brace_count += 1
#                                 elif char == '}':
#                                     brace_count -= 1
                        
#                         # If we're in a string, close it
#                         if in_string:
#                             # Find the last unclosed quote position
#                             last_quote = json_str.rfind('"')
#                             if last_quote >= 0:
#                                 # Check if there's content after the quote that might be incomplete
#                                 after_quote = json_str[last_quote+1:].strip()
#                                 if after_quote and not after_quote.startswith(','):
#                                     # String is incomplete, close it
#                                     repaired_json = json_str + '"'
#                                 else:
#                                     repaired_json = json_str
#                             else:
#                                 repaired_json = json_str + '"'
#                         else:
#                             repaired_json = json_str
                        
#                         # Close any open objects
#                         while brace_count > 0:
#                             repaired_json += '}'
#                             brace_count -= 1
                        
#                         # Close any open arrays (but keep at least one for the main array)
#                         while bracket_count > 1:
#                             repaired_json += ']'
#                             bracket_count -= 1
                        
#                         # Try to parse the repaired JSON
#                         try:
#                             questions_data = json.loads(repaired_json)
#                             print(f"[parse_document] Successfully repaired incomplete JSON from MAX_TOKENS truncation")
#                         except json.JSONDecodeError:
#                             # If repair failed, check if we can extract any valid partial JSON
#                             # Try to find the last complete object in the array
#                             first_bracket = repaired_json.find('[')
#                             if first_bracket >= 0:
#                                 # Try to find complete objects before the truncation
#                                 potential_json = repaired_json[first_bracket:]
#                                 # Look for the last complete object
#                                 last_complete_obj_end = -1
#                                 brace_count = 0
#                                 in_string = False
#                                 escape_next = False
                                
#                                 for i, char in enumerate(potential_json):
#                                     if escape_next:
#                                         escape_next = False
#                                         continue
#                                     if char == '\\':
#                                         escape_next = True
#                                         continue
#                                     if char == '"' and not escape_next:
#                                         in_string = not in_string
#                                         continue
#                                     if not in_string:
#                                         if char == '{':
#                                             brace_count += 1
#                                         elif char == '}':
#                                             brace_count -= 1
#                                             if brace_count == 0:
#                                                 # Found a complete object, check if it's followed by valid JSON
#                                                 # Look ahead to see if we can close the array
#                                                 remaining = potential_json[i+1:].strip()
#                                                 if remaining.startswith(',') or remaining.startswith(']') or not remaining:
#                                                     last_complete_obj_end = i
                                
#                                 if last_complete_obj_end > 0:
#                                     # Extract up to the last complete object and close the array
#                                     partial_json = potential_json[:last_complete_obj_end+1] + ']'
#                                     try:
#                                         questions_data = json.loads(partial_json)
#                                         print(f"[parse_document] Extracted partial JSON with {len(questions_data)} question(s) from truncated response")
#                                     except json.JSONDecodeError:
#                                         # If MAX_TOKENS and we can't parse, return helpful error
#                                         raise json.JSONDecodeError(
#                                             "Response was truncated and JSON is too incomplete to parse. The document may be too large. Please try with a smaller document or split it into multiple parts.",
#                                             json_str, len(json_str)
#                                         )
#                                 else:
#                                     # If MAX_TOKENS and we can't extract valid JSON, return helpful error
#                                     raise json.JSONDecodeError(
#                                         "Response was truncated and JSON is too incomplete to parse. The document may be too large. Please try with a smaller document or split it into multiple parts.",
#                                         json_str, len(json_str)
#                                     )
#                             else:
#                                 raise json_err
#                     else:
#                         # For non-MAX_TOKENS errors, try the original repair logic
#                         # Try to find complete JSON by looking for balanced brackets
#                         bracket_count = 0
#                         last_valid_pos = -1
#                         in_string = False
#                         escape_next = False
                        
#                         for i, char in enumerate(json_str):
#                             if escape_next:
#                                 escape_next = False
#                                 continue
#                             if char == '\\':
#                                 escape_next = True
#                                 continue
#                             if char == '"' and not escape_next:
#                                 in_string = not in_string
#                                 continue
#                             if not in_string:
#                                 if char == '[':
#                                     bracket_count += 1
#                                 elif char == ']':
#                                     bracket_count -= 1
#                                     if bracket_count == 0:
#                                         last_valid_pos = i
#                                         break
                        
#                         if last_valid_pos > 0:
#                             json_str = json_str[:last_valid_pos + 1]
#                             try:
#                                 questions_data = json.loads(json_str)
#                             except json.JSONDecodeError:
#                                 raise json_err
#                         else:
#                             raise json_err
#             else:
#                 # Try parsing the whole cleaned response as JSON
#                 print(f"[parse_document] Trying to parse entire cleaned response as JSON")
#                 try:
#                     questions_data = json.loads(cleaned_text)
#                     # Ensure it's a list
#                     if not isinstance(questions_data, list):
#                         print(f"[parse_document] WARNING: Response is not an array, converting single object to list")
#                         questions_data = [questions_data]
#                 except json.JSONDecodeError:
#                     # If that fails, try to find multiple JSON objects (not just one)
#                     # Look for all JSON objects in the response by finding balanced braces
#                     print(f"[parse_document] Attempting to extract multiple JSON objects from response...")
#                     questions_data = []
#                     i = 0
#                     objects_found = 0
#                     while i < len(cleaned_text):
#                         # Find the start of a JSON object
#                         obj_start = cleaned_text.find('{', i)
#                         if obj_start == -1:
#                             break
                        
#                         # Find the matching closing brace
#                         brace_count = 0
#                         in_string = False
#                         escape_next = False
#                         obj_end = -1
                        
#                         for j in range(obj_start, len(cleaned_text)):
#                             if escape_next:
#                                 escape_next = False
#                                 continue
#                             if cleaned_text[j] == '\\':
#                                 escape_next = True
#                                 continue
#                             if cleaned_text[j] == '"' and not escape_next:
#                                 in_string = not in_string
#                                 continue
#                             if not in_string:
#                                 if cleaned_text[j] == '{':
#                                     brace_count += 1
#                                 elif cleaned_text[j] == '}':
#                                     brace_count -= 1
#                                     if brace_count == 0:
#                                         obj_end = j
#                                         break
                        
#                         if obj_end != -1:
#                             obj_str = cleaned_text[obj_start:obj_end + 1]
#                             try:
#                                 obj_data = json.loads(obj_str)
#                                 # Verify it looks like a question object
#                                 if isinstance(obj_data, dict) and ('question_text' in obj_data or 'question' in obj_data):
#                                     questions_data.append(obj_data)
#                                     objects_found += 1
#                                     print(f"[parse_document] Extracted question object {objects_found} at position {obj_start}-{obj_end}")
#                                 i = obj_end + 1
#                             except json.JSONDecodeError:
#                                 i = obj_start + 1
#                         else:
#                             i = obj_start + 1
                    
#                     if questions_data:
#                         print(f"[parse_document] Successfully parsed {len(questions_data)} question objects from multiple JSON objects")
#                     else:
#                         # Last resort: try to extract a single JSON object
#                         print(f"[parse_document] No question objects found, trying single object extraction...")
#                         obj_match = re.search(r'\{.*?\}', cleaned_text, re.DOTALL)
#                         if obj_match:
#                             json_str = obj_match.group()
#                             try:
#                                 questions_data = json.loads(json_str)
#                                 # Convert single object to list
#                                 if not isinstance(questions_data, list):
#                                     questions_data = [questions_data]
#                                 print(f"[parse_document] WARNING: Only found single JSON object, converted to list")
#                             except json.JSONDecodeError:
#                                 raise
#                         else:
#                             raise

#             parsed_count = len(questions_data) if isinstance(questions_data, list) else 1
#             print(
#                 f"[parse_document] Successfully parsed {parsed_count} question(s) from AI response")
            
#             # Verify we got all questions - log the count
#             if isinstance(questions_data, list):
#                 print(f"[parse_document] Extracted questions array has {len(questions_data)} items")
#                 # Log first and last question to verify range
#                 if len(questions_data) > 0:
#                     print(f"[parse_document] First question preview: {str(questions_data[0].get('question_text', '')[:100]) if isinstance(questions_data[0], dict) else 'N/A'}")
#                     if len(questions_data) > 1:
#                         print(f"[parse_document] Last question preview: {str(questions_data[-1].get('question_text', '')[:100]) if isinstance(questions_data[-1], dict) else 'N/A'}")
#             else:
#                 print(f"[parse_document] WARNING: questions_data is not a list, it's a {type(questions_data)}")
#         except json.JSONDecodeError as e:
#             print(f"[parse_document] JSON decode error: {str(e)}")
#             print(f"[parse_document] Full response: {response_text}")
            
#             # Check if error is related to MAX_TOKENS truncation
#             if finish_reason == 2:
#                 error_msg = str(e)
#                 return JsonResponse({
#                     "success": False,
#                     "error": f"Response was truncated and could not be parsed as JSON: {str(e)}. The document may be too large. Please try with a smaller document or split it into multiple parts."
#                 }, status=400)
#             else:
#                 return JsonResponse({"success": False, "error": f"Failed to parse AI response as JSON: {str(e)}. Response preview: {response_text[:500]}"}, status=500)
#         except Exception as e:
#             import traceback
#             print(f"[parse_document] Parse error: {str(e)}")
#             print(traceback.format_exc())
#             print(f"[parse_document] Full response: {response_text}")
#             return JsonResponse({"success": False, "error": f"Failed to parse AI response: {str(e)}. Response preview: {response_text[:500]}"}, status=500)

#         if not isinstance(questions_data, list):
#             questions_data = [questions_data]

#         total_questions_to_process = len(questions_data)
#         print(f"[parse_document] ===== FINAL QUESTION COUNT =====")
#         print(f"[parse_document] Total questions extracted from document: {total_questions_to_process}")
#         print(f"[parse_document] Processing {total_questions_to_process} questions for saving")

#         # Limit questions in test mode
#         if test_mode and limit:
#             questions_data = questions_data[:limit]
#             print(
#                 f"[parse_document] Limited to {limit} questions in test mode")

#         # Get a default course (you may want to make this configurable)
#         default_course = Course.objects.first()
#         if not default_course:
#             print(f"[parse_document] ERROR: No course found in database")
#             return JsonResponse({"success": False, "error": "No course found. Please create a course first."}, status=400)
#         print(
#             f"[parse_document] Using course: {default_course.id} - {getattr(default_course, 'name', 'Unnamed')}")

#         # Create a parsing session to track this operation
#         session_name = f"Parse - {file.name if file else 'Document'} - {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
#         parsing_session = ParsingSession(
#             session_name=session_name,
#             session_type='parse',
#             course=default_course,
#             document_name=file.name if file else None,
#             document_type=file_ext if file else None,
#             parsing_instructions=parsing_instructions,
#             model_used=model_name,
#             status='in_progress'
#         )
#         parsing_session.save()
#         print(
#             f"[parse_document] Created parsing session: {parsing_session.id} - {session_name}")

#         # Save questions
#         saved_count = 0
#         errors = []

#         print(f"\n[parse_document] ===== STARTING TO SAVE QUESTIONS =====")
#         print(
#             f"[parse_document] Total questions to process: {len(questions_data)}")
#         print(f"[parse_document] Default course ID: {default_course.id}")
#         print(
#             f"[parse_document] Default course name: {getattr(default_course, 'name', 'Unnamed')}")
#         print(f"[parse_document] Session ID: {parsing_session.id}")
#         print(f"[parse_document] Session name: {parsing_session.session_name}")

#         for idx, q_data in enumerate(questions_data):
#             try:
#                 print(
#                     f"\n[parse_document] Processing question {idx + 1}/{len(questions_data)}")
#                 print(
#                     f"[parse_document] Raw question data: {json.dumps(q_data, indent=2, default=str)[:500]}")

#                 question_text = q_data.get('question_text', '').strip()
#                 if not question_text:
#                     error_msg = f"Question {idx + 1}: Missing question text"
#                     errors.append(error_msg)
#                     print(f"[parse_document] {error_msg}")
#                     continue

#                 options = q_data.get('options', [])
#                 if not options:
#                     error_msg = f"Question {idx + 1}: Missing options"
#                     errors.append(error_msg)
#                     print(f"[parse_document] {error_msg}")
#                     continue

#                 # Normalize options - preserve explanations if provided
#                 normalized_options = []
#                 option_texts = []  # Track option texts for validation
#                 for opt in options:
#                     if isinstance(opt, dict):
#                         opt_text = opt.get('text', '').strip()
#                         if opt_text:
#                             # Preserve explanation if it exists
#                             opt_dict = {"text": opt_text}
#                             if 'explanation' in opt and opt.get('explanation'):
#                                 opt_dict['explanation'] = str(
#                                     opt.get('explanation', '')).strip()
#                             normalized_options.append(opt_dict)
#                             option_texts.append(opt_text)
#                     elif isinstance(opt, str):
#                         opt_text = opt.strip()
#                         if opt_text:
#                             normalized_options.append({"text": opt_text})
#                             option_texts.append(opt_text)

#                 if len(normalized_options) < 2:
#                     error_msg = f"Question {idx + 1}: Need at least 2 options, got {len(normalized_options)}"
#                     errors.append(error_msg)
#                     print(f"[parse_document] {error_msg}")
#                     continue

#                 correct_answers = q_data.get('correct_answers', [])
#                 if not correct_answers:

#                     logger.warning(f"Question {idx}: No correct answers provided — saving as input")

#                     correct_answers = []
#                     status = "input"   # or "draft" / "needs_review"
#                 else:
#                     status = "ready"

#                 if not isinstance(correct_answers, list):
#                     correct_answers = [correct_answers]

#                 # Normalize correct answers (remove empty strings, strip whitespace)
#                 correct_answers = [str(ca).strip()
#                                    for ca in correct_answers if str(ca).strip()]

#                 if not correct_answers:
#                     logger.warning(
#                         f"Question {idx}: No valid correct answers after normalization — saving as input"
#                     )

#                     normalized_correct_answers = []
#                     status = "input"
#                 else:
#                     status = "ready"

#                 # Validate and match correct answers to option texts
#                 # Try to match correct answers to option texts (case-insensitive)
#                 validated_correct_answers = []
#                 for ca in correct_answers:
#                     ca_str = str(ca).strip()
#                     if not ca_str:
#                         continue

#                     ca_lower = ca_str.lower()
#                     matched = False

#                     # Try exact match first (case-insensitive)
#                     for opt_text in option_texts:
#                         if opt_text.lower().strip() == ca_lower:
#                             validated_correct_answers.append(
#                                 opt_text)  # Use the actual option text
#                             matched = True
#                             break

#                     if not matched:
#                         # Try partial match (contains)
#                         for opt_text in option_texts:
#                             if ca_lower in opt_text.lower() or opt_text.lower() in ca_lower:
#                                 validated_correct_answers.append(opt_text)
#                                 matched = True
#                                 break

#                     if not matched:
#                         # Try letter-based answer (A, B, C, D, etc.)
#                         if len(ca_str) == 1 and ca_str.upper() in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
#                             letter_index = ord(ca_str.upper()) - ord('A')
#                             if 0 <= letter_index < len(option_texts):
#                                 validated_correct_answers.append(
#                                     option_texts[letter_index])
#                                 matched = True

#                     if not matched:
#                         # Try numeric index (0, 1, 2, 3, etc.)
#                         try:
#                             num_index = int(ca_str)
#                             if 0 <= num_index < len(option_texts):
#                                 validated_correct_answers.append(
#                                     option_texts[num_index])
#                                 matched = True
#                         except ValueError:
#                             pass

#                     # If still not matched, try to use the answer as-is or find closest match
#                     if not matched:
#                         # If this is the first correct answer and we have no matches yet, try to use it as-is
#                         # or use first option as fallback
#                         if not validated_correct_answers:
#                             # Try to use the answer as-is first (might work if it's close enough)
#                             # But if it's clearly not an option text, use first option
#                             if len(ca_str) > 20 or ca_str.lower() in ['true', 'false', 'yes', 'no']:
#                                 # Probably not an option text, use first option
#                                 if option_texts:
#                                     validated_correct_answers.append(
#                                         option_texts[0])
#                                     print(
#                                         f"[parse_document] Question {idx + 1}: Correct answer '{ca_str}' doesn't match options, using first option as fallback")
#                                 else:
#                                     validated_correct_answers.append(ca_str)
#                             else:
#                                 # Might be an option text, use as-is
#                                 validated_correct_answers.append(ca_str)
#                                 print(
#                                     f"[parse_document] Question {idx + 1}: Using correct answer '{ca_str}' as-is (could not match to options)")
#                         else:
#                             # We already have some matches, skip this unmatchable one
#                             print(
#                                 f"[parse_document] Question {idx + 1}: Could not match correct answer '{ca_str}', skipping (already have {len(validated_correct_answers)} match(es))")

#                 # Ensure we have at least one correct answer
#                 if not validated_correct_answers:
#                     if option_texts:
#                         # Use first option as default
#                         validated_correct_answers = [option_texts[0]]
#                         print(
#                             f"[parse_document] Question {idx + 1}: No valid correct answers found, using first option '{option_texts[0]}' as default")
#                     else:
#                         error_msg = f"Question {idx + 1}: No options available to set as correct answer"
#                         errors.append(error_msg)
#                         print(f"[parse_document] {error_msg}")
#                         continue

#                 print(
#                     f"[parse_document] Question {idx + 1}: Validated correct answers: {validated_correct_answers}")

#                 question_type = q_data.get('question_type', 'single')
#                 if question_type not in ['single', 'multiple']:
#                     question_type = 'single' if len(
#                         validated_correct_answers) == 1 else 'multiple'

#                 # Normalize tags
#                 tags = q_data.get('tags', [])
#                 if isinstance(tags, str):
#                     tags = [t.strip() for t in tags.split(',') if t.strip()]
#                 elif not isinstance(tags, list):
#                     tags = []

#                 # Create question
#                 try:
#                     print(
#                         f"[parse_document] Question {idx + 1}: Creating Question object...")
#                     print(
#                         f"[parse_document] Question {idx + 1}: question_text length={len(question_text)}")
#                     print(
#                         f"[parse_document] Question {idx + 1}: question_type={question_type}")
#                     print(
#                         f"[parse_document] Question {idx + 1}: options count={len(normalized_options)}")
#                     print(
#                         f"[parse_document] Question {idx + 1}: correct_answers={validated_correct_answers}")
#                     print(
#                         f"[parse_document] Question {idx + 1}: course={default_course.id}")

#                     # Create CraftsmanQuestion with status field and link to session
#                     question = CraftsmanQuestion(
#                         course=default_course,
#                         parsing_session=parsing_session,  # Link to parsing session
#                         question_text=question_text,
#                         question_type=question_type,
#                         options=normalized_options,
#                         # correct_answers=validated_correct_answers,
#                         # explanation=q_data.get('explanation', '') or '',
#                         tags=tags,
#                         status='input'  # Mark as input question
#                     )
#                     print(
#                         f"[parse_document] Question {idx + 1}: Creating CraftsmanQuestion with status='input'")

#                     print(
#                         f"[parse_document] Question {idx + 1}: Question object created, calling save()...")
#                     question.save()
#                     print(
#                         f"[parse_document] Question {idx + 1}: ✅ save() completed successfully")

#                     # Verify question was actually saved to database
#                     try:
#                         saved_question = CraftsmanQuestion.objects.get(
#                             id=question.id)
#                         saved_status = saved_question.status
#                         print(
#                             f"[parse_document] Question {idx + 1}: ✅ Verified in database - ID: {saved_question.id}")
#                         print(
#                             f"[parse_document] Question {idx + 1}: ✅ Database verification - question_text length: {len(saved_question.question_text)}")
#                         print(
#                             f"[parse_document] Question {idx + 1}: ✅ Database verification - status: {saved_status}")

#                         saved_count += 1
#                         print(
#                             f"[parse_document] Question {idx + 1}: ✅ Successfully saved and verified: {question_text[:50]}...")
#                         print(
#                             f"[parse_document] Question {idx + 1}: ✅ TOTAL SAVED COUNT: {saved_count}")
#                     except CraftsmanQuestion.DoesNotExist:
#                         print(
#                             f"[parse_document] Question {idx + 1}: ❌ ERROR - Question not found in database after save()!")
#                         error_msg = f"Question {idx + 1}: Question was not saved to database (DoesNotExist after save)"
#                         errors.append(error_msg)
#                     except Exception as verify_error:
#                         print(
#                             f"[parse_document] Question {idx + 1}: ⚠️ Warning - Could not verify in database: {verify_error}")
#                         saved_count += 1  # Still count as saved if save() succeeded

#                 except Exception as save_error:
#                     error_msg = f"Question {idx + 1}: Failed to save - {str(save_error)}"
#                     errors.append(error_msg)
#                     print(
#                         f"[parse_document] Question {idx + 1}: ❌ {error_msg}")
#                     import traceback
#                     print(
#                         f"[parse_document] Question {idx + 1}: Full traceback:")
#                     print(traceback.format_exc())
#             except Exception as e:
#                 error_msg = f"Question {idx + 1}: Unexpected error - {str(e)}"
#                 errors.append(error_msg)
#                 print(f"[parse_document] {error_msg}")
#                 import traceback
#                 print(traceback.format_exc())

#         # Update parsing session with statistics
#         session_obj_id = ObjectId(str(parsing_session.id))
#         session_questions = CraftsmanQuestion.objects(
#             parsing_session=session_obj_id)
#         input_count = session_questions.filter(status='input').count()
#         # Count all generated questions (both validated and not validated)
#         generated_count = session_questions.filter(status__in=['generated', 'manual_review']).count()
#         total_count = session_questions.count()
        
#         print(f"\n[parse_document] ===== SESSION STATISTICS =====")
#         print(f"[parse_document] Session ID: {parsing_session.id}")
#         print(f"[parse_document] Session name: {parsing_session.session_name}")
#         print(f"[parse_document] Questions processed: {len(questions_data)}")
#         print(f"[parse_document] Questions successfully saved: {saved_count}")
#         print(f"[parse_document] Questions with errors: {len(errors)}")
#         print(f"[parse_document] Total questions in session (input): {input_count}")
#         print(f"[parse_document] Total questions in session (generated): {generated_count}")
#         print(f"[parse_document] Total questions in session (all): {total_count}")
        
#         if saved_count < len(questions_data):
#             print(f"[parse_document] ⚠️ WARNING: Only saved {saved_count} out of {len(questions_data)} questions!")
#             if errors:
#                 print(f"[parse_document] Errors encountered:")
#                 for error in errors[:10]:  # Show first 10 errors
#                     print(f"[parse_document]   - {error}")
#         else:
#             print(f"[parse_document] ✅ SUCCESS: All {saved_count} questions saved successfully!")

#         parsing_session.total_questions = total_count
#         parsing_session.input_questions_count = input_count
#         parsing_session.generated_questions_count = generated_count
#         parsing_session.status = 'completed' if saved_count > 0 else 'failed'
#         parsing_session.errors = errors
#         parsing_session.completed_at = datetime.datetime.utcnow()
#         parsing_session.save()
#         print(
#             f"[parse_document] Updated parsing session {parsing_session.id}: {saved_count} questions saved, total: {total_count}")

#         # Update course question count (count CraftsmanQuestions)
#         if default_course:
#             input_questions_count = CraftsmanQuestion.objects(
#                 course=default_course, status='input').count()
#             print(
#                 f"[parse_document] Questions with status='input' in craftsman_questions collection: {input_questions_count}")

#             # Note: We're not updating course.questions count here since CraftsmanQuestions are separate
#             # If you want to track craftsman questions separately, consider adding a craftsman_questions field to Course

#         # Final database verification
#         print(f"\n[parse_document] ===== FINAL DATABASE VERIFICATION =====")
#         try:
#             all_questions = CraftsmanQuestion.objects(course=default_course)
#             total_in_db = all_questions.count()
#             print(
#                 f"[parse_document] Total CraftsmanQuestions in database for this course: {total_in_db}")

#             # Count by status
#             input_questions = CraftsmanQuestion.objects(
#                 course=default_course, status='input')
#             input_count = input_questions.count()
#             print(
#                 f"[parse_document] Questions with status='input' in craftsman_questions collection: {input_count}")

#             # Show last few questions saved
#             recent_questions = CraftsmanQuestion.objects(
#                 course=default_course).order_by('-created_at')[:5]
#             print(f"[parse_document] Last 5 CraftsmanQuestions in database:")
#             for q in recent_questions:
#                 q_text = q.question_text[:50] if q.question_text else 'N/A'
#                 q_status = q.status
#                 print(
#                     f"[parse_document]   - ID: {q.id}, Text: {q_text}..., Status: {q_status}")
#         except Exception as verify_error:
#             print(
#                 f"[parse_document] Error during final verification: {verify_error}")

#         print(f"\n[parse_document] ===== SUMMARY =====")
#         print(f"[parse_document] Total parsed: {len(questions_data)}")
#         print(f"[parse_document] Successfully saved: {saved_count}")
#         print(f"[parse_document] Errors: {len(errors)}")
#         if errors:
#             print(f"[parse_document] Error details: {errors}")
#         print(f"[parse_document] ====================\n")

#         # Create detailed message
#         if saved_count > 0:
#             message = f"✅ Successfully parsed {len(questions_data)} questions and saved {saved_count} question(s) to database"
#             if len(errors) > 0:
#                 message += f" ({len(errors)} question(s) had errors)"
#         else:
#             message = f"⚠️ Parsed {len(questions_data)} questions but saved 0 to database. Check errors for details."

#         print(f"[parse_document] ===== RETURNING RESPONSE =====")
#         print(f"[parse_document] Response message: {message}")
#         print(f"[parse_document] saved_count: {saved_count}")
#         print(
#             f"[parse_document] Total CraftsmanQuestions now in database for this course: {CraftsmanQuestion.objects(course=default_course).count() if default_course else 'N/A'}")

#         return JsonResponse({
#             "success": saved_count > 0,
#             "message": message,

#             # Counts
#             "parsed_count": len(questions_data),
#             "saved_count": saved_count,
#             "database_count": CraftsmanQuestion.objects(course=default_course).count() if default_course else 0,

#             # Errors
#             "errors": errors,

#             # Session
#             "session_id": str(parsing_session.id),

#             # 🔹 NEW: columns shown in Input Questions tab
#             "input_columns": [
#                 "id",
#                 "question_text",
#                 "option_a",
#                 "option_b",
#                 "option_c",
#                 "option_d",
#                 "parsing_flag",
#                 "status"
#             ],
#             "questions": questions_data
#         })

#     except Exception as e:
#         import traceback
#         error_msg = str(e)
#         print(f"[parse_document] Error: {error_msg}")
#         print(traceback.format_exc())
#         return JsonResponse({"success": False, "error": error_msg}, status=500)


# # ✅ Generate new questions from input (Admin) - Using OpenAI
# @api_view(['POST'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def generate_from_input(request):
#     """Admin: Generate new questions from input questions using OpenAI"""
#     try:
#         from settings_app.models import AdminSettings
#         import os
#         # Get configuration
#         settings_obj = AdminSettings.objects.first()
#         if not settings_obj:
#             settings_obj = AdminSettings()

#         # Get prompts
#         saved_prompts = getattr(settings_obj, 'prompts', {}) or {}
#         prompt2 = saved_prompts.get('prompt2', {})
#         generation_prompt = prompt2.get('prompt', '') if prompt2 else ''
#         # 🔥 ADD THESE DEBUG LINES
#         print("PROMPTS FROM DB:", saved_prompts)
#         print("PROMPT2 OBJECT:", prompt2)
#         print("GENERATION PROMPT:", generation_prompt)

#         # If no generation prompt, do not process — show message and no questions in tabs
#         if not generation_prompt or not generation_prompt.strip():
#             return JsonResponse({
#                 "success": False,
#                 "error": "Please provide the prompt."
#             }, status=400)

#         # Get parameters
#         data = request.data
#         question_ids = data.get('question_ids', [])
#         num_questions_per_source = int(data.get('num_questions_per_source', 1))
#         session_id = data.get('session_id', None)

#         # Check if OpenAI is available
#         if not OPENAI_AVAILABLE or not openai:
#             return JsonResponse({"success": False, "error": "OpenAI API not available. Please install openai package."}, status=500)

#         # Initialize OpenAI - Check database first, then environment variables
#         # Try to load .env file if not already loaded (settings.py loads it, but ensure it's accessible)
#         try:
#             from dotenv import load_dotenv
#             from pathlib import Path
#             # Use same BASE_DIR calculation as settings.py
#             BASE_DIR = Path(__file__).resolve().parent.parent
#             env_file = os.path.join(BASE_DIR, '.env')
#             if os.path.exists(env_file):
#                 load_dotenv(env_file, override=False)
#         except Exception as e:
#             print(
#                 f"[generate_from_input] Warning: Could not load .env file: {e}")

#         # Check for API key: database first, then environment variables, then Django settings
#         openai_api_key = None

#         # First check database
#         db_key = getattr(settings_obj, 'openai_api_key', None)
#         if db_key and str(db_key).strip():
#             openai_api_key = str(db_key).strip()

#         # Then check environment variables (already loaded by settings.py)
#         if not openai_api_key:
#             openai_api_key = os.environ.get('OPENAI_API_KEY', '').strip()

#         # Also try Django settings if available
#         if not openai_api_key:
#             try:
#                 from django.conf import settings as django_settings
#                 if hasattr(django_settings, 'OPENAI_API_KEY') and django_settings.OPENAI_API_KEY:
#                     openai_api_key = django_settings.OPENAI_API_KEY.strip()
#             except:
#                 pass

#         if not openai_api_key:
#             return JsonResponse({
#                 "success": False,
#                 "error": "OPENAI_API_KEY not found. Please add it to AdminSettings (openai_api_key field) or set OPENAI_API_KEY=your_key in .env file in backend directory."
#             }, status=500)

#         # Get input questions from CraftsmanQuestion collection
#         if question_ids:
#             # Generate from specific questions
#             questions = []
#             for qid in question_ids:
#                 if ObjectId.is_valid(qid):
#                     try:
#                         q = CraftsmanQuestion.objects.get(
#                             id=ObjectId(qid), status='input')
#                         # If session_id is provided, only include questions from that session
#                         if session_id:
#                             if q.parsing_session and str(q.parsing_session.id) == str(session_id):
#                                 questions.append(q)
#                         else:
#                             questions.append(q)
#                     except CraftsmanQuestion.DoesNotExist:
#                         continue
#         else:
#             # Generate from input questions, optionally filtered by session
#             if session_id:
#                 if not ObjectId.is_valid(session_id):
#                     return JsonResponse({"success": False, "error": "Invalid session_id"}, status=400)
#                 try:
#                     parsing_session = ParsingSession.objects.get(
#                         id=ObjectId(session_id))
#                     questions = CraftsmanQuestion.objects(
#                         status='input', parsing_session=parsing_session).order_by('-created_at')
#                     questions_count = questions.count()
#                     print(
#                         f"[generate_from_input] Filtering input questions by session_id: {session_id}")
#                     print(f"[generate_from_input] Found {questions_count} input questions in session {session_id} ({parsing_session.session_name})")
#                 except ParsingSession.DoesNotExist:
#                     return JsonResponse({"success": False, "error": "Session not found"}, status=400)
#             else:
#                 # No session_id provided - return empty (new session, no questions yet)
#                 questions = []
#                 print(
#                     f"[generate_from_input] No session_id provided - cannot generate (new session)")

#         if not questions:
#             return JsonResponse({"success": False, "error": "No input questions found to generate from"}, status=400)

#         # Get default course
#         default_course = Course.objects.first()
#         if not default_course:
#             return JsonResponse({"success": False, "error": "No course found. Please create a course first."}, status=400)

#         # Find the parsing session from input questions (if they have one)
#         # IMPORTANT: Always use the same session as input questions to ensure generated questions
#         # are visible in the same session context
#         # CRITICAL: Use the session_id from the request, which should be the parsing session
#         if session_id and ObjectId.is_valid(session_id):
#             try:
#                 generation_session = ParsingSession.objects.get(
#                     id=ObjectId(session_id))
#                 print(
#                     f"[generate_from_input] Using provided session_id: {session_id}")
#                 print(
#                     f"[generate_from_input] Generation session: {generation_session.id} - {generation_session.session_name}")
                
#                 # Verify that input questions belong to this session
#                 questions_list = list(questions) if hasattr(questions, '__iter__') and not isinstance(questions, list) else questions
#                 if questions_list:
#                     first_question_session = questions_list[0].parsing_session
#                     if first_question_session and str(first_question_session.id) != str(session_id):
#                         print(f"[generate_from_input] WARNING: Input questions belong to different session ({first_question_session.id}) than provided session_id ({session_id})")
#                         print(f"[generate_from_input] Using the session from input questions instead: {first_question_session.id}")
#                         generation_session = first_question_session
#                     else:
#                         print(f"[generate_from_input] Verified: Input questions belong to the same session ({session_id})")
#             except ParsingSession.DoesNotExist:
#                 return JsonResponse({"success": False, "error": "Session not found"}, status=400)
#         else:
#             # Use the session from the input questions - ensure all generated questions use the same session
#             questions_list = list(questions) if hasattr(questions, '__iter__') and not isinstance(questions, list) else questions
#             input_question_sessions = set()
#             for q in questions_list:
#                 if q.parsing_session:
#                     input_question_sessions.add(q.parsing_session)

#             # If all input questions belong to the same session, use that session
#             # This ensures generated questions are in the same session as input questions
#             if len(input_question_sessions) == 1:
#                 generation_session = list(input_question_sessions)[0]
#                 print(
#                     f"[generate_from_input] Using existing parsing session from input questions: {generation_session.id} - {generation_session.session_name}")
#             elif len(input_question_sessions) > 1:
#                 # Multiple sessions - use the first one (shouldn't happen, but handle it)
#                 generation_session = list(input_question_sessions)[0]
#                 print(
#                     f"[generate_from_input] Multiple sessions found, using first: {generation_session.id} - {generation_session.session_name}")
#             else:
#                 # No session found - this shouldn't happen if questions were parsed correctly
#                 return JsonResponse({"success": False, "error": "Input questions have no session. Please parse a document first."}, status=400)
        
#         # Final verification: Log the session that will be used for generated questions
#         print(f"[generate_from_input] FINAL: Generated questions will be linked to session: {generation_session.id} ({generation_session.session_name})")

#         # Get configuration
#         max_retries = getattr(settings_obj, 'max_retry_count', 3)
#         temperature = getattr(settings_obj, 'temperature', 0)
#         model_name = getattr(
#             settings_obj, 'model_selector', 'gpt-4') or 'gpt-4'
#         top_p = getattr(settings_obj, 'top_p', 1.0)
#         frequency_penalty = getattr(settings_obj, 'frequency_penalty', 0.0)
#         presence_penalty = getattr(settings_obj, 'presence_penalty', 0.0)
#         max_output_tokens = getattr(settings_obj, 'max_output_tokens', 2000)

#         saved_count = 0
#         errors = []
        
#         # Convert to list if it's a queryset to ensure we can iterate properly
#         questions_list = list(questions) if hasattr(questions, '__iter__') and not isinstance(questions, list) else questions
#         total_input_questions = len(questions_list)
#         print(f"[generate_from_input] Starting generation for {total_input_questions} input question(s)")

#         # Generate questions from each input question
#         for idx, source_question in enumerate(questions_list, 1):
#             print(f"[generate_from_input] ========================================")
#             print(f"[generate_from_input] Processing input question {idx}/{total_input_questions} (ID: {source_question.id})")
#             print(f"[generate_from_input] Source question text: {source_question.question_text[:100]}...")
#             for _ in range(num_questions_per_source):
#                 try:
#                     # Prepare prompt - use user's prompt exactly as provided
#                     # Format source question options with explanations if available
#                     source_options_str = []
#                     for opt in source_question.options:
#                         if isinstance(opt, dict):
#                             opt_str = opt.get('text', '')
#                             if opt.get('explanation'):
#                                 opt_str += f" (Explanation: {opt.get('explanation')})"
#                             source_options_str.append(opt_str)
#                         else:
#                             source_options_str.append(str(opt))

#                     # Get source question tags for reference
#                     source_tags = source_question.tags or []
#                     if isinstance(source_tags, str):
#                         source_tags = [t.strip() for t in source_tags.split(',') if t.strip()]
#                     source_tags_str = ', '.join(source_tags) if source_tags else 'N/A'

#                     # Use user's prompt exactly as provided, with source question context
#                     # Check if prompt is provided - if not, skip this question
#                     if not generation_prompt or not generation_prompt.strip():
#                         errors.append(f"Input question {idx}: No generation prompt configured. Please configure Prompt 2 in Admin Settings.")
#                         print(f"[generate_from_input] Skipping question {idx} - no generation prompt configured")
#                         continue
                    
#                     # Build full prompt using only the dynamic prompt from configuration
#                     full_prompt = f"{generation_prompt}\n\nSource question:\nQuestion: {source_question.question_text}\nOptions: {source_options_str}\nCorrect Answer: {source_question.correct_answers}\nExplanation: {source_question.explanation or 'N/A'}\nDomain/Tags: {source_tags_str}"

#                     # Call OpenAI - use only dynamic prompt, no hardcoded system message
#                     response_text = None
#                     try:
#                         # Try new OpenAI API format (v1.0+)
#                         client = openai.OpenAI(api_key=openai_api_key)
#                         response = client.chat.completions.create(
#                             model=model_name,
#                             messages=[
#                                 {"role": "user", "content": full_prompt}
#                             ],
#                             temperature=temperature,
#                             top_p=top_p,
#                             frequency_penalty=frequency_penalty,
#                             presence_penalty=presence_penalty,
#                             max_tokens=max_output_tokens
#                         )
#                         # Check if response has content
#                         if response and response.choices and len(response.choices) > 0:
#                             message = response.choices[0].message
#                             if message and message.content:
#                                 response_text = message.content.strip()
#                     except AttributeError:
#                         # Fallback to old API format
#                         try:
#                             openai.api_key = openai_api_key
#                             response = openai.ChatCompletion.create(
#                                 model=model_name,
#                                 messages=[
#                                     {"role": "user", "content": full_prompt}
#                                 ],
#                                 temperature=temperature,
#                                 top_p=top_p,
#                                 frequency_penalty=frequency_penalty,
#                                 presence_penalty=presence_penalty,
#                                 max_tokens=max_output_tokens
#                             )
#                             print("response in fallback", response)
#                             # Check if response has content
#                             if response and response.choices and len(response.choices) > 0:
#                                 message = response.choices[0].message
#                                 if message and message.content:
#                                     response_text = message.content.strip()
#                         except Exception as fallback_error:
#                             error_msg = f"OpenAI API error (fallback): {str(fallback_error)}"
#                             errors.append(error_msg)
#                             print(f"[generate_from_input] {error_msg}")
#                             continue
#                     except Exception as openai_error:
#                         error_msg = f"OpenAI API error: {str(openai_error)}"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] {error_msg}")
#                         continue

#                     # Check if response_text is empty or None
#                     if not response_text:
#                         error_msg = f"Empty response from OpenAI API for input question {idx}"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] {error_msg}")
#                         print(f"[generate_from_input] Response object: {response}")
#                         continue

#                     # Extract JSON with multiple strategies
#                     import re
#                     q_data = None
                    
#                     # Strategy 1: Try to extract from markdown code blocks
#                     code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL | re.IGNORECASE)
#                     if code_block_match:
#                         try:
#                             q_data = json.loads(code_block_match.group(1))
#                             print(f"[generate_from_input] ✅ Extracted JSON from code block")
#                         except:
#                             pass
                    
#                     # Strategy 2: Try to find JSON object with balanced braces
#                     if not q_data:
#                         brace_count = 0
#                         start_idx = -1
#                         for i, char in enumerate(response_text):
#                             if char == '{':
#                                 if brace_count == 0:
#                                     start_idx = i
#                                 brace_count += 1
#                             elif char == '}':
#                                 brace_count -= 1
#                                 if brace_count == 0 and start_idx != -1:
#                                     json_str = response_text[start_idx:i+1]
#                                     try:
#                                         q_data = json.loads(json_str)
#                                         print(f"[generate_from_input] ✅ Extracted JSON using balanced braces")
#                                         break
#                                     except:
#                                         # Try fixing trailing commas
#                                         try:
#                                             fixed = re.sub(r',\s*}', '}', json_str)
#                                             fixed = re.sub(r',\s*]', ']', fixed)
#                                             q_data = json.loads(fixed)
#                                             print(f"[generate_from_input] ✅ Extracted JSON after fixing trailing commas")
#                                             break
#                                         except:
#                                             continue
                    
#                     # Strategy 3: Try regex match (non-greedy)
#                     if not q_data:
#                         json_match = re.search(r'\{.*?\}', response_text, re.DOTALL)
#                         if json_match:
#                             try:
#                                 q_data = json.loads(json_match.group())
#                                 print(f"[generate_from_input] ✅ Extracted JSON using regex")
#                             except:
#                                 pass
                    
#                     # Strategy 4: Try parsing entire response
#                     if not q_data:
#                         try:
#                             q_data = json.loads(response_text.strip())
#                             print(f"[generate_from_input] ✅ Parsed entire response as JSON")
#                         except:
#                             pass
                    
#                     # If still no data, log and continue
#                     if not q_data:
#                         error_msg = f"Could not extract valid JSON from OpenAI response for input question {idx}"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] ❌ {error_msg}")
#                         print(f"[generate_from_input] Response text (first 1000 chars): {response_text[:1000]}")
#                         continue
                    
#                     print(f"[generate_from_input] ✅ Successfully extracted JSON data")
#                     print(f"[generate_from_input] Extracted JSON keys: {list(q_data.keys()) if isinstance(q_data, dict) else 'Not a dict'}")
#                     # Debug: Print full q_data structure (first 2000 chars) to see what AI returned
#                     q_data_str = json.dumps(q_data, indent=2, default=str)
#                     print(f"[generate_from_input] Full q_data structure (first 2000 chars):\n{q_data_str[:2000]}")

#                     # Validate and save question
#                     # Try multiple possible field names for question text
#                     question_text = (q_data.get('question_text') or 
#                                    q_data.get('question') or 
#                                    q_data.get('text') or 
#                                    q_data.get('prompt') or q_data.get('Question') or '').strip()
                    
#                     if not question_text:
#                         error_msg = f"Generated question {idx}: Missing question text"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] ❌ {error_msg}")
#                         print(f"[generate_from_input] Available keys in JSON: {list(q_data.keys()) if isinstance(q_data, dict) else 'N/A'}")
#                         continue

#                     # Try multiple possible field names for options
#                     options = (q_data.get('options') or 
#                               q_data.get('choices') or 
#                               q_data.get('option_list') or 
#                               q_data.get('answers') or 
#                               q_data.get('alternatives') or q_data.get('Options') or [])
                    
#                     # If options is not a list, try to convert it
#                     if options and not isinstance(options, list):
#                         if isinstance(options, dict):
#                             # If it's a dict, try to extract values
#                             options = list(options.values()) if options else []
#                         elif isinstance(options, str):
#                             # If it's a string, try to split it
#                             options = [opt.strip() for opt in options.split(',') if opt.strip()]
#                         else:
#                             options = [options]
                    
#                     # Check for option_a, option_b, option_c format (with per-option explanation)
#                     if not options or len(options) == 0:
#                         extracted_options = []
#                         option_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
#                         for letter in option_letters:
#                             option_key = f'option_{letter}'
#                             explanation_key = f'option_{letter}_explanation'
#                             explanation_key_alt = f'option_{letter}_Explaination'
#                             if option_key in q_data:
#                                 opt_text = str(q_data[option_key]).strip()
#                                 if opt_text:
#                                     opt_dict = {"text": opt_text}
#                                     exp_val = q_data.get(explanation_key) or q_data.get(explanation_key_alt)
#                                     opt_dict['explanation'] = str(exp_val).strip() if exp_val else ''
#                                     extracted_options.append(opt_dict)
#                         if extracted_options:
#                             options = extracted_options
#                             print(f"[generate_from_input] ✅ Extracted {len(options)} options with per-option explanations from option_a/option_b format")
                    
#                     # If still no options, try numbered format (option_1, option_2, etc.)
#                     if not options or len(options) == 0:
#                         extracted_options = []
#                         for num in range(1, 10):
#                             option_key = f'option_{num}'
#                             explanation_key = f'option_{num}_explanation'
#                             explanation_key_alt = f'option_{num}_Explaination'
#                             if option_key in q_data:
#                                 opt_text = str(q_data[option_key]).strip()
#                                 if opt_text:
#                                     opt_dict = {"text": opt_text}
#                                     exp_val = q_data.get(explanation_key) or q_data.get(explanation_key_alt)
#                                     opt_dict['explanation'] = str(exp_val).strip() if exp_val else ''
#                                     extracted_options.append(opt_dict)
#                             else:
#                                 break
#                         if extracted_options:
#                             options = extracted_options
#                             print(f"[generate_from_input] ✅ Extracted {len(options)} options from option_1/option_2 format")
                    
#                     if not options or len(options) == 0:
#                         error_msg = f"Generated question {idx}: Missing options"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] ❌ {error_msg}")
#                         print(f"[generate_from_input] Available keys in JSON: {list(q_data.keys()) if isinstance(q_data, dict) else 'N/A'}")
#                         print(f"[generate_from_input] Full JSON data: {json.dumps(q_data, indent=2)[:1000]}")
#                         continue
                    
#                     print(f"[generate_from_input] ✅ Question text extracted: {question_text[:50]}...")
#                     print(f"[generate_from_input] ✅ Options count: {len(options)}")
#                     print(f"[generate_from_input] Options data: {options}")
#                     # Debug: Check for explanation keys in q_data
#                     explanation_keys = [k for k in q_data.keys() if 'explanation' in k.lower() or 'Explaination' in k]
#                     if explanation_keys:
#                         print(f"[generate_from_input] Found explanation keys in q_data: {explanation_keys}")
#                     else:
#                         print(f"[generate_from_input] ⚠️ No explanation keys found in q_data. Available keys: {list(q_data.keys())[:20]}")

#                     normalized_options = []
#                     for opt in options:
#                         if isinstance(opt, dict):
#                             opt_text = (opt.get('text') or 
#                                        opt.get('option') or 
#                                        opt.get('choice') or 
#                                        opt.get('value') or 
#                                        opt.get('label') or 
#                                        str(opt.get('answer', '')) or '').strip()
#                             if opt_text:
#                                 opt_dict = {"text": opt_text}
#                                 # Per-option explanation (always set key so UI shows "—" when empty)
#                                 exp = (opt.get('explanation') or opt.get('reason') or 
#                                        opt.get('rationale') or opt.get('Explaination') or '')
#                                 opt_dict['explanation'] = str(exp).strip() if exp else ''
#                                 normalized_options.append(opt_dict)
#                         elif isinstance(opt, str):
#                             if opt.strip():
#                                 normalized_options.append({"text": opt.strip(), "explanation": ''})
#                         elif opt is not None:
#                             opt_str = str(opt).strip()
#                             if opt_str:
#                                 normalized_options.append({"text": opt_str, "explanation": ''})
                    
#                     # Extract option explanations from "Explanation" dict (AI returns option text -> explanation mapping)
#                     explanation_dict = None
#                     if 'Explanation' in q_data and isinstance(q_data.get('Explanation'), dict):
#                         explanation_dict = q_data.get('Explanation')
#                         print(f"[generate_from_input] ✅ Found Explanation dict with {len(explanation_dict)} entries")
#                     elif 'explanation' in q_data and isinstance(q_data.get('explanation'), dict):
#                         explanation_dict = q_data.get('explanation')
#                         print(f"[generate_from_input] ✅ Found explanation dict with {len(explanation_dict)} entries")
                    
#                     # Enrich option explanations from multiple sources
#                     # Priority: 1) Explanation dict (option text -> explanation), 2) option_X_explanation keys, 3) existing in array
#                     option_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
#                     explanations_found = 0
#                     for i, opt in enumerate(normalized_options):
#                         opt_text = opt.get('text', '').strip()
                        
#                         # Priority 1: Try to get explanation from Explanation dict (match by option text)
#                         if explanation_dict and opt_text:
#                             # Try exact match first
#                             if opt_text in explanation_dict:
#                                 exp_from_dict = str(explanation_dict[opt_text]).strip()
#                                 if exp_from_dict:
#                                     opt['explanation'] = exp_from_dict
#                                     explanations_found += 1
#                                     print(f"[generate_from_input] ✅ Matched explanation from Explanation dict for option {i+1}: {exp_from_dict[:50]}...")
#                             else:
#                                 # Try case-insensitive match
#                                 for key, value in explanation_dict.items():
#                                     if key.strip().lower() == opt_text.lower():
#                                         exp_from_dict = str(value).strip()
#                                         if exp_from_dict:
#                                             opt['explanation'] = exp_from_dict
#                                             explanations_found += 1
#                                             print(f"[generate_from_input] ✅ Matched explanation (case-insensitive) from Explanation dict for option {i+1}")
#                                             break
                        
#                         # Priority 2: Try option_X_explanation keys (if not already set from dict)
#                         if not opt.get('explanation') or not opt.get('explanation').strip():
#                             if i < len(option_letters):
#                                 letter = option_letters[i]
#                                 exp_from_key = (q_data.get(f'option_{letter}_explanation') or 
#                                                q_data.get(f'option_{letter}_Explaination') or 
#                                                q_data.get(f'Option_{letter}_explanation') or 
#                                                q_data.get(f'Option_{letter}_Explanation') or '')
#                                 if exp_from_key:
#                                     exp_from_key = str(exp_from_key).strip() if isinstance(exp_from_key, str) else ''
#                                     if exp_from_key:
#                                         opt['explanation'] = exp_from_key
#                                         explanations_found += 1
#                                         print(f"[generate_from_input] ✅ Found explanation for option {letter} from option_{letter}_explanation: {exp_from_key[:50]}...")
                        
#                         # Ensure every option has explanation key
#                         if 'explanation' not in opt or not opt.get('explanation'):
#                             opt['explanation'] = ''
                    
#                     if explanations_found > 0:
#                         print(f"[generate_from_input] ✅ Enriched {explanations_found} option explanations from Explanation dict/option_X_explanation keys")
#                     else:
#                         print(f"[generate_from_input] ⚠️ No option explanations found")
#                         # Debug: print all keys that might contain explanations
#                         all_keys = list(q_data.keys())
#                         exp_like_keys = [k for k in all_keys if any(word in k.lower() for word in ['explain', 'reason', 'rationale'])]
#                         if exp_like_keys:
#                             print(f"[generate_from_input] Found explanation-like keys: {exp_like_keys}")
                    
#                     # Validate that we have at least some normalized options
#                     if not normalized_options or len(normalized_options) == 0:
#                         error_msg = f"Generated question {idx}: Could not normalize options"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] ❌ {error_msg}")
#                         print(f"[generate_from_input] Original options: {options}")
#                         continue
                    
#                     print(f"[generate_from_input] ✅ Normalized {len(normalized_options)} options")

#                     # Try multiple possible field names for correct answers
#                     correct_answers = (q_data.get('correct_answers') or 
#                                       q_data.get('correct_answer') or 
#                                       q_data.get('answer') or 
#                                       q_data.get('answers') or 
#                                       q_data.get('solution') or q_data.get('Correct Answer') or [])
                    
#                     # If not a list, try to convert
#                     if correct_answers and not isinstance(correct_answers, list):
#                         if isinstance(correct_answers, str):
#                             # Split comma-separated answers
#                             correct_answers = [ans.strip() for ans in correct_answers.split(',') if ans.strip()]
#                         else:
#                             correct_answers = [correct_answers]


#                     # Check for correct_answer_a, correct_answer_b format
#                     if not correct_answers or len(correct_answers) == 0:
#                         extracted_answers = []
#                         option_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                        
#                         for letter in option_letters:
#                             answer_key = f'correct_answer_{letter}'
#                             if answer_key in q_data:
#                                 answer_text = str(q_data[answer_key]).strip()
#                                 if answer_text:
#                                     extracted_answers.append(answer_text)
                        
#                         if extracted_answers:
#                             correct_answers = extracted_answers
#                             print(f"[generate_from_input] ✅ Extracted correct answers from correct_answer_a/correct_answer_b format")
                    
#                     # Check for answer_a, answer_b format
#                     if not correct_answers or len(correct_answers) == 0:
#                         extracted_answers = []
#                         option_letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                        
#                         for letter in option_letters:
#                             answer_key = f'answer_{letter}'
#                             if answer_key in q_data:
#                                 answer_text = str(q_data[answer_key]).strip()
#                                 if answer_text:
#                                     extracted_answers.append(answer_text)
                        
#                         if extracted_answers:
#                             correct_answers = extracted_answers
#                             print(f"[generate_from_input] ✅ Extracted correct answers from answer_a/answer_b format")
                    
#                     # Don't skip: if correct_answers still empty, use first option as fallback (question goes to manual_review)
#                     if not correct_answers or len(correct_answers) == 0:
#                         if normalized_options and len(normalized_options) > 0:
#                             first_opt_text = normalized_options[0].get('text', '').strip()
#                             if first_opt_text:
#                                 correct_answers = [first_opt_text]
#                                 print(f"[generate_from_input] ⚠️ No correct answers found; using first option as fallback (question will go to manual review)")
#                             else:
#                                 error_msg = f"Generated question {idx}: Missing correct answers and no options to use as fallback"
#                                 errors.append(error_msg)
#                                 print(f"[generate_from_input] ❌ {error_msg}")
#                                 continue
#                         else:
#                             error_msg = f"Generated question {idx}: Missing correct answers"
#                             errors.append(error_msg)
#                             print(f"[generate_from_input] ❌ {error_msg}")
#                             continue
                    
#                     print(f"[generate_from_input] ✅ Correct answers: {correct_answers}")

#                     if not isinstance(correct_answers, list):
#                         correct_answers = [correct_answers]

#                     question_type = q_data.get('question_type', 'single')
#                     if question_type not in ['single', 'multiple']:
#                         question_type = 'single' if len(
#                             correct_answers) == 1 else 'multiple'

#                     # Extract tags from AI response, or inherit from source question
#                     ai_tags = q_data.get('tags', [])
#                     if not ai_tags or (isinstance(ai_tags, list) and len(ai_tags) == 0):
#                         # If AI didn't provide tags, inherit from source question
#                         source_tags = source_question.tags or []
#                         if isinstance(source_tags, str):
#                             source_tags = [t.strip() for t in source_tags.split(',') if t.strip()]
#                         elif not isinstance(source_tags, list):
#                             source_tags = []
#                         final_tags = source_tags
#                     else:
#                         # Normalize AI-provided tags
#                         if isinstance(ai_tags, str):
#                             final_tags = [t.strip() for t in ai_tags.split(',') if t.strip()]
#                         elif isinstance(ai_tags, list):
#                             final_tags = [str(t).strip() for t in ai_tags if t and str(t).strip()]
#                         else:
#                             final_tags = []

#                     # Validate that correct answers exactly match the options
#                     # Extract option texts for validation
#                     option_texts = [opt.get('text', '').strip() for opt in normalized_options if opt.get('text', '').strip()]
                    
#                     # Check if all correct answers match exactly (case-insensitive) with option texts
#                     all_answers_valid = True
#                     for correct_answer in correct_answers:
#                         correct_text = str(correct_answer).strip()
#                         if not correct_text:
#                             all_answers_valid = False
#                             break
                        
#                         # Check for exact match (case-insensitive)
#                         matched = False
#                         for opt_text in option_texts:
#                             if opt_text.lower() == correct_text.lower():
#                                 matched = True
#                                 break
                       
#                         if not matched:
#                             all_answers_valid = False
#                             break
                    
#                     # Determine status: 'generated' if all answers match, 'manual_review' if not
#                     # question_status = 'generated' if all_answers_valid else 'manual_review'
                    
#                     if not all_answers_valid:
#                         print(f"[generate_from_input] Question validation failed - correct answers don't match options exactly. Moving to manual review.")
#                         print(f"[generate_from_input] Options: {option_texts}")
#                         print(f"[generate_from_input] Correct answers: {correct_answers}")

#                     # Validate with Gemini AI using prompt3
#                     gemini_validation_passed = False
#                     max_retries = 3
#                     attempt = 0
#                     gemini_validation_passed = False

#                     while attempt < max_retries:
#                         attempt += 1
#                         print(f"[generate_from_input] 🔁 Gemini validation attempt {attempt}/{max_retries}")

#                         try:
#                             prompt3 = saved_prompts.get('prompt3', {})
#                             validation_prompt = prompt3.get('prompt', '') if prompt3 else ''

#                             if not validation_prompt:
#                                 print("[generate_from_input] No validation prompt provided, skipping validation")
#                                 gemini_validation_passed = True
#                             else:
#                                 overall_explanation = (q_data.get('explanation') or 
#                                                     q_data.get('overall_explanation') or 
#                                                     q_data.get('explanation_text') or 
#                                                     q_data.get('rationale') or 
#                                                     q_data.get('reason') or '').strip()

#                                 question_for_validation = {
#                                     "question_text": question_text,
#                                     "options": normalized_options,
#                                     "correct_answers": correct_answers,
#                                     "question_type": question_type,
#                                     "explanation": overall_explanation
#                                 }

#                                 gemini_api_key = None
#                                 db_key = getattr(settings_obj, 'gemini_api_key', None)
#                                 if db_key and str(db_key).strip():
#                                     gemini_api_key = str(db_key).strip()
#                                 if not gemini_api_key:
#                                     gemini_api_key = os.environ.get('GEMINI_API_KEY', '').strip()
#                                 if not gemini_api_key:
#                                     try:
#                                         from django.conf import settings as django_settings
#                                         if hasattr(django_settings, 'GEMINI_API_KEY') and django_settings.GEMINI_API_KEY:
#                                             gemini_api_key = django_settings.GEMINI_API_KEY.strip()
#                                     except:
#                                         pass

#                                 if gemini_api_key:
#                                     genai.configure(api_key=gemini_api_key)
#                                     gemini_model_selector = getattr(settings_obj, 'gemini_model_selector', 'gemini-1.5-flash-latest')
#                                     model_name_gemini = get_valid_gemini_model(gemini_model_selector, genai)

#                                     validation_full_prompt = f"{validation_prompt}\n\nQuestion to validate:\n{json.dumps(question_for_validation, indent=2)}"

#                                     model_gemini = genai.GenerativeModel(model_name_gemini)
#                                     validation_response = model_gemini.generate_content(
#                                         validation_full_prompt,
#                                         generation_config={'temperature': 0, 'max_output_tokens': 1000}
#                                     )

#                                     if validation_response and hasattr(validation_response, 'text'):
#                                         import re
#                                         match = re.search(r'\{.*\}', validation_response.text, re.DOTALL)
#                                         if match:
#                                             result = json.loads(match.group())
#                                             status = result.get("status", "").strip().upper()
#                                             gemini_validation_passed = (status == "CLEAN")
#                                             print(f"[generate_from_input] Gemini status: {status}")
#                                         else:
#                                             print("[generate_from_input] Could not parse Gemini response — treating as MANUAL_REVIEW")
#                                             gemini_validation_passed = False

#                                     else:
#                                         print("[generate_from_input] Gemini returned no response, assuming valid")
#                                         gemini_validation_passed = False
#                                 else:
#                                     print("[generate_from_input] No Gemini API key, skipping validation")
#                                     gemini_validation_passed = False

#                         except Exception as gemini_error:
#                             print(f"[generate_from_input] Gemini error: {gemini_error} — sending to manual review")
#                             gemini_validation_passed = False


#                         # ✅ STOP retrying immediately if validation passed
#                         if gemini_validation_passed:
#                             break

#                     # ✅ FINAL STATUS (single source of truth)
#                     # FINAL STATUS — Gemini can only downgrade, never upgrade
#                     if not all_answers_valid:
#                         question_status = 'manual_review'
#                     elif not gemini_validation_passed:
#                         question_status = 'manual_review'
#                     else:
#                         question_status = 'generated'

                                    
#                     # Create generated question in CraftsmanQuestion collection and link to session
#                     # Debug: Print normalized options with explanations before saving
#                     print(f"[generate_from_input] ===== NORMALIZED OPTIONS BEFORE SAVING =====")
#                     for i, opt in enumerate(normalized_options):
#                         opt_text = opt.get('text', '')[:50] if opt.get('text') else ''
#                         opt_exp = opt.get('explanation', '')[:50] if opt.get('explanation') else '(empty)'
#                         print(f"[generate_from_input] Option {i+1}: text='{opt_text}...', explanation='{opt_exp}...'")
#                     print(f"[generate_from_input] ============================================")
                    
#                     print(f"[generate_from_input] Attempting to save question {idx} with status: {question_status}")
#                     print(f"[generate_from_input] Question text: {question_text[:100]}...")
#                     print(f"[generate_from_input] Options count: {len(normalized_options)}")
#                     print(f"[generate_from_input] Correct answers: {correct_answers}")
#                     print(f"[generate_from_input] Generation session ID: {generation_session.id}")
                    
#                     try:
#                         # Extract overall explanation from multiple possible field names (try all variations)
#                         # Handle case where value might be dict, string, or other type
#                         explanation = ''
#                         overall_exp_candidates = [
#                             q_data.get('Overall Explanation'),
#                             q_data.get('overall_explanation'),
#                             q_data.get('Overall_Explanation'),
#                             q_data.get('explanation_text'),
#                             q_data.get('rationale'),
#                             q_data.get('reason'),
#                             q_data.get('explanation')  # Check this last as it might be the dict
#                         ]
                        
#                         for candidate in overall_exp_candidates:
#                             if candidate:
#                                 # If it's a string, use it
#                                 if isinstance(candidate, str) and candidate.strip():
#                                     explanation = candidate.strip()
#                                     break
#                                 # If it's a dict, skip (that's the option explanations dict)
#                                 elif isinstance(candidate, dict):
#                                     continue
#                                 # Otherwise, try to convert to string
#                                 else:
#                                     candidate_str = str(candidate).strip()
#                                     if candidate_str and len(candidate_str) > 10:
#                                         explanation = candidate_str
#                                         break
                        
#                         if explanation:
#                             print(f"[generate_from_input] ✅ Overall explanation extracted: {explanation[:100]}...")
#                         else:
#                             print(f"[generate_from_input] ⚠️ No overall explanation found in q_data")
#                             # Debug: show available keys that might contain explanation
#                             possible_keys = [k for k in q_data.keys() if any(word in k.lower() for word in ['explain', 'rationale', 'reason', 'summary', 'overall'])]
#                             if possible_keys:
#                                 print(f"[generate_from_input] Possible explanation keys found: {possible_keys}")
#                             # Try to get from any key containing 'overall' and 'explanation' (case-insensitive)
#                             for key in q_data.keys():
#                                 key_lower = key.lower()
#                                 if 'overall' in key_lower and 'explanation' in key_lower:
#                                     candidate = q_data.get(key)
#                                     if candidate and isinstance(candidate, str):
#                                         potential_exp = candidate.strip()
#                                         if potential_exp and len(potential_exp) > 10:
#                                             explanation = potential_exp
#                                             print(f"[generate_from_input] ✅ Found overall explanation in key '{key}': {explanation[:100]}...")
#                                             break
                   
#                         new_question = CraftsmanQuestion(
#                             course=default_course,
#                             parsing_session=generation_session,  # Link to generation session
#                             question_text=question_text,
#                             question_type=question_type,
#                             options=normalized_options,
#                             correct_answers=correct_answers,
#                             explanation=explanation,
#                             status=question_status,  # 'generated' if valid, 'manual_review' if validation fails
#                             tags=final_tags  # Always populate tags (from AI or source question)
#                         )
#                         new_question.save()
#                         saved_count += 1
#                         print(f"[generate_from_input] ✅ Successfully generated and saved question {saved_count} from input question {idx}")
#                         print(f"[generate_from_input] Saved question - ID: {new_question.id}, Status: {question_status}")
#                         print(f"[generate_from_input] Question session ID: {new_question.parsing_session.id if new_question.parsing_session else 'None'}, Expected: {generation_session.id}")
                        
#                         # Verify the question was saved with the correct session
#                         if new_question.parsing_session and str(new_question.parsing_session.id) != str(generation_session.id):
#                             print(f"[generate_from_input] ERROR: Question saved with wrong session! Expected {generation_session.id}, got {new_question.parsing_session.id}")
#                     except Exception as save_error:
#                         error_msg = f"Error saving question {idx} to database: {str(save_error)}"
#                         errors.append(error_msg)
#                         print(f"[generate_from_input] ❌ {error_msg}")
#                         import traceback
#                         print(f"[generate_from_input] Save error traceback: {traceback.format_exc()}")
#                         continue

#                 except Exception as e:
#                     import traceback
#                     error_msg = f"Error generating question from input question {idx}: {str(e)}"
#                     errors.append(error_msg)
#                     print(f"[generate_from_input] ❌ {error_msg}")
#                     print(f"[generate_from_input] Traceback: {traceback.format_exc()}")
#                     print(f"[generate_from_input] ========================================")
#                     continue
            
#             print(f"[generate_from_input] Completed processing input question {idx}/{total_input_questions}. Generated {saved_count} question(s) so far.")
#             print(f"[generate_from_input] ========================================")

#         # Update generation session with statistics
#         # Use ObjectId for filtering to ensure correct matching
#         session_obj_id = ObjectId(str(generation_session.id))
#         session_questions = CraftsmanQuestion.objects(
#             parsing_session=session_obj_id)
#         input_count = session_questions.filter(status='input').count()
#         # Count all generated questions (both validated and not validated)
#         generated_count = session_questions.filter(status__in=['generated', 'manual_review']).count()
#         total_count = session_questions.count()
#         print(f"[generate_from_input] Session statistics for session {generation_session.id}:")
#         print(f"[generate_from_input]   - Input questions: {input_count}")
#         print(f"[generate_from_input]   - Generated questions (all): {generated_count}")
#         print(f"[generate_from_input]   - Total questions: {total_count}")
#         print(f"[generate_from_input]   - Questions saved in this run: {saved_count}")

#         generation_session.total_questions = total_count
#         generation_session.input_questions_count = input_count
#         generation_session.generated_questions_count = generated_count
#         generation_session.status = 'completed' if saved_count > 0 else 'failed'
#         # Append errors to existing errors if reusing session
#         if hasattr(generation_session, 'errors') and generation_session.errors:
#             generation_session.errors.extend(errors)
#         else:
#             generation_session.errors = errors
#         generation_session.completed_at = datetime.datetime.utcnow()
#         generation_session.save()
#         print(
#             f"[generate_from_input] Updated generation session {generation_session.id}: {saved_count} new questions saved, total: {total_count}")
#         print(f"[generate_from_input] Generation complete: Processed {total_input_questions} input question(s), generated {saved_count} new question(s)")
        
#         if saved_count < total_input_questions:
#             print(f"[generate_from_input] WARNING: Only generated {saved_count} question(s) from {total_input_questions} input question(s). Some questions may have failed generation.")
#             if errors:
#                 print(f"[generate_from_input] Errors encountered: {len(errors)} error(s)")
#                 for error in errors[:10]:  # Print first 10 errors
#                     print(f"[generate_from_input]   - {error}")

#         # Note: CraftsmanQuestions are stored separately, so we don't update course.questions count
#         # If you want to track craftsman questions separately, consider adding a craftsman_questions field to Course

#         # Get all generated questions for this session to include in response
#         # This matches what's shown in the Generated Questions tab
#         session_obj_id = ObjectId(str(generation_session.id))
#         all_generated_questions = CraftsmanQuestion.objects(
#             parsing_session=session_obj_id,
#             status__in=['generated', 'manual_review']
#         ).order_by('-created_at')

#         # Serialize the generated questions
#         questions_data = []
#         if all_generated_questions:
#             serializer = QuestionSerializer(list(all_generated_questions), many=True)
#             questions_data = serializer.data
#             print(f"[generate_from_input] Including {len(questions_data)} generated questions in response")

#         return JsonResponse({
#             "success": True,
#             "message": f"Successfully generated {saved_count} new question(s) from {total_input_questions} input question(s)",

#             # Counts
#             "saved_count": saved_count,
#             "total_input_questions": total_input_questions,

#             # Errors
#             "errors": errors,

#             # Session
#             "session_id": str(generation_session.id),

#             # Generated questions data (matches what's shown in Generated Questions tab)
#             "questions": questions_data

#         })

#     except Exception as e:
#         import traceback
#         error_msg = str(e)
#         print(f"[generate_from_input] Error: {error_msg}")
#         print(traceback.format_exc())
#         return JsonResponse({"success": False, "error": error_msg}, status=500)


# # ✅ Update parsed question (Admin)
# @api_view(['PUT'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def update_parsed_question(request, question_id):
#     """Admin: Update a CraftsmanQuestion"""
#     try:
#         if not ObjectId.is_valid(question_id):
#             return Response({"success": False, "error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST)

#         question = CraftsmanQuestion.objects.get(id=ObjectId(question_id))
#         data = request.data
#         print("data : ",data)
        
#         # Track original status - if it's a generated question (validated or not), keep it visible
#         # Manual review queue shows all generated questions (both 'generated' and 'manual_review')
#         original_status = question.status
#         is_generated_question = original_status in ['generated', 'manual_review']
#         print("is_generated_question : ",is_generated_question)
#         print 

#         # Update fields with validation
#         if 'question_text' in data:
#             question_text = data['question_text']
#             if not question_text or not str(question_text).strip():
#                 return Response({"success": False, "error": "Question text cannot be empty"}, status=status.HTTP_400_BAD_REQUEST)
#             question.question_text = str(question_text).strip()
        
#         if 'question_type' in data:
#             question_type = data['question_type']
#             # Normalize question type format
#             if question_type in ['single', 'single-correct']:
#                 question.question_type = 'single'
#             elif question_type in ['multiple', 'multi-correct']:
#                 question.question_type = 'multiple'
#             else:
#                 question.question_type = question_type
        
#         if 'options' in data:
#             options = data['options']
#             if not isinstance(options, list):
#                 return Response({"success": False, "error": "Options must be a list"}, status=status.HTTP_400_BAD_REQUEST)
#             if len(options) < 2:
#                 return Response({"success": False, "error": "At least 2 options are required"}, status=status.HTTP_400_BAD_REQUEST)
#             question.options = options
        
#         if 'correct_answers' in data:
#             correct_answers = data['correct_answers']
#             if not isinstance(correct_answers, list):
#                 correct_answers = [correct_answers] if correct_answers else []
#             if len(correct_answers) == 0:
#                 return Response({"success": False, "error": "At least one correct answer is required"}, status=status.HTTP_400_BAD_REQUEST)
#             question.correct_answers = correct_answers
        
#         if 'explanation' in data:
#             question.explanation = str(data.get('explanation', '')).strip()
        
#         if 'status' in data:
#             print(data['status'],"stas")
#             # status field for craftsman questions
#             new_status = data['status']
#             # If question is a generated question (validated or not validated), 
#             # keep it in one of the generated statuses to ensure it remains visible
#             # in manual review queue after manual correction
#             # if is_generated_question:
#             #     # Keep in original status (either 'generated' or 'manual_review')
#             #     # This ensures manually corrected questions remain visible
#             #     question.status = original_status
#             # else:
#             #     # If it wasn't a generated question, use the provided status

#              # Map frontend statuses to backend allowed statuses
#             status_mapping = {
#                 'needs_review': 'manual_review',
#                 'pending': 'pending',
#                 'approved': 'approved',
#                 'rejected': 'rejected'
#             }
#             mapped_status = status_mapping.get(new_status)
#             if not mapped_status:
#                 # If frontend sent invalid status, keep original
#                 mapped_status = original_status
#             question.status = mapped_status
#         elif is_generated_question:
#             # If no status provided but question is a generated question, keep original status
#             question.status = original_status
        
#         if 'tags' in data:
#             tags = data['tags']
#             if isinstance(tags, str):
#                 tags = [t.strip() for t in tags.split(',') if t.strip()]
#             elif not isinstance(tags, list):
#                 tags = []
#             question.tags = tags

#         question.updated_at = datetime.datetime.utcnow()
#         question.save()

#         serializer = QuestionSerializer(question)
#         return Response({
#             "success": True,
#             "message": "Question updated successfully",
#             "data": serializer.data
#         })
#     except CraftsmanQuestion.DoesNotExist:
#         return Response({"success": False, "error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         print(e,"error")
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Delete parsed question (Admin)
# @api_view(['DELETE'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def delete_parsed_question(request, question_id):
#     """Admin: Delete a CraftsmanQuestion"""
#     try:
#         if not ObjectId.is_valid(question_id):
#             return Response({"success": False, "error": "Invalid question ID"}, status=status.HTTP_400_BAD_REQUEST)

#         question = CraftsmanQuestion.objects.get(id=ObjectId(question_id))
#         question.delete()

#         return Response({
#             "success": True,
#             "message": "Question deleted successfully"
#         })
#     except CraftsmanQuestion.DoesNotExist:
#         return Response({"success": False, "error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Bulk delete parsed questions (Admin)
# @api_view(['POST'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def bulk_delete_parsed_questions(request):
#     """Admin: Delete multiple CraftsmanQuestions"""
#     try:
#         question_ids = request.data.get('question_ids', [])

#         if not question_ids:
#             return Response({"success": False, "error": "No question IDs provided"}, status=status.HTTP_400_BAD_REQUEST)

#         deleted_count = 0

#         for qid in question_ids:
#             if ObjectId.is_valid(qid):
#                 try:
#                     question = CraftsmanQuestion.objects.get(id=ObjectId(qid))
#                     question.delete()
#                     deleted_count += 1
#                 except CraftsmanQuestion.DoesNotExist:
#                     continue

#         return Response({
#             "success": True,
#             "message": f"{deleted_count} questions deleted successfully",
#             "deleted_count": deleted_count
#         })
#     except Exception as e:
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get parsing sessions history (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def get_parsing_sessions(request):
#     """Admin: Get all parsing/generation sessions (history)"""
#     try:
#         # Get all sessions ordered by most recent first
#         sessions = ParsingSession.objects.all().order_by('-created_at')

#         sessions_data = []
#         for session in sessions:
#             sessions_data.append({
#                 'id': str(session.id),
#                 'session_name': session.session_name,
#                 'session_type': session.session_type,
#                 'document_name': session.document_name or '',
#                 'document_type': session.document_type or '',
#                 'total_questions': session.total_questions,
#                 'input_questions_count': session.input_questions_count,
#                 'generated_questions_count': session.generated_questions_count,
#                 'status': session.status,
#                 'model_used': session.model_used or '',
#                 'created_at': session.created_at.isoformat() if session.created_at else None,
#                 'completed_at': session.completed_at.isoformat() if session.completed_at else None,
#                 'errors_count': len(session.errors) if session.errors else 0
#             })

#         return Response({
#             "success": True,
#             "sessions": sessions_data,
#             "total": len(sessions_data)
#         })
#     except Exception as e:
#         print(f"[get_parsing_sessions] Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get questions by session (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def get_questions_by_session(request, session_id):
#     """Admin: Get all questions (input and generated) for a specific session"""
#     try:
#         if not ObjectId.is_valid(session_id):
#             return Response({"success": False, "error": "Invalid session ID"}, status=status.HTTP_400_BAD_REQUEST)

#         # Get session
#         try:
#             session = ParsingSession.objects.get(id=ObjectId(session_id))
#         except ParsingSession.DoesNotExist:
#             return Response({"success": False, "error": "Session not found"}, status=status.HTTP_404_NOT_FOUND)

#         # Get all questions for this session
#         questions = CraftsmanQuestion.objects(
#             parsing_session=session).order_by('status', '-created_at')

#         # Separate by status
#         input_questions = [q for q in questions if q.status == 'input']
#         generated_questions = [q for q in questions if q.status == 'generated']
#         manual_review_questions = [
#             q for q in questions if q.status == 'manual_review']

#         # Serialize questions
#         serializer = QuestionSerializer(questions, many=True)

#         # Session details
#         session_data = {
#             'id': str(session.id),
#             'session_name': session.session_name,
#             'session_type': session.session_type,
#             'document_name': session.document_name or '',
#             'document_type': session.document_type or '',
#             'total_questions': session.total_questions,
#             'input_questions_count': session.input_questions_count,
#             'generated_questions_count': session.generated_questions_count,
#             'status': session.status,
#             'model_used': session.model_used or '',
#             'created_at': session.created_at.isoformat() if session.created_at else None,
#             'completed_at': session.completed_at.isoformat() if session.completed_at else None,
#             'errors': session.errors or []
#         }

#         return Response({
#             "success": True,
#             "session": session_data,
#             "questions": serializer.data,
#             "input_questions": QuestionSerializer(input_questions, many=True).data,
#             "generated_questions": QuestionSerializer(generated_questions, many=True).data,
#             "manual_review_questions": QuestionSerializer(manual_review_questions, many=True).data,
#             "total_questions": len(questions)
#         })
#     except Exception as e:
#         print(f"[get_questions_by_session] Error: {str(e)}")
#         import traceback
#         print(traceback.format_exc())
#         return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

