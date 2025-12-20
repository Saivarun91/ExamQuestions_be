import json
import io
import csv
import re
import random
import os
from datetime import datetime, timedelta
from bson import ObjectId

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone

from common.middleware import authenticate, restrict
from exams.models import Question
from exams.models import Exam
# from exams.models import TestAttempt
from categories.models import Category 
from users.models import User
from practice_tests.models import PracticeTest
from exams.models import Question, Exam, TestAttempt, QuestionBank
from practice_tests.models import PracticeTest


# -------------------------------
# CREATE QUESTION
# -------------------------------
@csrf_exempt
@authenticate
@restrict(['admin'])
def create_question(request):
    """
    ✅ Create a new question linked to a PracticeTest.
    Supports both JSON and multipart/form-data.
    Required fields:
        category_id, question_type, options, correct_answers
    Question can have either question_text OR question_image (or both).
    Options can have either text OR image_url (or both).
    """
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Check if request is multipart/form-data (file upload) or JSON
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        
        if is_multipart:
            # Handle multipart/form-data (with file uploads)
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
            
            # Parse JSON fields if they are strings
            if 'options' in data and isinstance(data['options'], str):
                try:
                    data['options'] = json.loads(data['options'])
                except:
                    pass
            if 'correct_answers' in data and isinstance(data['correct_answers'], str):
                try:
                    data['correct_answers'] = json.loads(data['correct_answers'])
                except:
                    pass
        else:
            # Handle JSON request
            data = json.loads(request.body.decode('utf-8'))

        # ✅ Required fields check
        required_fields = ["category_id", "question_type", "options", "correct_answers"]
        for field in required_fields:
            if field not in data:
                return JsonResponse({"success": False, "message": f"{field} is required"}, status=400)

        # ✅ Parse options and correct_answers if they are JSON strings
        if isinstance(data['options'], str):
            try:
                data['options'] = json.loads(data['options'])
            except:
                return JsonResponse({"success": False, "message": "Invalid options format"}, status=400)
        if isinstance(data['correct_answers'], str):
            try:
                data['correct_answers'] = json.loads(data['correct_answers'])
            except:
                return JsonResponse({"success": False, "message": "Invalid correct_answers format"}, status=400)

        # ✅ Validate category_id
        category_id = data['category_id']
        if not ObjectId.is_valid(category_id):
            return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

        try:
            category = PracticeTest.objects.get(id=ObjectId(category_id))
        except PracticeTest.DoesNotExist:
            return JsonResponse({"success": False, "message": "PracticeTest not found"}, status=404)

        # ✅ Validate question: must have either text or image (or both)
        question_text = data.get('question_text', '').strip() if data.get('question_text') else ''
        question_image_file = request.FILES.get('question_image') if is_multipart else None
        
        if not question_text and not question_image_file:
            return JsonResponse({
                "success": False, 
                "message": "Either question_text or question_image must be provided"
            }, status=400)

        # ✅ Handle question image upload
        question_image = None
        if question_image_file:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(settings.MEDIA_ROOT, "question_images")
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            filename = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{question_image_file.name}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in question_image_file.chunks():
                    f.write(chunk)
            
            # Store file in GridFS FileField
            question_image = question_image_file

        # ✅ Validate and process options
        options_raw = data['options']
        if not isinstance(options_raw, list) or len(options_raw) < 2:
            return JsonResponse({"success": False, "message": "At least 2 options are required"}, status=400)

        processed_options = []
        option_image_files = {}
        
        # Handle option images if provided
        if is_multipart:
            # Get all option image files (named like option_image_0, option_image_1, etc.)
            for key in request.FILES:
                if key.startswith('option_image_'):
                    try:
                        index = int(key.replace('option_image_', ''))
                        option_image_files[index] = request.FILES[key]
                    except:
                        pass

        # Process each option
        for idx, option in enumerate(options_raw):
            option_dict = {}
            
            # If option is a string, convert to dict format
            if isinstance(option, str):
                option_dict['text'] = option
            elif isinstance(option, dict):
                option_dict = option.copy()
            else:
                return JsonResponse({
                    "success": False, 
                    "message": f"Invalid option format at index {idx}"
                }, status=400)
            
            # Handle option image - can be file upload or direct URL
            if idx in option_image_files:
                option_image_file = option_image_files[idx]
                # Create upload directory if it doesn't exist
                upload_dir = os.path.join(settings.MEDIA_ROOT, "option_images")
                os.makedirs(upload_dir, exist_ok=True)
                
                # Save file
                filename = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{idx}_{option_image_file.name}"
                file_path = os.path.join(upload_dir, filename)
                
                with open(file_path, 'wb') as f:
                    for chunk in option_image_file.chunks():
                        f.write(chunk)
                
                # Store relative path as image_url
                option_dict['image_url'] = f"/media/option_images/{filename}"
            elif 'image_url' in option_dict and option_dict['image_url']:
                # If image_url is provided directly (e.g., Cloudinary URL), keep it as is
                pass
            
            # Validate that option has either text or image
            option_text = option_dict.get('text', '').strip() if option_dict.get('text') else ''
            option_image_url = option_dict.get('image_url', '').strip() if option_dict.get('image_url') else ''
            
            if not option_text and not option_image_url:
                return JsonResponse({
                    "success": False, 
                    "message": f"Option at index {idx} must have either text or image"
                }, status=400)
            
            processed_options.append(option_dict)

        # ✅ Validate correct answers
        correct_answers = data['correct_answers']
        if not isinstance(correct_answers, list) or len(correct_answers) == 0:
            return JsonResponse({"success": False, "message": "At least one correct answer is required"}, status=400)

        # Convert correct answers to option identifiers (index or text)
        # For backward compatibility, support both string matching and index-based
        processed_correct_answers = []
        for ans in correct_answers:
            # If answer is an index (integer or string number)
            if isinstance(ans, int) or (isinstance(ans, str) and ans.isdigit()):
                idx = int(ans)
                if 0 <= idx < len(processed_options):
                    # Use index as identifier
                    processed_correct_answers.append(str(idx))
                else:
                    return JsonResponse({
                        "success": False, 
                        "message": f"Invalid correct answer index: {idx}"
                    }, status=400)
            else:
                # Try to match by text
                found = False
                for idx, opt in enumerate(processed_options):
                    opt_text = opt.get('text', '').strip() if opt.get('text') else ''
                    if opt_text == str(ans).strip():
                        processed_correct_answers.append(str(idx))
                        found = True
                        break
                if not found:
                    # If not found, store as-is (might be an identifier)
                    processed_correct_answers.append(str(ans))

        # ✅ Create and save Question
        question = Question(
            category=category,
            question_text=question_text if question_text else '',
            question_type=data['question_type'],
            options=processed_options,
            correct_answers=processed_correct_answers,
            marks=data.get('marks', 1),
            explanation=data.get('explanation', ''),
            tags=data.get('tags', []),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Save question image if provided
        if question_image:
            question.question_image.put(question_image, content_type=question_image.content_type)
        
        question.save()

        return JsonResponse({
            "success": True,
            "message": "Question created successfully",
            "question_id": str(question.id)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=400)


# -------------------------------
# UPDATE QUESTION
# -------------------------------
@csrf_exempt
@authenticate
@restrict(['admin'])
def update_question(request, question_id):
    """
    ✅ Update an existing question.
    Supports both JSON and multipart/form-data.
    Question can have either question_text OR question_image (or both).
    Options can have either text OR image_url (or both).
    """
    if request.method != 'PUT':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"success": False, "message": "Invalid question ID"}, status=400)

        question = Question.objects.get(id=ObjectId(question_id))
        
        # Check if request is multipart/form-data (file upload) or JSON
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        
        if is_multipart:
            # Handle multipart/form-data (with file uploads)
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
            
            # Parse JSON fields if they are strings
            if 'options' in data and isinstance(data['options'], str):
                try:
                    data['options'] = json.loads(data['options'])
                except:
                    pass
            if 'correct_answers' in data and isinstance(data['correct_answers'], str):
                try:
                    data['correct_answers'] = json.loads(data['correct_answers'])
                except:
                    pass
        else:
            # Handle JSON request
            data = json.loads(request.body.decode('utf-8'))

        # Update question_text if provided
        if 'question_text' in data:
            question.question_text = data['question_text'] if data['question_text'] else ''
        
        # Handle question image upload
        question_image_file = request.FILES.get('question_image') if is_multipart else None
        if question_image_file:
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(settings.MEDIA_ROOT, "question_images")
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            filename = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{question_image_file.name}"
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                for chunk in question_image_file.chunks():
                    f.write(chunk)
            
            # Store file in GridFS FileField
            question.question_image.put(question_image_file, content_type=question_image_file.content_type)
        
        # Validate question: must have either text or image (or both)
        question_text = question.question_text.strip() if question.question_text else ''
        has_question_image = question.question_image is not None
        
        if not question_text and not has_question_image:
            return JsonResponse({
                "success": False, 
                "message": "Either question_text or question_image must be provided"
            }, status=400)

        # Update other fields
        for field in ['question_type', 'marks', 'explanation', 'tags']:
            if field in data:
                setattr(question, field, data[field])

        # Handle options update
        if 'options' in data:
            options_raw = data['options']
            if not isinstance(options_raw, list) or len(options_raw) < 2:
                return JsonResponse({"success": False, "message": "At least 2 options are required"}, status=400)

            processed_options = []
            option_image_files = {}
            
            # Handle option images if provided
            if is_multipart:
                # Get all option image files (named like option_image_0, option_image_1, etc.)
                for key in request.FILES:
                    if key.startswith('option_image_'):
                        try:
                            index = int(key.replace('option_image_', ''))
                            option_image_files[index] = request.FILES[key]
                        except:
                            pass

            # Process each option
            for idx, option in enumerate(options_raw):
                option_dict = {}
                
                # If option is a string, convert to dict format
                if isinstance(option, str):
                    option_dict['text'] = option
                elif isinstance(option, dict):
                    option_dict = option.copy()
                else:
                    return JsonResponse({
                        "success": False, 
                        "message": f"Invalid option format at index {idx}"
                    }, status=400)
                
                # Handle option image - can be file upload or direct URL
                if idx in option_image_files:
                    option_image_file = option_image_files[idx]
                    # Create upload directory if it doesn't exist
                    upload_dir = os.path.join(settings.MEDIA_ROOT, "option_images")
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    # Save file
                    filename = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{idx}_{option_image_file.name}"
                    file_path = os.path.join(upload_dir, filename)
                    
                    with open(file_path, 'wb') as f:
                        for chunk in option_image_file.chunks():
                            f.write(chunk)
                    
                    # Store relative path as image_url
                    option_dict['image_url'] = f"/media/option_images/{filename}"
                elif 'image_url' in option_dict and option_dict['image_url']:
                    # If image_url is provided directly (e.g., Cloudinary URL), keep it as is
                    pass
                
                # Validate that option has either text or image
                option_text = option_dict.get('text', '').strip() if option_dict.get('text') else ''
                option_image_url = option_dict.get('image_url', '').strip() if option_dict.get('image_url') else ''
                
                if not option_text and not option_image_url:
                    return JsonResponse({
                        "success": False, 
                        "message": f"Option at index {idx} must have either text or image"
                    }, status=400)
                
                processed_options.append(option_dict)
            
            question.options = processed_options

        # Handle correct_answers update
        if 'correct_answers' in data:
            correct_answers = data['correct_answers']
            if not isinstance(correct_answers, list) or len(correct_answers) == 0:
                return JsonResponse({"success": False, "message": "At least one correct answer is required"}, status=400)

            # Get current options for validation
            current_options = data.get('options', question.options)
            
            # Convert correct answers to option identifiers
            processed_correct_answers = []
            for ans in correct_answers:
                # If answer is an index (integer or string number)
                if isinstance(ans, int) or (isinstance(ans, str) and ans.isdigit()):
                    idx = int(ans)
                    if 0 <= idx < len(current_options):
                        processed_correct_answers.append(str(idx))
                    else:
                        return JsonResponse({
                            "success": False, 
                            "message": f"Invalid correct answer index: {idx}"
                        }, status=400)
                else:
                    # Try to match by text
                    found = False
                    for idx, opt in enumerate(current_options):
                        opt_text = opt.get('text', '').strip() if isinstance(opt, dict) and opt.get('text') else (str(opt).strip() if isinstance(opt, str) else '')
                        if opt_text == str(ans).strip():
                            processed_correct_answers.append(str(idx))
                            found = True
                            break
                    if not found:
                        processed_correct_answers.append(str(ans))
            
            question.correct_answers = processed_correct_answers

        question.updated_at = datetime.utcnow()
        question.save()
        return JsonResponse({'success': True, 'message': 'Question updated successfully'})

    except Question.DoesNotExist:
        return JsonResponse({"success": False, "message": "Question not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)
    except Exception as e:
        import traceback
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# -------------------------------
# DELETE QUESTION
# -------------------------------
from django.http import JsonResponse
from bson import ObjectId
from django.views.decorators.csrf import csrf_exempt
from users.authentication import authenticate, restrict  # adjust import as per your project
from .models import Question


@csrf_exempt
@authenticate
@restrict(['admin'])
def delete_question(request, question_id):
    """
    Delete a question by its ObjectId.
    Accessible only by admin users.
    """
    if request.method != 'DELETE':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # ✅ Validate ObjectId
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"success": False, "message": "Invalid question ID"}, status=400)

        # ✅ Use _id instead of id
        question = Question.objects(_id=ObjectId(question_id)).first()
        if not question:
            return JsonResponse({"success": False, "message": "Question not found"}, status=404)

        # ✅ Delete question
        question.delete()

        return JsonResponse({"success": True, "message": "Question deleted successfully"}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)



