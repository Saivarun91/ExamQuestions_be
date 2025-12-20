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
from .serializers import QuestionSerializer
from common.middleware import authenticate, restrict
import csv
import io
import datetime
import json


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
        print(f"[get_test_questions] Looking for test_id: {test_id}, course_id: {course_id}")
        
        try:
            # Try to find by slug first (SEO-friendly)
            current_test = PracticeTest.objects(slug=test_id, course=course).first()
            if current_test:
                print(f"[get_test_questions] Found test by slug: {current_test.title}")
            else:
                # Try by ObjectId
                if ObjectId.is_valid(test_id):
                    print(f"[get_test_questions] test_id is valid ObjectId, searching...")
                    try:
                        current_test = PracticeTest.objects.get(id=ObjectId(test_id), course=course)
                        print(f"[get_test_questions] Found test by ObjectId: {current_test.title}")
                    except PracticeTest.DoesNotExist:
                        # Try without course filter in case course reference is wrong
                        try:
                            current_test = PracticeTest.objects.get(id=ObjectId(test_id))
                            print(f"[get_test_questions] Found test by ObjectId (without course filter): {current_test.title}")
                            # Verify it belongs to the course
                            if str(current_test.course.id) != str(course.id):
                                print(f"[get_test_questions] Warning: Test belongs to different course")
                                current_test = None
                        except PracticeTest.DoesNotExist:
                            print(f"[get_test_questions] Test with ObjectId {test_id} not found")
                            current_test = None
                else:
                    # Try by index (1-based) for backward compatibility
                    try:
                        print(f"[get_test_questions] test_id is not ObjectId or slug, trying as index...")
                        test_index = int(test_id) - 1
                        practice_tests = list(course.practice_tests) if course.practice_tests else []
                        print(f"[get_test_questions] Course has {len(practice_tests)} practice tests in reference list")
                        
                        if test_index >= 0 and test_index < len(practice_tests):
                            current_test = practice_tests[test_index]
                            print(f"[get_test_questions] Found test by index from reference list: {current_test.title}")
                        else:
                            # Fallback: query directly from database
                            all_tests = list(PracticeTest.objects(course=course).order_by('created_at'))
                            print(f"[get_test_questions] Found {len(all_tests)} tests in database for course")
                            if test_index >= 0 and test_index < len(all_tests):
                                current_test = all_tests[test_index]
                                print(f"[get_test_questions] Found test by index from database: {current_test.title}")
                    except (ValueError, TypeError):
                        print(f"[get_test_questions] test_id is not a valid index, slug, or ObjectId")
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
            exam_questions = ExamQuestion.objects(category=current_test).order_by('created_at')
            if exam_questions.count() > 0:
                # Use questions from exams app (linked to PracticeTest)
                questions = exam_questions
                print(f"[get_test_questions] Found {exam_questions.count()} questions linked to PracticeTest")
        except Exception as e:
            print(f"[get_test_questions] No questions in exams app, using questions app: {e}")
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
        
        print(f"[get_test_questions] Returning {len(questions_list)} questions for test {current_test.id}")
        
        # Check if we have any questions
        if len(questions_list) == 0:
            print(f"[get_test_questions] No questions found for course {course.id}")
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
                            processed_options.append(opt)
                        elif isinstance(opt, str):
                            processed_options.append({'text': opt})
                        else:
                            processed_options.append({'text': str(opt)})
                elif isinstance(q.options, str):
                    try:
                        options_data = json.loads(q.options)
                        processed_options = options_data if isinstance(options_data, list) else []
                    except:
                        processed_options = [{'text': q.options}]
            
            # Handle question_image - could be string URL or FileField
            question_image = None
            if hasattr(q, 'question_image') and q.question_image:
                if hasattr(q.question_image, 'url'):
                    question_image = q.question_image.url
                elif isinstance(q.question_image, str):
                    question_image = q.question_image
                else:
                    question_image = str(q.question_image)
            
            questions_data.append({
                'id': str(q.id),
                '_id': str(q.id),  # For compatibility
                'question_text': getattr(q, 'question_text', '') or '',
                'question_type': getattr(q, 'question_type', 'single'),  # Default to 'single' for questions app
                'options': processed_options,
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
        
        # ✅ AUTO-SYNC: Update course's questions count
        question_count = Question.objects(course=course).count()
        course.questions = question_count
        course.save()
        
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
        
        # ✅ AUTO-SYNC: Update course's questions count
        if question.course:
            question_count = Question.objects(course=question.course).count()
            question.course.questions = question_count
            question.course.save()
        
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
        
        # ✅ AUTO-SYNC: Update course's questions count
        if course:
            question_count = Question.objects(course=course).count()
            course.questions = question_count
            course.save()
        
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
        
        # ✅ AUTO-SYNC: Update questions count for all affected courses
        for course in courses_to_update:
            question_count = Question.objects(course=course).count()
            course.questions = question_count
            course.save()
        
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
                    opt = get_row_value(row, [f'answer option {letter}', f'option {letter}'])
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
                        mapped_correct.append(option_texts[option_letters.index(ans)])
                    else:
                        for opt in option_texts:
                            if opt.lower() == ans.lower():
                                mapped_correct.append(opt)
                                break

                if not mapped_correct:
                    errors.append(f"Row {row_num}: Correct answers do not match options")
                    continue

                correct_answers = mapped_correct

                # ----------------------------
                # 🧠 AUTO-DETECT QUESTION TYPE
                # ----------------------------
                csv_type = get_row_value(
                    row, ['question type', 'type']
                )
                csv_type = str(csv_type).strip().lower() if csv_type else 'auto'

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
                    raise ValueError("Single choice must have exactly 1 correct answer")

                if question_type == 'multiple' and correct_count < 2:
                    raise ValueError("Multiple choice must have 2+ correct answers")

                explanation = str(
                    get_row_value(row, ['overall explanation', 'explanation']) or ''
                ).strip()

                tags_raw = get_row_value(row, ['domain', 'tags'])
                tags = [t.strip() for t in tags_raw.split(',')] if tags_raw else []

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

        course.questions = Question.objects(course=course).count()
        course.save()

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

