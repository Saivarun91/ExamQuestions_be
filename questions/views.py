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
            # Try to find by ObjectId first
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
                # Try by index (1-based)
                print(f"[get_test_questions] test_id is not ObjectId, trying as index...")
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
        except (PracticeTest.DoesNotExist, ValueError, TypeError) as e:
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
        # Get course_id from different sources  
        course_id = request.POST.get('course_id')
        csv_file = request.FILES.get('file') or request.FILES.get('csv_file')
        
        print(f"📝 Upload CSV Request")
        print(f"   Content-Type: {request.content_type}")
        print(f"   course_id: {course_id}")
        print(f"   file: {csv_file}")
        print(f"   POST data: {request.POST.keys()}")
        print(f"   FILES: {request.FILES.keys()}")
        
        if not course_id:
            return JsonResponse({"error": "Course ID is required", "success": False}, status=400)
        
        if not ObjectId.is_valid(course_id):
            return JsonResponse({"error": "Invalid course ID format", "success": False}, status=400)
        
        if not csv_file:
            return JsonResponse({"error": "No file provided", "success": False}, status=400)
        
        # Get course
        try:
            course = Course.objects.get(id=ObjectId(course_id))
            print(f"✅ Found course: {course.title}")
        except Course.DoesNotExist:
            return JsonResponse({"error": "Course not found", "success": False}, status=404)
        
        # Read CSV file
        try:
            decoded_file = csv_file.read().decode('utf-8')
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
            print(f"✅ CSV file decoded successfully")
        except Exception as e:
            print(f"❌ Error decoding CSV: {str(e)}")
            return JsonResponse({"error": f"Error reading CSV file: {str(e)}", "success": False}, status=400)
        
        created_count = 0
        errors = []
        
        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # Parse options (expecting JSON string or pipe-separated)
                options_str = row.get('options', '')
                if not options_str:
                    errors.append(f"Row {row_num}: No options provided")
                    continue
                    
                if options_str.startswith('['):
                    import json
                    options = json.loads(options_str)
                else:
                    # Pipe-separated format: "Option A|Option B|Option C"
                    options = [{'text': opt.strip()} for opt in options_str.split('|') if opt.strip()]
                
                # Parse correct answers (comma-separated or pipe-separated)
                correct_answers_str = row.get('correct_answers', '')
                if not correct_answers_str:
                    errors.append(f"Row {row_num}: No correct answers provided")
                    continue
                    
                # Handle both comma and pipe separators
                if '|' in correct_answers_str:
                    correct_answers = [ans.strip() for ans in correct_answers_str.split('|') if ans.strip()]
                else:
                    correct_answers = [ans.strip() for ans in correct_answers_str.split(',') if ans.strip()]
                
                question_text = row.get('question_text', '').strip()
                if not question_text:
                    errors.append(f"Row {row_num}: No question text provided")
                    continue
                
                # Create question
                question = Question(
                    course=course,
                    question_text=question_text,
                    question_type=row.get('question_type', 'single').strip().lower(),
                    options=options,
                    correct_answers=correct_answers,
                    explanation=row.get('explanation', '').strip(),
                    question_image=row.get('question_image', None) if row.get('question_image', '').strip() else None,
                    marks=int(row.get('marks', 1)) if row.get('marks', '').strip() else 1,
                    tags=[tag.strip() for tag in row.get('tags', '').split(',') if tag.strip()] if row.get('tags', '').strip() else []
                )
                question.save()
                created_count += 1
                print(f"✅ Created question {created_count}: {question_text[:50]}...")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                import traceback
                traceback.print_exc()
        
        print(f"✅ Upload complete: {created_count} questions created, {len(errors)} errors")
        
        # ✅ AUTO-SYNC: Update course's questions count
        question_count = Question.objects(course=course).count()
        course.questions = question_count
        course.save()
        print(f"✅ Updated course questions count: {question_count}")
        
        return JsonResponse({
            "success": True,
            "message": f"{created_count} questions uploaded successfully",
            "created_count": created_count,
            "errors": errors if errors else None
        })
        
    except Exception as e:
        print(f"❌ Unexpected error in upload_questions_csv: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "error": str(e),
            "success": False
        }, status=500)


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