# -------------------------------
# BULK DELETE QUESTIONS
# -------------------------------

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from bson import ObjectId
from .models import Question
from common.middleware import authenticate, restrict  # adjust your actual import paths

from bson import ObjectId
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Question
from common.middleware import authenticate, restrict  # adjust import to your project

@csrf_exempt
@authenticate
@restrict(['admin'])
def bulk_delete_questions(request):
    if request.method != 'DELETE':
        return JsonResponse(
            {"success": False, "message": "Method not allowed"},
            status=405
        )

    try:
        data = json.loads(request.body.decode('utf-8'))
        question_ids = data.get('question_ids', [])

        if not question_ids:
            return JsonResponse(
                {"success": False, "message": "No question IDs provided"},
                status=400
            )

        # ✅ Validate ObjectIds
        valid_ids = []
        for qid in question_ids:
            try:
                valid_ids.append(ObjectId(qid))
            except Exception:
                return JsonResponse(
                    {"success": False, "message": f"Invalid question ID: {qid}"},
                    status=400
                )

        # ✅ Use `pk__in` or `id__in` is wrong for MongoEngine
        # Use filter with id=ObjectId instead
        deleted_result = Question.objects(_id__in=valid_ids).delete()  # ✅ FIXED

        # `.delete()` returns an int in MongoEngine (count of deleted)
        deleted_count = deleted_result if isinstance(deleted_result, int) else deleted_result[0]

        return JsonResponse(
            {"success": True, "message": f"{deleted_count} question(s) deleted successfully"},
            status=200
        )

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)

    except Exception as e:
        print("❌ Bulk delete error:", str(e))
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# -------------------------------
# GET QUESTION IMAGE
# -------------------------------
@csrf_exempt
def get_question_image(request, question_id):
    """Serve question image file."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"success": False, "message": "Invalid question ID"}, status=400)
        
        question = Question.objects.get(id=ObjectId(question_id))
        
        if not question.question_image:
            return JsonResponse({"success": False, "message": "Question image not found"}, status=404)
        
        from django.http import HttpResponse
        image_data = question.question_image.read()
        content_type = getattr(question.question_image, 'content_type', 'image/jpeg')
        response = HttpResponse(image_data, content_type=content_type)
        file_ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
        response['Content-Disposition'] = f'inline; filename="question_{question_id}.{file_ext}"'
        return response
        
    except Question.DoesNotExist:
        return JsonResponse({"success": False, "message": "Question not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# -------------------------------
# GET QUESTION BY ID
# -------------------------------
@csrf_exempt
@authenticate
@restrict(['admin'])
def get_question_by_id(request, question_id):
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(question_id):
            return JsonResponse({"success": False, "message": "Invalid question ID"}, status=400)

        question = Question.objects.get(id=ObjectId(question_id))
        
        # Build question image URL if exists
        question_image_url = None
        if question.question_image:
            question_image_url = request.build_absolute_uri(f"/api/exams/questions/{question_id}/image/")
        
        # Process options - handle both old format (strings) and new format (dicts)
        processed_options = []
        for opt in question.options:
            if isinstance(opt, dict):
                processed_options.append(opt)
            elif isinstance(opt, str):
                # Backward compatibility: convert string to dict
                processed_options.append({'text': opt})
            else:
                processed_options.append({'text': str(opt)})
        
        question_data = {
            'id': str(question.id),
            'category_id': str(question.category.id),
            'category_name': getattr(question.category, 'name', ''),
            'question_text': question.question_text or '',
            'question_image': question_image_url,
            'question_type': question.question_type,
            'options': processed_options,
            'correct_answers': question.correct_answers,
            'marks': question.marks,
            'explanation': question.explanation or '',
            'tags': question.tags or [],
            'created_at': question.created_at.isoformat() if question.created_at else None,
            'updated_at': question.updated_at.isoformat() if question.updated_at else None
        }
        return JsonResponse({"success": True, "question": question_data}, status=200)

    except Question.DoesNotExist:
        return JsonResponse({"success": False, "message": "Question not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# -------------------------------
# GET QUESTIONS (BY CATEGORY)
# -------------------------------
@csrf_exempt
# @authenticate
# @restrict(['admin'])
def get_questions(request):
    """Fetch all questions for a category or test (Admin only)."""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        category_id = request.GET.get('category_id')
        test_id = request.GET.get('test_id')
        id_to_check = test_id or category_id

        if not id_to_check:
            return JsonResponse({"success": False, "message": "category_id (or test_id) is required"}, status=400)

        if not ObjectId.is_valid(id_to_check):
            return JsonResponse({"success": False, "message": "Invalid ID format"}, status=400)

        # Questions are linked to PracticeTest, not TestCategory
        practice_test = None
        try:
            practice_test = PracticeTest.objects.get(id=ObjectId(id_to_check))
        except PracticeTest.DoesNotExist:
            # If not a PracticeTest, we can't get questions since they're linked to PracticeTest
            return JsonResponse({
                "success": False,
                "message": f"No PracticeTest found with ID: {id_to_check}. Questions are linked to PracticeTest."
            }, status=404)

        # Filter questions by PracticeTest
        all_questions = list(Question.objects.filter(category=practice_test))
        
        # Limit questions to the test's question count (if specified)
        # If test has 20 questions but CSV has 50, only show 20 questions
        question_limit = practice_test.questions if practice_test.questions > 0 else len(all_questions)
        
        # Shuffle questions randomly so different sets are shown
        import random
        random.shuffle(all_questions)
        
        # Take only the limited number of questions
        questions = all_questions[:question_limit]

        question_list = []
        for q in questions:
            # Build question image URL if exists
            question_image_url = None
            if q.question_image:
                question_image_url = request.build_absolute_uri(f"/api/exams/questions/{q.id}/image/")
            
            # Process options - handle both old format (strings) and new format (dicts)
            processed_options = []
            for opt in q.options:
                if isinstance(opt, dict):
                    processed_options.append(opt)
                elif isinstance(opt, str):
                    # Backward compatibility: convert string to dict
                    processed_options.append({'text': opt})
                else:
                    processed_options.append({'text': str(opt)})
            
            question_list.append({
                'id': str(q.id),
                'question_text': q.question_text or '',
                'question_image': question_image_url,
                'question_type': q.question_type,
                'options': processed_options,
                'correct_answers': q.correct_answers,
                'marks': getattr(q, 'marks', 1),
                'category_id': str(q.category.id) if getattr(q, 'category', None) else None,
                'category_name': getattr(q.category, 'name', ''),
                'explanation': getattr(q, 'explanation', '') or '',
                'tags': getattr(q, 'tags', []) or [],
                'created_at': q.created_at.isoformat() if getattr(q, 'created_at', None) else ''
            })

        return JsonResponse({"success": True, "questions": question_list}, status=200)

    except Exception as e:
        print("❌ ERROR in get_questions:", e)
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# -------------------------------
# UPLOAD QUESTIONS CSV
# -------------------------------

# @csrf_exempt
# @authenticate
# # @restrict(['admin'])
# def upload_questions_csv(request):
#     print(request.method)
#     """
#     Upload questions in bulk via CSV (Admin only).
#     """
#     if request.method != 'POST':
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         csv_file = request.FILES.get('csv_file')
#         category_id = request.POST.get('category_id')

