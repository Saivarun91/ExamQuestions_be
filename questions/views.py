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
        
        # Read CSV file with multiple encoding support
        csv_file.seek(0)  # Reset file pointer
        file_content = csv_file.read()
        decoded_file = None
        
        # Try multiple encodings in order of preference
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'windows-1252']
        
        for encoding in encodings:
            try:
                decoded_file = file_content.decode(encoding)
                print(f"✅ CSV file decoded successfully with encoding: {encoding}")
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        if decoded_file is None:
            print(f"❌ Error decoding CSV: Could not decode with any supported encoding")
            return JsonResponse({"error": "Error reading CSV file: Could not decode file. Please ensure the file is saved as UTF-8, Latin-1, or Windows-1252 encoding.", "success": False}, status=400)
        
        try:
            csv_reader = csv.DictReader(io.StringIO(decoded_file))
        except Exception as e:
            print(f"❌ Error parsing CSV: {str(e)}")
            return JsonResponse({"error": f"Error parsing CSV file: {str(e)}", "success": False}, status=400)
        
        # Print CSV headers for debugging
        if csv_reader.fieldnames:
            # Normalize header names (strip whitespace)
            normalized_headers = [h.strip() if h else h for h in csv_reader.fieldnames]
            print(f"📋 CSV Headers: {normalized_headers}")
        else:
            print(f"⚠️ Warning: No headers found in CSV file")
            return JsonResponse({"error": "CSV file has no headers. Please ensure the first row contains column names.", "success": False}, status=400)
        
        created_count = 0
        errors = []
        row_count = 0
        
        # Normalize column names (case-insensitive, strip whitespace)
        def get_row_value(row, possible_keys):
            """Get value from row using multiple possible column name variations"""
            # First, normalize all row keys (strip whitespace)
            normalized_row = {k.strip() if k else k: v for k, v in row.items()}
            
            for key in possible_keys:
                key_normalized = key.strip().lower()
                # Try exact match (case-insensitive, whitespace-insensitive)
                for row_key, row_value in normalized_row.items():
                    if row_key and row_key.strip().lower() == key_normalized:
                        return row_value
            return None
        
        for row_num, row in enumerate(csv_reader, start=2):
            row_count += 1
            try:
                # Skip empty rows
                if not row or all(not str(v).strip() if v else True for v in row.values()):
                    continue
                
                # Debug: Print first few rows to see structure
                if row_num <= 3:
                    print(f"📝 Row {row_num} data: {dict(row)}")
                    print(f"   Row keys: {list(row.keys())}")
                
                # Parse options - handle two formats:
                # 1. Single column with pipe/comma-separated values: "Option A|Option B|Option C"
                # 2. Separate columns: "Answer Option A", "Answer Option B", etc.
                options = []
                options_str = get_row_value(row, ['options', 'option', 'Options', 'Option']) or ''
                
                if options_str and str(options_str).strip():
                    # Format 1: Single column with options
                    options_str = str(options_str).strip()
                    if options_str.startswith('['):
                        import json
                        options = json.loads(options_str)
                    else:
                        # Pipe-separated or semicolon-separated format
                        if '|' in options_str:
                            options = [{'text': opt.strip()} for opt in options_str.split('|') if opt.strip()]
                        elif ';' in options_str:
                            options = [{'text': opt.strip()} for opt in options_str.split(';') if opt.strip()]
                        else:
                            # Try comma-separated as fallback
                            options = [{'text': opt.strip()} for opt in options_str.split(',') if opt.strip()]
                else:
                    # Format 2: Separate columns for each option (Answer Option A, B, C, D, E)
                    option_columns = [
                        ['Answer Option A', 'answer option a', 'option a', 'Option A'],
                        ['Answer Option B', 'answer option b', 'option b', 'Option B'],
                        ['Answer Option C', 'answer option c', 'option c', 'Option C'],
                        ['Answer Option D', 'answer option d', 'option d', 'Option D'],
                        ['Answer Option E', 'answer option e', 'option e', 'Option E']
                    ]
                    
                    explanation_columns = [
                        ['Explanation A', 'explanation a'],
                        ['Explanation B', 'explanation b'],
                        ['Explanation C', 'explanation c'],
                        ['Explanation D', 'explanation d'],
                        ['Explanation E', 'explanation e']
                    ]
                    
                    for i, option_cols in enumerate(option_columns):
                        option_text = get_row_value(row, option_cols) or ''
                        if option_text and str(option_text).strip():
                            option_data = {'text': str(option_text).strip()}
                            # Try to get corresponding explanation
                            if i < len(explanation_columns):
                                explanation_text = get_row_value(row, explanation_columns[i]) or ''
                                if explanation_text and str(explanation_text).strip():
                                    option_data['explanation'] = str(explanation_text).strip()
                            options.append(option_data)
                
                if not options:
                    error_detail = f"Row {row_num}: No options provided. Available columns: {list(row.keys())}"
                    errors.append(error_detail)
                    if row_num <= 3:
                        print(f"   ⚠️  {error_detail}")
                    continue
                
                # Parse correct answers (comma-separated or pipe-separated)
                # Try multiple column name variations
                correct_answers_str = get_row_value(row, ['correct_answers', 'correct_answer', 'correct_ans', 'answer', 'Correct Answers', 'Correct Answer']) or ''
                if not correct_answers_str or not str(correct_answers_str).strip():
                    errors.append(f"Row {row_num}: No correct answers provided. Available columns: {list(row.keys())}")
                    continue
                
                correct_answers_str = str(correct_answers_str).strip()
                # Handle both comma and pipe separators
                if '|' in correct_answers_str:
                    correct_answers = [ans.strip() for ans in correct_answers_str.split('|') if ans.strip()]
                else:
                    # Split by comma, but handle quoted values
                    correct_answers = []
                    # Try to handle comma-separated values, including those with commas inside quotes
                    import re
                    # Split by comma, but preserve quoted strings
                    parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', correct_answers_str)
                    for part in parts:
                        part = part.strip().strip('"').strip("'")
                        if part:
                            correct_answers.append(part)
                    
                    # If regex didn't work well, fall back to simple split
                    if not correct_answers:
                        correct_answers = [ans.strip().strip('"').strip("'") for ans in correct_answers_str.split(',') if ans.strip()]
                
                if not correct_answers:
                    errors.append(f"Row {row_num}: No valid correct answers found after parsing. Value was: '{correct_answers_str}'")
                    if row_num <= 3:
                        print(f"   ⚠️  Row {row_num}: Could not parse correct answers from: '{correct_answers_str}'")
                    continue
                
                # Get question text - try multiple column name variations
                question_text = get_row_value(row, ['question_text', 'question', 'Question Text', 'Question']) or ''
                question_text = str(question_text).strip()
                if not question_text:
                    errors.append(f"Row {row_num}: No question text provided. Available columns: {list(row.keys())}")
                    continue
                
                # Get question type - try multiple column name variations
                question_type_str = get_row_value(row, ['question_type', 'type', 'Question Type', 'Type']) or 'single'
                question_type = str(question_type_str).strip().lower() if question_type_str else 'single'
                # Normalize question type values
                if question_type in ['single', 'single choice', 'single-choice', '1']:
                    question_type = 'single'
                elif question_type in ['multiple', 'multiple choice', 'multiple-choice', 'multi', '2']:
                    question_type = 'multiple'
                else:
                    question_type = 'single'  # Default to single if invalid
                
                # Get explanation - try multiple column name variations (Overall Explanation, Explanation, etc.)
                explanation = get_row_value(row, ['explanation', 'Explanation', 'Overall Explanation', 'overall explanation']) or ''
                explanation = str(explanation).strip() if explanation else ''
                
                # Get question image - try multiple column name variations
                question_image = get_row_value(row, ['question_image', 'image', 'Question Image', 'Image']) or None
                question_image = str(question_image).strip() if question_image and str(question_image).strip() else None
                
                # Get marks - try multiple column name variations
                marks_str = get_row_value(row, ['marks', 'mark', 'Marks', 'Mark']) or '1'
                try:
                    marks = int(str(marks_str).strip()) if marks_str and str(marks_str).strip() else 1
                except (ValueError, TypeError):
                    marks = 1
                
                # Get tags - try multiple column name variations (Domain, Tags, Tag, etc.)
                tags_str = get_row_value(row, ['tags', 'tag', 'Tags', 'Tag', 'Domain', 'domain']) or ''
                if tags_str and str(tags_str).strip():
                    tags = [tag.strip() for tag in str(tags_str).split(',') if tag.strip()]
                else:
                    tags = []
                
                # Validate that correct_answers match options
                # Check if correct answers are valid option texts or option letters (A, B, C, D, E)
                option_texts = [opt.get('text', '').strip() for opt in options if opt.get('text')]
                option_letters = ['A', 'B', 'C', 'D', 'E'][:len(options)]
                
                # Map correct answers - handle both full text and letter format
                mapped_correct_answers = []
                for ans in correct_answers:
                    ans_stripped = ans.strip()
                    # Check if it's a letter (A, B, C, D, E)
                    if ans_stripped.upper() in option_letters:
                        # Map letter to option text
                        letter_index = option_letters.index(ans_stripped.upper())
                        if letter_index < len(option_texts):
                            mapped_correct_answers.append(option_texts[letter_index])
                        else:
                            mapped_correct_answers.append(ans_stripped)  # Keep original if mapping fails
                    # Check if it matches an option text exactly
                    elif ans_stripped in option_texts:
                        mapped_correct_answers.append(ans_stripped)
                    # Try case-insensitive match
                    else:
                        matched = False
                        for opt_text in option_texts:
                            if opt_text.lower() == ans_stripped.lower():
                                mapped_correct_answers.append(opt_text)
                                matched = True
                                break
                        if not matched:
                            # If no match found, keep original and let validation catch it
                            mapped_correct_answers.append(ans_stripped)
                
                # Validate mapped answers
                invalid_answers = [ans for ans in mapped_correct_answers if ans not in option_texts]
                
                if invalid_answers:
                    error_msg = f"Row {row_num}: Correct answers '{', '.join(invalid_answers)}' do not match any options. Available options: {', '.join(option_texts)}"
                    errors.append(error_msg)
                    if row_num <= 3:
                        print(f"   ⚠️  {error_msg}")
                    continue
                
                # Use mapped correct answers
                correct_answers = mapped_correct_answers
                
                # Create question
                question = Question(
                    course=course,
                    question_text=question_text,
                    question_type=question_type,
                    options=options,
                    correct_answers=correct_answers,
                    explanation=explanation,
                    question_image=question_image,
                    marks=marks,
                    tags=tags
                )
                question.save()
                created_count += 1
                print(f"✅ Created question {created_count}: {question_text[:50]}...")
                
            except Exception as e:
                error_msg = f"Row {row_num}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ Row {row_num} error: {str(e)}")
                # Print row data for debugging
                if row_num <= 3:
                    print(f"   Row data: {dict(row)}")
                import traceback
                if row_num <= 3:  # Only print full traceback for first few errors
                    traceback.print_exc()
        
        # Print summary of errors
        if errors:
            print(f"\n📊 Error Summary:")
            print(f"   Total errors: {len(errors)}")
            # Print first 10 errors as examples
            for i, error in enumerate(errors[:10], 1):
                print(f"   {i}. {error}")
            if len(errors) > 10:
                print(f"   ... and {len(errors) - 10} more errors")
        
        print(f"✅ Upload complete: {created_count} questions created, {len(errors)} errors")
        
        # ✅ AUTO-SYNC: Update course's questions count
        question_count = Question.objects(course=course).count()
        course.questions = question_count
        course.save()
        print(f"✅ Updated course questions count: {question_count}")
        
        # Return response with detailed error information
        return JsonResponse({
            "success": True if created_count > 0 else False,
            "message": f"{created_count} questions uploaded successfully" if created_count > 0 else f"No questions were created. {len(errors)} errors found. Please check the CSV format and column names.",
            "created_count": created_count,
            "errors": errors if errors else None,
            "total_rows_processed": row_count if 'row_count' in locals() else 0
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