#         if not csv_file or not category_id:
#             return JsonResponse(
#                 {"success": False, "message": "CSV file and category_id are required"},
#                 status=400
#             )

#         if not ObjectId.is_valid(category_id):
#             return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

#         try:
#             category = PracticeTest.objects.get(id=ObjectId(category_id))
#         except PracticeTest.DoesNotExist:
#             return JsonResponse({"success": False, "message": "PracticeTest not found"}, status=404)

#         csv_data = csv_file.read().decode('utf-8')
#         csv_reader = csv.DictReader(io.StringIO(csv_data))

#         questions_created = 0
#         errors = []

#         for row_num, row in enumerate(csv_reader, 1):
#             try:
#                 row = {k.strip(): v.strip() for k, v in row.items() if k and v}
#                 options = [opt.strip() for opt in row['options'].split('|') if opt.strip()]
#                 correct_answers = [
#                     x.strip() for x in re.split(r'[|,]', row['correct_answers']) if x.strip()
#                 ]

#                 Question.objects.create(
#                     category=category,
#                     question_text=row['question_text'],
#                     question_type=row['question_type'],
#                     options=options,
#                     correct_answers=correct_answers,
#                     marks=int(row.get('marks', 1)),
#                     explanation=row.get('explanation', ''),
#                 )
#                 questions_created += 1

#             except Exception as e:
#                 errors.append(f"Row {row_num} Error: {str(e)}")
#                 continue

#         return JsonResponse({
#             'success': True if questions_created > 0 else False,
#             'message': f'{questions_created} question(s) created, {len(errors)} error(s)',
#             'errors': errors
#         })

#     except Exception as e:
#         return JsonResponse({'success': False, 'message': str(e)}, status=400)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.utils import timezone
from django.conf import settings
from bson import ObjectId
import os, csv, io, re

from users.authentication import authenticate
from categories.models import Category
from exams.models import Question, CSVFile
from practice_tests.models import PracticeTest


# Directory where CSV files are stored
UPLOAD_DIR = os.path.join(settings.MEDIA_ROOT, "csv_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ✅ UPLOAD CSV (Admin Only)
@csrf_exempt
# @authenticate
@api_view(["POST"])
def upload_questions_csv(request):
    """
    Upload a CSV file, save it on disk, create a CSVFile record,
    and insert questions into the database.
    """
    try:
        csv_file = request.FILES.get("file") or request.FILES.get("csv_file")
        category_id = request.POST.get("category_id")
        test_id = request.POST.get("test_id")  # Optional: accept test_id directly
        course_id = request.POST.get("course_id")  # Optional: accept course_id
        
        # Get user - handle both Django User and MongoEngine User
        user = getattr(request, "user", None)
        # Check if user is AnonymousUser or not a MongoEngine User document
        # MongoEngine User documents have '_class' attribute, Django users don't
        if user:
            # Check if it's Django AnonymousUser (has is_anonymous attribute that returns True)
            if hasattr(user, 'is_anonymous') and user.is_anonymous:
                user = None
            # Check if it's not a MongoEngine Document (MongoEngine docs have _class)
            elif not hasattr(user, '_class'):
                user = None

        # Priority: test_id > course_id > category_id
        id_to_check = test_id or course_id or category_id

        if not csv_file or not id_to_check:
            return JsonResponse({
                "success": False,
                "message": "CSV file and test_id (or course_id or category_id) are required"
            }, status=400)

        if not ObjectId.is_valid(id_to_check):
            return JsonResponse({
                "success": False,
                "message": "Invalid ID format"
            }, status=400)

        # Try to find PracticeTest first (if test_id is provided)
        practice_test = None
        test_category = None
        
        if test_id:
            try:
                practice_test = PracticeTest.objects.get(id=ObjectId(test_id))
                # Get the TestCategory from the PracticeTest for CSVFile
                if practice_test.category:
                    test_category = practice_test.category
                elif practice_test.course and practice_test.course.category:
                    test_category = practice_test.course.category
            except PracticeTest.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": f"PracticeTest not found with ID: {test_id}"
                }, status=404)
        elif course_id:
            # If course_id is provided, find or create a test for this course
            from courses.models import Course
            try:
                course = Course.objects.get(id=ObjectId(course_id))
                test_category = course.category
                
                # Find the first test in this course, or create a default one
                practice_test = PracticeTest.objects(course=course).first()
                if not practice_test:
                    # Create a default test for this course
                    import re
                    from bson import ObjectId as BsonObjectId
                    default_title = f"{course.name} Test"
                    default_slug = re.sub(r'[^\w\s-]', '', default_title.lower().strip())
                    default_slug = re.sub(r'[-\s]+', '-', default_slug)
                    default_slug = default_slug.strip('-') or f"test-{BsonObjectId()}"
                    
                    practice_test = PracticeTest(
                        slug=default_slug,
                        title=default_title,
                        course=course,
                        category=course.category,
                        questions=0,
                        duration=60
                    )
                    practice_test.save()
            except Course.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": f"Course not found with ID: {course_id}"
                }, status=404)
        elif category_id:
            # Try to find PracticeTest by category_id (backward compatibility)
            try:
                practice_test = PracticeTest.objects.get(id=ObjectId(category_id))
                if practice_test.category:
                    test_category = practice_test.category
                elif practice_test.course and practice_test.course.category:
                    test_category = practice_test.course.category
            except PracticeTest.DoesNotExist:
                # If not a PracticeTest, try to find Category
                try:
                    test_category = Category.objects.get(id=ObjectId(category_id))
                    # Find first test in this category
                    practice_test = PracticeTest.objects(category=test_category).first()
                    if not practice_test:
                        return JsonResponse({
                            "success": False,
                            "message": f"Category found, but no PracticeTest exists for this category. Please create a test first."
                        }, status=400)
                except Category.DoesNotExist:
                    return JsonResponse({
                        "success": False,
                        "message": f"No PracticeTest or Category found with ID: {category_id}"
                    }, status=404)
        
        if not practice_test:
            return JsonResponse({
                "success": False,
                "message": "Could not find or create a test for the provided ID"
            }, status=400)
        
        if not test_category:
            # Try to get category from course or test
            if practice_test.course and practice_test.course.category:
                test_category = practice_test.course.category
            elif practice_test.category:
                test_category = practice_test.category
            else:
                return JsonResponse({
                    "success": False,
                    "message": "Test has no category assigned"
                }, status=400)

        # Read CSV content first (before saving to disk)
        csv_file.seek(0)  # Reset file pointer to beginning
        csv_data = csv_file.read().decode("utf-8")
        
        # Save file to disk
        filename = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{csv_file.name}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            csv_file.seek(0)  # Reset again for writing
            for chunk in csv_file.chunks():
                f.write(chunk)

        # Store CSVFile document (store path as string)
        # CSVFile uses TestCategory, so use test_category
        # uploaded_by can be None if user is not authenticated or is AnonymousUser
        csv_doc = CSVFile(
            category=test_category,
            file_path=file_path,  # store as string
            uploaded_by=user if user else None,  # Ensure None if user is invalid
            uploaded_at=timezone.now()
        )
        csv_doc.save()

        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(csv_data))

        # Check if test has a question limit set
        # Reload test to get current questions value
        practice_test.reload()
        question_limit = practice_test.questions if practice_test.questions > 0 else None
        
        # Get current question count for this test
        current_question_count = Question.objects(category=practice_test).count()

        questions_created = 0
        questions_skipped = 0
        errors = []

        # Convert to list to count total rows
        csv_rows = list(csv_reader)
        total_rows = len(csv_rows)

        for row_num, row in enumerate(csv_rows, start=1):
            # If test has a question limit, stop creating questions once we reach it
            if question_limit is not None:
                # Check if we've reached the limit (current + newly created)
                if (current_question_count + questions_created) >= question_limit:
                    # Count remaining rows as skipped
                    questions_skipped = total_rows - row_num + 1
                    break  # Stop processing more rows
            try:
                row = {k.strip(): v.strip() for k, v in row.items() if k and v}

                # Expected columns: question_text, question_type, options, correct_answer/correct_answers
                question_text = row.get("question_text", "")
                question_type = row.get("question_type", "single")
                
                # Handle both semicolon and pipe-separated options
                # Convert to list of dicts with 'text' key (as required by Question model)
                options_str = row.get("options", "")
                if ";" in options_str:
                    options_raw = [opt.strip() for opt in options_str.split(";") if opt.strip()]
                else:
                    options_raw = [opt.strip() for opt in options_str.split("|") if opt.strip()]
                
                # Convert to list of dicts format required by Question model
                options = [{"text": opt} for opt in options_raw]
                
                # Handle both correct_answer (singular) and correct_answers (plural)
                correct_answer_str = row.get("correct_answer", "") or row.get("correct_answers", "")
                
                # Parse correct answers - handle both comma/pipe separated and single values
                if "," in correct_answer_str or "|" in correct_answer_str:
                    correct_answer_list = [x.strip() for x in re.split(r"[|,]", correct_answer_str) if x.strip()]
                else:
                    correct_answer_list = [correct_answer_str.strip()] if correct_answer_str.strip() else []
                
                # Map letter answers (A, B, C, D) to option index or text
                # Question model stores correct_answers as option indices (strings) or option text
                correct_answers = []
                for ans in correct_answer_list:
                    ans = ans.strip()
                    # Check if answer is a single letter (A, B, C, D, etc.)
                    if len(ans) == 1 and ans.isalpha():
                        # Find the option index that starts with this letter
                        found = False
                        for idx, opt_dict in enumerate(options):
                            opt_text = opt_dict.get("text", "").strip()
                            # Check if option starts with "A)", "B)", etc. or just "A", "B"
                            if opt_text.upper().startswith(ans.upper() + ")") or opt_text.upper().startswith(ans.upper() + "."):
                                # Store as index (string) as required by Question model
                                correct_answers.append(str(idx))
                                found = True
                                break
                        if not found:
                            # Try to match by first character
                            for idx, opt_dict in enumerate(options):
                                opt_text = opt_dict.get("text", "").strip()
                                if opt_text and opt_text[0].upper() == ans.upper():
                                    correct_answers.append(str(idx))
                                    found = True
                                    break
                        if not found:
                            raise ValueError(f"Could not find option matching letter '{ans}'")
                    elif ans.isdigit():
                        # If answer is a number, use it as index directly
                        idx = int(ans)
                        if 0 <= idx < len(options):
                            correct_answers.append(str(idx))
                        else:
                            raise ValueError(f"Invalid option index: {idx}")
                    else:
                        # Answer is text - find matching option index
                        found = False
                        for idx, opt_dict in enumerate(options):
                            opt_text = opt_dict.get("text", "").strip()
                            if opt_text == ans or opt_text.endswith(ans) or ans in opt_text:
                                correct_answers.append(str(idx))
                                found = True
                                break
                        if not found:
                            # If not found, store as-is (might be used for matching)
                            correct_answers.append(ans)
                
                marks = int(row.get("marks", 1)) if row.get("marks") else 1
                explanation = row.get("explanation", "")

                if not question_text:
                    raise ValueError("Missing question_text")
                
                if not options or len(options) == 0:
                    raise ValueError("Missing or empty options")
                
                if not correct_answers or len(correct_answers) == 0:
                    raise ValueError("No valid correct answer found")

                # Normalize question_type to uppercase
                question_type_upper = question_type.upper()
                if question_type_upper not in ['MCQ', 'SINGLE', 'TRUE_FALSE']:
                    # Default to SINGLE if invalid
                    question_type_upper = 'SINGLE'

                # Questions are linked to PracticeTest, not TestCategory
                Question.objects.create(
                    category=practice_test,
                    question_text=question_text,
                    question_type=question_type_upper,
                    options=options,
                    correct_answers=correct_answers,
                    marks=marks,
                    explanation=explanation,
                )
                questions_created += 1
            except Exception as e:
                errors.append(f"Row {row_num} Error: {str(e)}")
                import traceback
                print(f"Error in row {row_num}: {str(e)}")
                print(traceback.format_exc())

        # Auto-update test question count after CSV upload
        # Only update if questions field is 0 or not set (preserve admin-set limit)
        if practice_test and questions_created > 0:
            from datetime import datetime
            # Refresh the test to get current questions value
            practice_test.reload()
            # Only update if questions is 0 or not set (preserve admin-set limit)
            if not practice_test.questions or practice_test.questions == 0:
                question_count = Question.objects(category=practice_test).count()
                practice_test.update(set__questions=question_count, set__updated_at=datetime.utcnow())
            else:
                # Just update the timestamp, preserve the question limit
                practice_test.update(set__updated_at=datetime.utcnow())

        # Build response message
        message_parts = [f"{questions_created} question(s) created"]
        if questions_skipped > 0:
            message_parts.append(f"{questions_skipped} question(s) skipped (test limit: {question_limit})")
        if len(errors) > 0:
            message_parts.append(f"{len(errors)} error(s)")
        message = ", ".join(message_parts)

        return JsonResponse({
            "success": True,
            "message": message,
            "errors": errors,
            "questions_created": questions_created,
            "questions_skipped": questions_skipped,
            "test_id": str(practice_test.id) if practice_test else None,
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)


# ✅ GET CSV FILES BY CATEGORY
@csrf_exempt
#@authenticate
@api_view(["GET"])
def get_csv_files(request):
    """
    Fetch all uploaded CSV files for a given category or test.
    """
    try:
        category_id = request.GET.get("category_id")
        test_id = request.GET.get("test_id")
        id_to_check = test_id or category_id

        if not id_to_check:
            return JsonResponse({
                "success": False,
                "message": "category_id (or test_id) is required"
            }, status=400)

        if not ObjectId.is_valid(id_to_check):
            return JsonResponse({
                "success": False,
                "message": "Invalid ID format"
            }, status=400)

        # Try to find PracticeTest first, then get its category
        final_category_id = None
        try:
            practice_test = PracticeTest.objects.get(id=ObjectId(id_to_check))
            # Get category from test (direct) or from course
            if practice_test.category:
                final_category_id = practice_test.category.id
            elif practice_test.course and practice_test.course.category:
                final_category_id = practice_test.course.category.id
            else:
                return JsonResponse({
                    "success": False,
                    "message": f"PracticeTest found but has no category assigned"
                }, status=400)
        except PracticeTest.DoesNotExist:
            # If not a PracticeTest, assume it's a Category ID
            try:
                category = Category.objects.get(id=ObjectId(id_to_check))
                final_category_id = category.id
            except Category.DoesNotExist:
                return JsonResponse({
                    "success": False,
                    "message": f"No PracticeTest or TestCategory found with ID: {id_to_check}"
                }, status=404)

        csv_files = CSVFile.objects(category=final_category_id)
        data = []

        for f in csv_files:
            data.append({
                "id": str(f.id),
                "filename": os.path.basename(f.file_path),
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                "uploaded_by": str(f.uploaded_by.id) if getattr(f, "uploaded_by", None) else None,
            })

        return JsonResponse({
            "success": True,
            "csv_files": data
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)


# ✅ DELETE CSV FILE (and related questions)
@csrf_exempt
#@authenticate
@api_view(["DELETE"])
def delete_csv_file(request, csv_id):
    """
    Delete a CSV file and all questions in that file's category.
    """
    try:
        if not ObjectId.is_valid(csv_id):
            return JsonResponse({
                "success": False,
                "message": "Invalid CSV ID"
            }, status=400)

        csv_doc = CSVFile.objects.get(id=ObjectId(csv_id))
        file_path = csv_doc.file_path

        # Delete file from disk
        if os.path.exists(file_path):
            os.remove(file_path)

        # Optionally delete related questions in that category
        Question.objects(category=csv_doc.category).delete()

        # Delete CSV record
        csv_doc.delete()

        return JsonResponse({
            "success": True,
            "message": "CSV file and related questions deleted successfully"
        })

    except CSVFile.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "CSV file not found"
        }, status=404)

    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": str(e)
        }, status=400)




# ----------------------------
# EXAM & TEST ATTEMPTS
# ----------------------------
@csrf_exempt
# @authenticate   
@restrict(['admin'])
def create_exam(request):
    """✅ Create a new exam linked to a Category."""
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))

        # ✅ Required fields validation
        required_fields = ['category_id', 'title', 'duration', 'questions_per_test']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({"success": False, "message": f"{field} is required"}, status=400)

        # ✅ Validate category_id
        category_id = data['category_id']
        if not ObjectId.is_valid(category_id):
            return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

        try:
            category = Category.objects.get(id=ObjectId(category_id))
        except Category.DoesNotExist:
            return JsonResponse({"success": False, "message": "Category not found"}, status=404)

        # ✅ Create Exam object
        exam = Exam(
            category=category,
            title=data['title'],
            description=data.get('description', ''),
            duration=int(data['duration']),
            questions_per_test=int(data['questions_per_test']),
            passing_score=float(data.get('passing_score', 60.0)),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        exam.save()

        return JsonResponse({
            "success": True,
            "message": "Exam created successfully",
            "exam_id": str(exam.id)
        }, status=201)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON body"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=400)


from datetime import datetime
import random
from bson import ObjectId

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from users.models import User
from exams.models import Question, Exam, TestAttempt, QuestionBank
from practice_tests.models import PracticeTest


@csrf_exempt
@authenticate  # only check if the user is authenticated
def start_test(request):
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        # Get user ID from request.user (dict from authenticate decorator)
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)
        
        # Get User object for TestAttempt
        user_obj = User.objects.get(id=ObjectId(user_id))
        
        exam_id = data.get("exam_id")
        category_id = data.get("category_id")

        if not category_id:
            return JsonResponse({"success": False, "message": "category_id is required"}, status=400)

        # ✅ Fetch category and exam (if given)
        # Try to find PracticeTest by ID first
        try:
            category = PracticeTest.objects.get(id=ObjectId(category_id))
        except PracticeTest.DoesNotExist:
            # If not found, try to find PracticeTest linked to Category
            from categories.models import Category
            try:
                test_category = Category.objects.get(id=ObjectId(category_id))
                # Find a PracticeTest linked to this Category
                category = PracticeTest.objects(category=test_category).first()
                if not category:
                    # Try to find by course's category
                    from courses.models import Course
                    courses = Course.objects(category=test_category)
                    for course in courses:
                        category = PracticeTest.objects(course=course).first()
                        if category:
                            break
                    if not category:
                        return JsonResponse({"success": False, "message": "Practice test not found for this category"}, status=404)
            except Category.DoesNotExist:
                return JsonResponse({"success": False, "message": "Category not found"}, status=404)
            except Exception as e:
                return JsonResponse({"success": False, "message": f"Error finding practice test: {str(e)}"}, status=400)
        
        exam = Exam.objects.get(id=ObjectId(exam_id)) if exam_id else None

        # ✅ Check enrollment - user must be enrolled to take the test
        # Prefer course enrollment over category enrollment
        from categories.models import Category
        from enrollments.models import Enrollment
        
        enrolled = False
        
        # Get category_obj for later use (regardless of enrollment check path)
        category_obj = None
        if hasattr(category, 'category') and category.category:
            category_obj = category.category
        elif hasattr(category, 'course') and category.course and category.course.category:
            category_obj = category.course.category
        
        # Check enrollment by course first (preferred)
        if hasattr(category, 'course') and category.course:
            course_obj = category.course
            # Check enrollment record
            enrollment = Enrollment.objects(user_name=user_id, course=course_obj).first()
            if enrollment:
                enrolled = True
            else:
                # Also check in user's enrolled_courses list
                enrolled = any(str(c.id) == str(course_obj.id) for c in user_obj.enrolled_courses if hasattr(c, 'id'))
        
        # Fallback: Check enrollment by category (backward compatibility)
        if not enrolled and category_obj:
                # Check enrollment record
                enrollment = Enrollment.objects(user_name=user_id, category=category_obj).first()
                if enrollment:
                    enrolled = True
                else:
                    # Also check in user's enrolled_courses list
                    enrolled = any(str(c.id) == str(category_obj.id) for c in user_obj.enrolled_courses if hasattr(c, 'id'))
        
        if not enrolled:
            return JsonResponse({
                "success": False,
                "message": "You are not enrolled in this course. Please enroll to take the test.",
                "requires_enrollment": True
            }, status=403)

        # ✅ Get ALL questions linked to this category
        all_questions = list(Question.objects(category=category))
        if not all_questions:
            return JsonResponse({"success": False, "message": "No questions found in this category"}, status=404)

        # ✅ Limit questions to the test's question count (if specified)
        question_limit = category.questions if category.questions > 0 else len(all_questions)

        # ✅ Shuffle question order randomly so different students get different sets
        import random
        random.shuffle(all_questions)
        
        # ✅ Take only the limited number of questions
        selected_questions = all_questions[:question_limit]

        formatted_questions = []
        for q in selected_questions:
            # Process options - handle both old format (strings) and new format (dicts)
            processed_options = []
            try:
                if isinstance(q.options, str):
                    options_data = json.loads(q.options) if q.options else []
                else:
                    options_data = q.options or []
            except (json.JSONDecodeError, TypeError):
                options_data = []
            
            if isinstance(options_data, list):
                for opt in options_data:
                    if isinstance(opt, dict):
                        processed_options.append(opt)
                    elif isinstance(opt, str):
                        # Backward compatibility: convert string to dict
                        processed_options.append({'text': opt})
                    else:
                        processed_options.append({'text': str(opt)})
            
            # Process correct_answers
            processed_correct_answers = []
            try:
                if isinstance(q.correct_answers, str):
                    correct_answers_data = json.loads(q.correct_answers) if q.correct_answers else []
                else:
                    correct_answers_data = q.correct_answers or []
            except (json.JSONDecodeError, TypeError):
                correct_answers_data = []
            
            if isinstance(correct_answers_data, list):
                for ans in correct_answers_data:
                    if isinstance(ans, dict):
                        processed_correct_answers.append(ans)
                    elif isinstance(ans, str):
                        processed_correct_answers.append(ans)
                    else:
                        processed_correct_answers.append(str(ans))
            
            formatted_questions.append({
                "id": str(q.id),
                "question_text": getattr(q, 'question_text', '') or "",
                "question_type": getattr(q, 'question_type', 'single_choice'),
                "options": processed_options,
                "correct_answers": processed_correct_answers,
                "marks": getattr(q, 'marks', 1),
                "explanation": getattr(q, 'explanation', '') or "",
                "tags": getattr(q, 'tags', []) or [],  # Include tags for topic analysis
            })

        # ✅ Create test attempt
        attempt = TestAttempt.objects.create(
            user=user_obj,
            exam=exam,
            category=category,
            questions=formatted_questions,
            total_marks=sum(q.marks for q in selected_questions),
            time_limit=getattr(exam, 'duration', 30) if exam else getattr(category, 'duration', 30),
            start_time=datetime.utcnow(),
            is_completed=False
        )

        # ✅ Include category/test info
        try:
            category_name = getattr(category.category, 'name', '') if hasattr(category, 'category') and category.category else getattr(category, 'title', 'Practice Test')
        except:
            category_name = getattr(category, 'title', 'Practice Test')
        
        # Get course name if available
        course_name = ""
        try:
            if hasattr(category, 'course') and category.course:
                course_name = getattr(category.course, 'name', '') or ""
        except Exception as e:
            print(f"Error getting course name: {e}")
        
        test_name = getattr(exam, 'title', None) if exam else None
        if not test_name:
            test_name = getattr(category, 'title', 'Practice Test')
        
        description = getattr(category, 'description', '') or ''
        if not description and exam:
            description = getattr(exam, 'description', '') or ''

        # Ensure time_limit is a valid integer
        time_limit = int(attempt.time_limit) if attempt.time_limit else 30

        # Get category ID for enrollment redirect
        category_id_for_enroll = None
        if category_obj:
            category_id_for_enroll = str(category_obj.id)

        # ✅ Return navigable structure
        return JsonResponse({
            "success": True,
            "message": "Test started successfully",
            "attempt_id": str(attempt.id),
            "questions": formatted_questions,
            "total_questions": len(formatted_questions),
            "current_question_index": 0,  # frontend starts here
            "time_limit": time_limit,
            "category_name": category_name or "Practice Test",
            "course_name": course_name or "",
            "test_name": test_name or "Practice Test",
            "category_id": category_id_for_enroll,  # Category ID for enrollment redirect
            "description": description or ""
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except PracticeTest.DoesNotExist:
        return JsonResponse({"success": False, "message": "Category not found"}, status=404)
    except Exam.DoesNotExist:
        return JsonResponse({"success": False, "message": "Exam not found"}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON"}, status=400)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=400)



# -----------------------------
# SUBMIT TEST
# -----------------------------
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
import json
from bson import ObjectId

@csrf_exempt
@authenticate
def submit_test(request, attempt_id):
    print(f"[submit_test] Request received: {request.method} {request.path}, attempt_id: {attempt_id}")
    
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Parse JSON body
        data = json.loads(request.body)
        user_answers = data.get("user_answers", [])
        print(f"[submit_test] Received {len(user_answers)} user answers")

        # Get the TestAttempt using id field (your model uses id as primary key)
        try:
            attempt = TestAttempt.objects.get(_id=ObjectId(attempt_id))
            print(f"[submit_test] Found attempt: {attempt.id}, user: {attempt.user.id}")
        except TestAttempt.DoesNotExist:
            print(f"[submit_test] Attempt {attempt_id} not found")
            return JsonResponse({"success": False, "message": "Attempt not found"}, status=404)


        total_score = 0

        # OPTIMIZATION: Batch fetch all questions at once instead of individual queries
        question_ids = [ObjectId(ans.get("question_id")) for ans in user_answers if ans.get("question_id") and ObjectId.is_valid(ans.get("question_id"))]
        
        # Create a map of questions for quick lookup
        questions_map = {}
        
        # Try to fetch from exams.models.Question first (batch)
        if question_ids:
            try:
                from exams.models import Question as ExamQuestion
                exam_questions = ExamQuestion.objects.no_dereference().filter(_id__in=question_ids)
                for q in exam_questions:
                    questions_map[str(q.id)] = q
            except Exception as e:
                print(f"[submit_test] Error batch fetching from exams.models: {e}")
        
        # Fetch remaining questions from questions.models.Question (batch)
        remaining_ids = [qid for qid in question_ids if str(qid) not in questions_map]
        if remaining_ids:
            try:
                from questions.models import Question as CourseQuestion
                course_questions = CourseQuestion.objects.filter(id__in=remaining_ids)
                for q in course_questions:
                    questions_map[str(q.id)] = q
            except Exception as e:
                print(f"[submit_test] Error batch fetching from questions.models: {e}")

        # Process user answers using pre-fetched questions
        for ans in user_answers:
            question_id = ans.get("question_id")
            selected = ans.get("selected_answers", [])

            if not question_id:
                continue

            question = questions_map.get(str(question_id))
            if not question:
                continue

            # Get correct_answers efficiently
            correct_answers = []
            try:
                question_data = question.to_mongo().to_dict()
                correct_answers = question_data.get('correct_answers', []) or []
            except Exception:
                try:
                    correct_answers = getattr(question, 'correct_answers', []) or []
                except Exception:
                    correct_answers = []
            
            selected_str = sorted([str(s) for s in selected])
            correct_str = sorted([str(c) for c in correct_answers])
            
            if selected_str == correct_str:
                marks = 1
                try:
                    question_data = question.to_mongo().to_dict()
                    marks = question_data.get('marks', 1) or 1
                except Exception:
                    try:
                        marks = getattr(question, 'marks', 1) or 1
                    except Exception:
                        marks = 1
                total_score += marks

        # Calculate percentage
        percentage = (total_score / attempt.total_marks) * 100 if attempt.total_marks and attempt.total_marks > 0 else 0
        
        # Get passing score from PracticeTest or default
        passing_score = 60.0  # Default
        if attempt.category:
            # Try to get passing_score from PracticeTest or Course
            passing_score = getattr(attempt.category, 'passing_score', None)
            if passing_score is None:
                # Try from exam if available
                if attempt.exam:
                    passing_score = getattr(attempt.exam, 'passing_score', 60.0)
                else:
                    passing_score = 60.0
        
        passed = percentage >= passing_score

        # Update questions array with user_selected_answers, is_correct, and marks_awarded for each question
        updated_questions = []
        print(f"[submit_test] Processing {len(attempt.questions)} questions from attempt")
        
        for idx, q in enumerate(attempt.questions):
            # Try multiple ways to get question_id
            question_id = str(q.get("question_id", "") or q.get("id", "") or q.get("_id", "")).strip()
            
            if not question_id or question_id == "None" or question_id == "":
                print(f"[submit_test] Warning: Question {idx + 1} in attempt has no ID: {q}")
                # Still add it but mark as unanswered
                q["user_selected_answers"] = []
                q["is_correct"] = False
                q["marks_awarded"] = 0
                updated_questions.append(q)
                continue
            
            # Validate ObjectId format
            if not ObjectId.is_valid(question_id):
                print(f"[submit_test] Warning: Question ID {question_id} is not a valid ObjectId")
                # Still process it, but log the warning
            
            # Find matching user answer - try exact match first, then try without leading/trailing spaces
            user_answer_entry = None
            for ans in user_answers:
                user_q_id = str(ans.get("question_id", "")).strip()
                # Try exact match
                if user_q_id == question_id:
                    user_answer_entry = ans
                    break
                # Try with ObjectId conversion (in case of format differences)
                try:
                    if ObjectId.is_valid(user_q_id) and ObjectId.is_valid(question_id):
                        if ObjectId(user_q_id) == ObjectId(question_id):
                            user_answer_entry = ans
                            break
                except:
                    pass
            
            print(f"[submit_test] Question {question_id} (index {idx + 1}): found answer entry: {user_answer_entry is not None}")
            if user_answer_entry:
                q["user_selected_answers"] = user_answer_entry.get("selected_answers", [])
                print(f"[submit_test] Question {question_id}: matched user answer with {len(q['user_selected_answers'])} selections")
            else:
                q["user_selected_answers"] = []
                print(f"[submit_test] Question {question_id}: no matching user answer found")
            
            # Calculate is_correct and marks_awarded using pre-fetched questions map
            try:
                question_obj = questions_map.get(question_id)
                
                if question_obj:
                    selected = q.get("user_selected_answers", [])
                    # Get correct_answers efficiently
                    correct_answers = []
                    try:
                        question_data = question_obj.to_mongo().to_dict()
                        correct_answers = question_data.get('correct_answers', []) or []
                    except Exception:
                        try:
                            if hasattr(question_obj, 'correct_answers'):
                                correct_answers = question_obj.correct_answers or []
                        except Exception:
                            correct_answers = []
                    
                    # Normalize to strings for comparison
                    selected_str = sorted([str(s) for s in selected])
                    correct_str = sorted([str(c) for c in correct_answers])
                    is_correct = selected_str == correct_str
                    
                    # Get marks efficiently
                    marks = 1
                    try:
                        question_data = question_obj.to_mongo().to_dict()
                        marks = question_data.get('marks', 1) or q.get("marks", 1) or 1
                    except Exception:
                        try:
                            marks = getattr(question_obj, 'marks', 1) or q.get("marks", 1) or 1
                        except Exception:
                            marks = q.get("marks", 1) or 1
                    
                    marks_awarded = marks if is_correct else 0
                    q["is_correct"] = is_correct
                    q["marks_awarded"] = marks_awarded
                else:
                    q["is_correct"] = False
                    q["marks_awarded"] = 0
            except Exception as e:
                print(f"[submit_test] Error calculating correctness for question {question_id}: {e}")
                q["is_correct"] = False
                q["marks_awarded"] = 0
            
            updated_questions.append(q)

        # Calculate duration taken in minutes
        end_time = datetime.utcnow()
        duration_taken = None
        if attempt.start_time:
            time_diff = end_time - attempt.start_time
            duration_taken = int(time_diff.total_seconds() / 60)  # Convert to minutes

        # Update attempt - this saves to MongoDB
        attempt.update(
            set__user_answers=user_answers,
            set__questions=updated_questions,  # Update questions with user_selected_answers
            set__score=total_score,
            set__percentage=percentage,
            set__passed=passed,
            set__is_completed=True,
            set__end_time=end_time,
            set__duration_taken=duration_taken
        )
        
        # Reload to verify the update was saved
        attempt.reload()
        print(f"[submit_test] Attempt saved to MongoDB: id={attempt.id}, is_completed={attempt.is_completed}, score={attempt.score}, percentage={attempt.percentage}%")
        print(f"[submit_test] Submission successful: score={total_score}, percentage={percentage:.2f}%, passed={passed}")
        
        return JsonResponse({
            "success": True,
            "message": "Test submitted successfully",
            "score": total_score,
            "percentage": round(percentage, 2),
            "passed": passed,
            "total_marks": attempt.total_marks,
            "duration_taken": duration_taken
        }, status=200)

    except TestAttempt.DoesNotExist:
        print(f"[submit_test] Attempt {attempt_id} not found")
        return JsonResponse({"success": False, "message": "Attempt not found"}, status=404)
    except json.JSONDecodeError as e:
        print(f"[submit_test] JSON decode error: {e}")
        return JsonResponse({"success": False, "message": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[submit_test] Error: {error_msg}")
        traceback.print_exc()
        return JsonResponse({
            "success": False, 
            "message": error_msg or "An error occurred while submitting the test"
        }, status=400)



# -----------------------------
# GET TEST RESULT
# -----------------------------
# -----------------------------
# GET TEST RESULT
# -----------------------------
@csrf_exempt
# @authenticate
def get_test_result(request, attempt_id):
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        attempt = TestAttempt.objects.no_dereference().get(_id=ObjectId(attempt_id))
        raw_data = attempt.to_mongo().to_dict()

        user_id = None
        category_id = None

        if "user" in raw_data and isinstance(raw_data["user"], dict):
            user_id = str(raw_data["user"].get("$id")) if "$id" in raw_data["user"] else str(raw_data["user"])
        elif isinstance(raw_data.get("user"), ObjectId):
            user_id = str(raw_data["user"])

        if "category" in raw_data and isinstance(raw_data["category"], dict):
            category_id = str(raw_data["category"].get("$id")) if "$id" in raw_data["category"] else str(raw_data["category"])
        elif isinstance(raw_data.get("category"), ObjectId):
            category_id = str(raw_data["category"])

        result = {
            "user": user_id,
            "category": category_id,
            "score": raw_data.get("score", 0),
            "total_marks": raw_data.get("total_marks", 0),
            "percentage": raw_data.get("percentage", 0),
            "passed": raw_data.get("passed", False),
            "start_time": str(raw_data.get("start_time")),
            "end_time": str(raw_data.get("end_time")),
        }

        return JsonResponse({"success": True, "result": result}, status=200)

    except TestAttempt.DoesNotExist:
        return JsonResponse({"success": False, "message": "Attempt not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from .models import TestAttempt


@csrf_exempt
def get_attempt_questions(request, attempt_id):
    """
    ✅ Fetch all questions for a given TestAttempt document.
    Includes user-selected answers, correct answers, and explanation.
    """
    try:
        # ✅ Ensure attempt_id is valid ObjectId
        if not ObjectId.is_valid(attempt_id):
            return JsonResponse({
                "success": False,
                "message": "Invalid attempt ID format"
            }, status=400)

        # ✅ Fetch using pk/ObjectId (correct for MongoEngine)
        attempt = TestAttempt.objects.get(pk=ObjectId(attempt_id))

        # ✅ Ensure questions exist
        if not hasattr(attempt, "questions") or not isinstance(attempt.questions, list):
            return JsonResponse({
                "success": False,
                "message": "No questions found for this attempt."
            }, status=404)

        questions_data = []

        for q in attempt.questions:
            question_id = str(q.get("question_id", ""))
            question_text = q.get("question_text", "")
            options = q.get("options", [])
            correct_answers_raw = q.get("correct_answers", [])
            user_selected_answers_raw = q.get("user_selected_answers", [])
            marks = q.get("marks", 1)
            explanation = q.get("explanation", "")

            # ✅ Normalize correct_answers - convert to strings and handle both indices and values
            correct_answers = []
            for ans in correct_answers_raw:
                if isinstance(ans, (int, float)):
                    correct_answers.append(str(int(ans)))
                elif isinstance(ans, str):
                    # If it's a numeric string, keep it as is (it's an index)
                    if ans.isdigit():
                        correct_answers.append(ans)
                    else:
                        # It's a value, try to find matching option index
                        found_index = None
                        for idx, opt in enumerate(options):
                            opt_text = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                            if str(opt_text).strip() == str(ans).strip():
                                found_index = str(idx)
                                break
                        if found_index is not None:
                            correct_answers.append(found_index)
                        else:
                            correct_answers.append(ans)
                else:
                    correct_answers.append(str(ans))
            
            # ✅ Normalize user_selected_answers - convert option values to indices if needed
            user_selected_answers = []
            for ans in user_selected_answers_raw:
                if isinstance(ans, (int, float)):
                    user_selected_answers.append(str(int(ans)))
                elif isinstance(ans, str):
                    if ans.isdigit():
                        # It's already an index
                        user_selected_answers.append(ans)
                    else:
                        # It's an option value, try to find matching option index
                        found_index = None
                        for idx, opt in enumerate(options):
                            opt_text = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                            opt_value = opt.get('value', opt_text) if isinstance(opt, dict) else opt_text
                            # Compare both text and value
                            if str(opt_text).strip() == str(ans).strip() or str(opt_value).strip() == str(ans).strip():
                                found_index = str(idx)
                                break
                        if found_index is not None:
                            user_selected_answers.append(found_index)
                        else:
                            # Keep as-is if no match found
                            user_selected_answers.append(ans)
                elif isinstance(ans, dict):
                    # Handle object format {text: ..., value: ...}
                    opt_text = ans.get('text', '') or ans.get('value', '')
                    found_index = None
                    for idx, opt in enumerate(options):
                        opt_text_val = opt.get('text', '') if isinstance(opt, dict) else str(opt)
                        if str(opt_text_val).strip() == str(opt_text).strip():
                            found_index = str(idx)
                            break
                    if found_index is not None:
                        user_selected_answers.append(found_index)
                    else:
                        user_selected_answers.append(str(opt_text))
                else:
                    user_selected_answers.append(str(ans))

            # ✅ Determine correctness - compare normalized answers (both as indices)
            # Sort both sets for consistent comparison
            correct_set = set(sorted(correct_answers))
            user_set = set(sorted(user_selected_answers))
            is_correct = correct_set == user_set
            marks_awarded = marks if is_correct else 0

            questions_data.append({
                "question_id": question_id,
                "question_text": question_text,
                "options": options,
                "correct_answers": correct_answers,  # Return normalized correct_answers
                "user_selected_answers": user_selected_answers,  # Return normalized user_selected_answers
                "is_correct": is_correct,
                "marks": marks,
                "marks_awarded": marks_awarded,
                "explanation": explanation,
            })

        return JsonResponse({
            "success": True,
            "questions": questions_data
        }, status=200)

    except TestAttempt.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Attempt not found."
        }, status=404)

    except ValidationError:
        return JsonResponse({
            "success": False,
            "message": "Invalid ObjectId."
        }, status=400)

    except Exception as e:
        print("❌ Error in get_attempt_questions:", e)
        return JsonResponse({
            "success": False,
            "message": f"Internal server error: {str(e)}"
        }, status=500)


# -----------------------------
# GET TEST RANKINGS/LEADERBOARD
# -----------------------------
@csrf_exempt
def get_test_rankings(request, category_id):
    """
    Get rankings/leaderboard for a specific test category.
    Returns top performers sorted by percentage (descending).
    Supports search query parameter for filtering by user name.
    """
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(category_id):
            return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

        # Get search query parameter
        search_query = request.GET.get('search', '').strip().lower()

        # Get all completed attempts for this category, sorted by percentage
        attempts = TestAttempt.objects(
            category=ObjectId(category_id),
            is_completed=True
        ).order_by('-percentage', '-score', 'end_time')

        rankings = []
        attempt_list = []  # Store all attempts with user info

        # First pass: collect all attempts (not just best per user)
        for attempt in attempts:
            # Safely get user ID from ReferenceField
            user_id = None
            try:
                raw_data = attempt.to_mongo().to_dict()
                user_data = raw_data.get("user")
                if isinstance(user_data, dict):
                    user_id = str(user_data.get("id", ""))
                elif hasattr(attempt.user, 'id'):
                    user_id = str(attempt.user.id)
                elif ObjectId.is_valid(str(attempt.user)):
                    user_id = str(attempt.user)
            except Exception as e:
                print(f"Error getting user ID: {e}")
                continue

            if not user_id:
                continue
            
            # Add all attempts to the list (not filtering to best)
            attempt_list.append({
                    "attempt": attempt,
                "user_id": user_id
            })

        # Sort all attempts by percentage (descending), then by score (descending), then by completion time (ascending - earlier attempts first if same score)
        sorted_attempts = sorted(
            attempt_list,
            key=lambda x: (
                -x["attempt"].percentage, 
                -x["attempt"].score, 
                x["attempt"].end_time if x["attempt"].end_time else datetime.min
            )
        )

        rank = 1
        for item in sorted_attempts:
            attempt = item["attempt"]
            user_id = item["user_id"]
            
            # Get user name - safely dereference
            user_name = "Anonymous"
            try:
                if hasattr(attempt.user, 'fullname') and attempt.user.fullname:
                    user_name = attempt.user.fullname
                elif hasattr(attempt.user, 'email') and attempt.user.email:
                    user_name = attempt.user.email
                else:
                    # Try to fetch user directly
                    user_obj = User.objects(id=ObjectId(user_id)).first()
                    if user_obj:
                        user_name = user_obj.fullname or user_obj.email or "Anonymous"
            except Exception as e:
                print(f"Error getting user name: {e}")

            # Apply search filter if provided
            if search_query and search_query not in user_name.lower():
                continue

            # Get course and category information
            course_name = ""
            category_name = ""
            test_name = ""
            try:
                # Get PracticeTest (test) from attempt.category
                if attempt.category:
                    practice_test = attempt.category
                    test_name = getattr(practice_test, 'title', 'Unknown Test')
                    
                    # Get course if available
                    if hasattr(practice_test, 'course') and practice_test.course:
                        course = practice_test.course
                        course_name = getattr(course, 'name', 'Unknown Course')
                        
                        # Get category from course if available
                        if hasattr(course, 'category') and course.category:
                            category = course.category
                            category_name = getattr(category, 'name', 'Unknown Category')
                    
                    # Fallback: get category directly from practice_test if course doesn't have it
                    if not category_name and hasattr(practice_test, 'category') and practice_test.category:
                        category = practice_test.category
                        category_name = getattr(category, 'name', 'Unknown Category')
            except Exception as e:
                print(f"Error getting course/category info: {e}")

            # Add ranking (outside try-except block so it always happens)
                rankings.append({
                    "rank": rank,
                    "user_id": user_id,
                    "user_name": user_name,
                    "score": attempt.score,
                    "total_marks": attempt.total_marks,
                    "percentage": round(attempt.percentage, 2),
                    "passed": attempt.passed,
                "completed_at": attempt.end_time.isoformat() if attempt.end_time else None,
                "course_name": course_name,
                "category_name": category_name,
                "test_name": test_name,
                "attempt_id": str(attempt.id)  # Add attempt ID for unique identification
                })
                rank += 1

        return JsonResponse({
            "success": True,
            "rankings": rankings,
            "total_participants": len(rankings)
        }, status=200)

    except Exception as e:
        import traceback
        print(f"Rankings error: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=400)


@csrf_exempt
def get_topic_wise_analysis(request, attempt_id):
    """
    Get topic-wise analysis for a test attempt.
    Groups questions by tags (topics) and calculates statistics.
    """
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(attempt_id):
            return JsonResponse({"success": False, "message": "Invalid attempt ID"}, status=400)
        
        attempt = TestAttempt.objects.get(id=ObjectId(attempt_id))
        
        if not hasattr(attempt, "questions") or not isinstance(attempt.questions, list):
            return JsonResponse({
                "success": False,
                "message": "No questions found for this attempt"
            }, status=404)
        
        # Get user answers - need to check is_correct from questions
        # Group questions by topic (tags)
        topic_stats = {}
        
        for idx, q in enumerate(attempt.questions):
            # Get tags from question - check if stored in question dict first, then fetch from Question model
            question_id = q.get("id") or q.get("question_id")
            tags = q.get("tags", []) or []  # Check if tags are stored in the question dict
            
            # If not in dict, fetch from Question model
            if (not tags or len(tags) == 0) and question_id and ObjectId.is_valid(str(question_id)):
                try:
                    question_obj = Question.objects.get(id=ObjectId(question_id))
                    tags = getattr(question_obj, 'tags', []) or []
                except Question.DoesNotExist:
                    pass
                except Exception as e:
                    print(f"Error fetching tags for question {question_id}: {e}")
            
            # If no tags, use "General" as default topic
            if not tags or len(tags) == 0:
                tags = ["General"]
            
            # Check if answer is correct - check from question data or calculate
            is_correct = q.get("is_correct", False)
            marks = q.get("marks", 1)
            marks_awarded = q.get("marks_awarded", 0) if is_correct else 0
            
            # Update stats for each tag
            for tag in tags:
                if tag not in topic_stats:
                    topic_stats[tag] = {
                        "topic": tag,
                        "total_questions": 0,
                        "correct_questions": 0,
                        "wrong_questions": 0,
                        "total_marks": 0,
                        "marks_obtained": 0,
                        "percentage": 0
                    }
                
                topic_stats[tag]["total_questions"] += 1
                topic_stats[tag]["total_marks"] += marks
                topic_stats[tag]["marks_obtained"] += marks_awarded
                
                if is_correct:
                    topic_stats[tag]["correct_questions"] += 1
                else:
                    topic_stats[tag]["wrong_questions"] += 1
        
        # Calculate percentage for each topic
        for topic in topic_stats:
            stats = topic_stats[topic]
            if stats["total_marks"] > 0:
                stats["percentage"] = round((stats["marks_obtained"] / stats["total_marks"]) * 100, 2)
            else:
                stats["percentage"] = 0
        
        # Convert to list and sort by percentage (descending)
        topic_list = list(topic_stats.values())
        topic_list.sort(key=lambda x: x["percentage"], reverse=True)
        
        return JsonResponse({
            "success": True,
            "topic_analysis": topic_list,
            "total_topics": len(topic_list)
        }, status=200)
    
    except TestAttempt.DoesNotExist:
        return JsonResponse({"success": False, "message": "Attempt not found"}, status=404)
    except Exception as e:
        print(f"Error in topic analysis: {e}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)




from django.http import JsonResponse
# from .models import Attempt, QuestionAttempt

def get_result_summary(request, attempt_id):
    try:
        attempt = Attempt.objects.get(id=attempt_id)
        result_data = {
            "result": {
                "score": attempt.score,
                "total_marks": attempt.total_marks,
                "percentage": attempt.percentage,
                "passed": attempt.passed,
            }
        }
        return JsonResponse(result_data, status=200)
    except Attempt.DoesNotExist:
        return JsonResponse({"error": "Attempt not found"}, status=404)





# -----------------------------
# CREATE QUESTION BANK
# -----------------------------
@csrf_exempt
#@authenticate
def create_question_bank(request):
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        category_id = data.get("category")
        if not category_id:
            return JsonResponse({"success": False, "message": "category is required"}, status=400)

        category = PracticeTest.objects.get(id=ObjectId(category_id))
        question_ids = data.get("question_ids", [])
        questions = [Question.objects.get(id=ObjectId(qid)) for qid in question_ids]

        qb = QuestionBank.objects.create(
            category=category,
            name=data.get("name"),
            description=data.get("description", ""),
            questions=questions,
            total_questions=len(questions)
        )
        return JsonResponse({"success": True, "message": "Question bank created", "id": str(qb.id)}, status=201)

    except PracticeTest.DoesNotExist:
        return JsonResponse({"success": False, "message": "Category not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)


# -----------------------------
# GET OR CREATE TEST ATTEMPT
# -----------------------------
@csrf_exempt
@authenticate
def get_or_create_test_attempt(request):
    """
    Get an existing incomplete test attempt for a user and test, or create a new one.
    This allows users to resume incomplete tests or start new ones.
    """
    print(f"[get_or_create_test_attempt] Request received: {request.method} {request.path}")
    
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Check if request.body is empty
        if not request.body:
            return JsonResponse({"success": False, "message": "Request body is empty"}, status=400)
        
        data = json.loads(request.body)
        print(f"[get_or_create_test_attempt] Request data: {data}")
        
        # Get user ID from request.user (dict from authenticate decorator)
        if not hasattr(request, 'user') or not request.user:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)
        
        user_id = request.user.get("id") if isinstance(request.user, dict) else getattr(request.user, "id", None)
        if not user_id:
            print(f"[get_or_create_test_attempt] User ID not found. request.user: {request.user}")
            return JsonResponse({"success": False, "message": "User not authenticated. Please log in again."}, status=401)
        
        print(f"[get_or_create_test_attempt] User ID: {user_id}, type: {type(user_id)}")
        
        # Normalize user_id to string for validation
        user_id_str = str(user_id).strip()
        if not user_id_str:
            print(f"[get_or_create_test_attempt] Empty user_id after normalization")
            return JsonResponse({"success": False, "message": "Invalid user ID in token. Please log in again."}, status=401)
        
        # Get User object for TestAttempt
        # user_id from JWT is a string representation of ObjectId
        try:
            # Validate that user_id is a valid ObjectId string
            if not ObjectId.is_valid(user_id_str):
                print(f"[get_or_create_test_attempt] Invalid user_id format: {user_id_str}")
                return JsonResponse({"success": False, "message": "Invalid user ID format in token. Please log in again."}, status=400)
            
            user_obj = User.objects.get(id=ObjectId(user_id_str))
            print(f"[get_or_create_test_attempt] User found: {user_obj.email}")
        except User.DoesNotExist:
            print(f"[get_or_create_test_attempt] User with ID {user_id_str} does not exist in database")
            return JsonResponse({
                "success": False, 
                "message": "User account not found. Please log in again."
            }, status=404)
        except Exception as e:
            print(f"[get_or_create_test_attempt] Error getting user: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "success": False, 
                "message": f"Error retrieving user: {str(e)}"
            }, status=500)
        
        exam_id = data.get("exam_id")
        category_id = data.get("category_id")
        test_id = data.get("test_id")  # Can be PracticeTest ID or index (1-based) in course.practice_tests
        
        print(f"[get_or_create_test_attempt] exam_id: {exam_id}, test_id: {test_id}, category_id: {category_id}")
        
        # If we have exam_id and test_id (but not category_id), try to find PracticeTest from course
        if exam_id and test_id and not category_id:
            try:
                from courses.models import Course
                course = Course.objects.get(id=ObjectId(exam_id))
                # Check if test_id is a PracticeTest ID (ObjectId)
                if ObjectId.is_valid(test_id):
                    try:
                        # Try to get PracticeTest by ID
                        category = PracticeTest.objects.get(id=ObjectId(test_id))
                        # Verify it belongs to this course
                        if category.course.id != course.id:
                            return JsonResponse({"success": False, "message": "Practice test does not belong to this course"}, status=404)
                    except PracticeTest.DoesNotExist:
                        return JsonResponse({"success": False, "message": "Practice test not found"}, status=404)
                else:
                    # Try to find by slug first (SEO-friendly)
                    category = PracticeTest.objects(slug=test_id, course=course).first()
                    if not category:
                        # test_id is likely an index (1-based) - query PracticeTest objects directly
                        try:
                            test_index = int(test_id) - 1  # Convert to 0-based index
                            
                            # Get all practice tests for this course from the database
                            all_course_tests = list(PracticeTest.objects(course=course).order_by('created_at'))
                            
                            if test_index >= 0 and test_index < len(all_course_tests):
                                category = all_course_tests[test_index]
                            else:
                                return JsonResponse({
                                    "success": False, 
                                    "message": f"Practice test index {test_index + 1} out of range. Course has {len(all_course_tests)} practice test(s)."
                                }, status=404)
                        except ValueError:
                            return JsonResponse({"success": False, "message": f"Invalid test_id format: '{test_id}'. Expected a slug, number (1-based index), or ObjectId."}, status=400)
            except Course.DoesNotExist:
                return JsonResponse({"success": False, "message": "Course not found"}, status=404)
            except (ValueError, TypeError):
                return JsonResponse({"success": False, "message": "Invalid test_id format"}, status=400)
        elif category_id:
            # Direct PracticeTest ID provided
            try:
                category = PracticeTest.objects.get(id=ObjectId(category_id))
            except PracticeTest.DoesNotExist:
                return JsonResponse({"success": False, "message": "Practice test not found"}, status=404)
        else:
            return JsonResponse({"success": False, "message": "category_id or (exam_id and test_id) is required"}, status=400)
        
        # exam_id is actually a Course ID, not an Exam ID
        # Try to get Exam if it exists, but it's optional
        exam = None
        if exam_id:
            try:
                exam = Exam.objects.get(id=ObjectId(exam_id))
            except Exam.DoesNotExist:
                # That's okay - exam_id is a Course ID, not an Exam ID
                exam = None

        # ✅ Ensure practice test is in course's practice_tests reference list
        if exam_id and category:
            try:
                from courses.models import Course
                course = Course.objects.get(id=ObjectId(exam_id))
                
                # Check if practice test is already in the course's practice_tests list
                if category.id not in [str(pt.id) for pt in course.practice_tests]:
                    # Add the practice test reference to the course
                    course.practice_tests.append(category)
                    course.save()
            except Exception as e:
                # Don't fail the request if updating practice_tests fails
                print(f"Warning: Could not update course practice_tests: {str(e)}")

        # Check for existing incomplete attempt for this user and test
        existing_attempt = TestAttempt.objects(
            user=user_obj,
            category=category,
            is_completed=False
        ).order_by('-start_time').first()

        if existing_attempt:
            # Return existing incomplete attempt
            return JsonResponse({
                "success": True,
                "attempt_id": str(existing_attempt.id),
                "is_existing": True,
                "questions": existing_attempt.questions or [],
                "start_time": existing_attempt.start_time.isoformat() if existing_attempt.start_time else None,
                "time_limit": existing_attempt.time_limit or 30
            }, status=200)

        # No existing attempt, create a new one using start_test logic
        # Get all questions - try both Question models
        all_questions = []
        
        # First, try to get questions from exams.models.Question (linked to PracticeTest via category)
        try:
            all_questions = list(Question.objects(category=category))
            print(f"[get_or_create_test_attempt] Found {len(all_questions)} questions from exams.models.Question")
        except Exception as e:
            print(f"[get_or_create_test_attempt] No questions in exams.models.Question: {e}")
        
        # If no questions found, try questions.models.Question (linked to Course)
        if not all_questions and exam_id:
            try:
                from questions.models import Question as CourseQuestion
                from courses.models import Course
                course = Course.objects.get(id=ObjectId(exam_id))
                all_questions = list(CourseQuestion.objects(course=course).order_by('created_at'))
                print(f"[get_or_create_test_attempt] Found {len(all_questions)} questions from questions.models.Question")
            except Exception as e:
                print(f"[get_or_create_test_attempt] No questions in questions.models.Question: {e}")
        
        if not all_questions:
            return JsonResponse({
                "success": False, 
                "message": "No questions found for this test. Please add questions to the course or practice test."
            }, status=404)

        # Limit questions to the test's question count (if specified)
        question_limit = category.questions if category.questions > 0 else len(all_questions)

        # Shuffle question order randomly
        import random
        random.shuffle(all_questions)
        
        # Take only the limited number of questions
        selected_questions = all_questions[:question_limit]

        formatted_questions = []
        for q in selected_questions:
            # Process options
            processed_options = []
            try:
                if isinstance(q.options, str):
                    options_data = json.loads(q.options) if q.options else []
                else:
                    options_data = q.options or []
            except (json.JSONDecodeError, TypeError):
                options_data = []
            
            if isinstance(options_data, list):
                for opt in options_data:
                    if isinstance(opt, dict):
                        processed_options.append(opt)
                    elif isinstance(opt, str):
                        processed_options.append({'text': opt})
                    else:
                        processed_options.append({'text': str(opt)})
            
            # Process correct_answers
            processed_correct_answers = []
            try:
                if isinstance(q.correct_answers, str):
                    correct_answers_data = json.loads(q.correct_answers) if q.correct_answers else []
                else:
                    correct_answers_data = q.correct_answers or []
            except (json.JSONDecodeError, TypeError):
                correct_answers_data = []
            
            if isinstance(correct_answers_data, list):
                for ans in correct_answers_data:
                    if isinstance(ans, dict):
                        processed_correct_answers.append(ans)
                    elif isinstance(ans, str):
                        processed_correct_answers.append(ans)
                    else:
                        processed_correct_answers.append(str(ans))
            
            # Handle question_text - could be in different fields
            question_text = getattr(q, 'question_text', '') or getattr(q, 'question', '') or ""
            
            # Handle question_type - normalize to common format
            question_type = getattr(q, 'question_type', 'single')
            if question_type in ['MCQ', 'SINGLE', 'TRUE_FALSE']:
                # exams.models.Question format
                question_type = 'single' if question_type in ['SINGLE', 'TRUE_FALSE'] else 'multiple'
            elif question_type not in ['single', 'multiple']:
                question_type = 'single'  # Default
            
            formatted_questions.append({
                "id": str(q.id),
                "_id": str(q.id),  # For compatibility
                "question_id": str(q.id),  # For submit_test compatibility
                "question_text": question_text,
                "question_type": question_type,
                "options": processed_options,
                "correct_answers": processed_correct_answers,
                "marks": getattr(q, 'marks', 1),
                "explanation": getattr(q, 'explanation', '') or "",
                "tags": getattr(q, 'tags', []) or [],
            })

        # Calculate time_limit - handle both number and string formats
        time_limit = 30  # Default 30 minutes
        if category:
            duration = getattr(category, 'duration', None)
            if duration:
                if isinstance(duration, int):
                    time_limit = duration
                elif isinstance(duration, str):
                    # Extract number from string (e.g., "90 minutes" -> 90)
                    import re
                    match = re.search(r'\d+', duration)
                    if match:
                        time_limit = int(match.group())
        
        # Create new test attempt
        attempt = TestAttempt.objects.create(
            user=user_obj,
            exam=exam,
            category=category,
            questions=formatted_questions,
            total_marks=sum(q.marks for q in selected_questions),
            time_limit=time_limit,
            start_time=datetime.utcnow(),
            is_completed=False
        )

        return JsonResponse({
            "success": True,
            "attempt_id": str(attempt.id),
            "is_existing": False,
            "questions": formatted_questions,
            "start_time": attempt.start_time.isoformat() if attempt.start_time else None,
            "time_limit": attempt.time_limit or 30
        }, status=200)

    except User.DoesNotExist:
        # This should already be handled above, but keep as fallback
        print(f"[get_or_create_test_attempt] User.DoesNotExist: User ID not found")
        return JsonResponse({
            "success": False, 
            "message": "User account not found. Please log in again."
        }, status=404)
    except PracticeTest.DoesNotExist:
        print(f"[get_or_create_test_attempt] PracticeTest.DoesNotExist")
        return JsonResponse({"success": False, "message": "Practice test not found"}, status=404)
    except Exam.DoesNotExist:
        # This is okay - exam_id is a Course ID, not necessarily an Exam ID
        print(f"[get_or_create_test_attempt] Exam.DoesNotExist (this is okay, continuing...)")
        pass
    except json.JSONDecodeError as e:
        print(f"[get_or_create_test_attempt] JSONDecodeError: {e}")
        return JsonResponse({"success": False, "message": f"Invalid JSON in request body: {str(e)}"}, status=400)
    except ValueError as e:
        import traceback
        print(f"[get_or_create_test_attempt] ValueError: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": f"Invalid data format: {str(e)}"}, status=400)
    except KeyError as e:
        import traceback
        print(f"[get_or_create_test_attempt] KeyError: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": f"Missing required field: {str(e)}"}, status=400)
    except AttributeError as e:
        import traceback
        print(f"[get_or_create_test_attempt] AttributeError: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": f"Invalid object attribute: {str(e)}"}, status=400)
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[get_or_create_test_attempt] Unexpected error: {e}")
        print(error_trace)
        # Return a more detailed error message
        error_message = str(e) if str(e) else "An unexpected error occurred"
        return JsonResponse({
            "success": False, 
            "message": error_message,
            "error_type": type(e).__name__
        }, status=500)


