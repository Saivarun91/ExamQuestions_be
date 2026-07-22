import json
import io
import csv
import re
import random
import os
from datetime import datetime, timedelta
from bson import ObjectId

from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

from common.middleware import authenticate, restrict
from exams.models import Question
from exams.models import Exam
# from exams.models import TestAttempt
from categories.models import Category 
from users.models import User
from practice_tests.models import PracticeTest
from exams.models import Question, Exam, TestAttempt, QuestionBank
from practice_tests.models import PracticeTest


def _resolve_practice_test(test_id_raw, course_id_raw=None):
    """Resolve a PracticeTest from ObjectId, slug, or 1-based index within a course."""
    test_id_raw = str(test_id_raw or "").strip()
    if not test_id_raw:
        return None, "test_id (or category_id) is required"

    if ObjectId.is_valid(test_id_raw):
        try:
            return PracticeTest.objects.get(id=ObjectId(test_id_raw)), None
        except PracticeTest.DoesNotExist:
            return None, f"No PracticeTest found with ID: {test_id_raw}"

    course_oid = None
    if course_id_raw is not None:
        course_id_str = str(course_id_raw).strip()
        if ObjectId.is_valid(course_id_str):
            course_oid = ObjectId(course_id_str)

    if course_oid is not None:
        try:
            from courses.models import Course

            course = Course.objects.get(id=course_oid)
            practice_tests = list(getattr(course, "practice_tests", None) or [])
            for pt in practice_tests:
                if not pt:
                    continue
                if str(pt.id) == test_id_raw or getattr(pt, "slug", None) == test_id_raw:
                    return pt, None

            try:
                index = int(test_id_raw) - 1
                if 0 <= index < len(practice_tests) and practice_tests[index]:
                    return practice_tests[index], None
            except (TypeError, ValueError):
                pass
        except Exception:
            pass

    slug_matches = list(PracticeTest.objects(slug=test_id_raw))
    if len(slug_matches) == 1:
        return slug_matches[0], None

    return None, (
        "Invalid practice test id. Open the test from the course admin page, "
        "or send a valid 24-character test id with course_id."
    )


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

        # Normalize practice test id (Question.category references PracticeTest; API field name is legacy)
        cid = data.get("category_id")
        if cid is None or (isinstance(cid, str) and not cid.strip()):
            for key in ("test_id", "practice_test_id", "categoryId", "practiceTestId"):
                val = data.get(key)
                if val is not None and (not isinstance(val, str) or val.strip()):
                    data["category_id"] = val if not isinstance(val, str) else val.strip()
                    break

        # ✅ Required fields check
        required_fields = ["category_id", "question_type", "options", "correct_answers"]
        for field in required_fields:
            if field not in data or data[field] is None:
                return JsonResponse({"success": False, "message": f"{field} is required"}, status=400)
            if field == "category_id" and isinstance(data[field], str) and not data[field].strip():
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

        # ✅ Resolve PracticeTest (category_id is legacy; value may be ObjectId or slug when course_id is sent)
        category_id_raw = str(data['category_id']).strip()
        course_id_raw = data.get('course_id')
        category = None

        if ObjectId.is_valid(category_id_raw):
            try:
                category = PracticeTest.objects.get(id=ObjectId(category_id_raw))
            except PracticeTest.DoesNotExist:
                return JsonResponse({"success": False, "message": "PracticeTest not found"}, status=404)
        else:
            course_oid = None
            if course_id_raw is not None:
                cs = str(course_id_raw).strip()
                if ObjectId.is_valid(cs):
                    course_oid = ObjectId(cs)
            if course_oid is not None:
                try:
                    from courses.models import Course
                    course = Course.objects.get(id=course_oid)
                    for pt in getattr(course, 'practice_tests', None) or []:
                        if not pt:
                            continue
                        if str(pt.id) == category_id_raw or getattr(pt, 'slug', None) == category_id_raw:
                            category = pt
                            break
                except Exception:
                    category = None
            if category is None:
                pts = list(PracticeTest.objects(slug=category_id_raw))
                if len(pts) == 1:
                    category = pts[0]
            if category is None:
                return JsonResponse({
                    "success": False,
                    "message": "Invalid practice test id. Open the test from the course admin page, or send a valid 24-character test id with course_id so the server can match the test slug.",
                }, status=400)

        # ✅ Validate question: must have either text or image (or both); JSON may carry a remote image URL
        question_text = data.get('question_text', '').strip() if data.get('question_text') else ''
        question_image_file = request.FILES.get('question_image') if is_multipart else None
        question_image_url = ''
        if not is_multipart:
            qi = data.get('question_image')
            if isinstance(qi, str):
                question_image_url = qi.strip()

        if not question_text and not question_image_file and not question_image_url:
            return JsonResponse({
                "success": False,
                "message": "Either question_text or question_image must be provided"
            }, status=400)

        # ✅ Handle question image upload (multipart file or JSON URL e.g. Cloudinary)
        question_image = None
        question_image_content_type = None
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
            question_image_content_type = question_image_file.content_type
        elif question_image_url.startswith(('http://', 'https://')):
            try:
                import urllib.request
                req = urllib.request.Request(
                    question_image_url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                )
                with urllib.request.urlopen(req, timeout=45) as resp:
                    body = resp.read()
                if not body:
                    return JsonResponse({"success": False, "message": "Question image URL returned empty data"}, status=400)
                raw_ct = resp.headers.get('Content-Type') or 'image/jpeg'
                ctype = raw_ct.split(';')[0].strip() if raw_ct else 'image/jpeg'
                if not ctype or ctype == 'application/octet-stream':
                    ctype = 'image/jpeg'
                question_image = ContentFile(body)
                question_image.name = 'question_remote.jpg'
                question_image_content_type = ctype
            except Exception as e:
                return JsonResponse({
                    "success": False,
                    "message": f"Could not load question image from URL: {str(e)}"
                }, status=400)

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
        if (
            question_image_url
            and isinstance(question_image_url, str)
            and question_image_url.strip().startswith(("http://", "https://"))
        ):
            question.question_image_external_url = question_image_url.strip()[:2048]

        # Save question image if provided
        if question_image:
            ct = question_image_content_type or getattr(question_image, 'content_type', None) or 'application/octet-stream'
            question.question_image.put(question_image, content_type=ct)
        
        question.save()

        from courses.counts import refresh_course_counts_for_practice_test

        refresh_course_counts_for_practice_test(category)

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

        question = Question.objects(_id=ObjectId(question_id)).first()
        if not question:
            return JsonResponse({"success": False, "message": "Question not found"}, status=404)

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
            question.question_image_external_url = None

        elif not is_multipart and 'question_image' in data:
            qi = data.get('question_image')
            if isinstance(qi, str):
                qi = qi.strip()
            if isinstance(qi, str) and qi.startswith(('http://', 'https://')):
                own_a = f"/api/exams/questions/{question_id}/image/"
                own_b = f"/api/exams/questions/{str(question.id)}/image/"
                if own_a in qi or own_b in qi:
                    pass
                else:
                    try:
                        import urllib.request
                        req = urllib.request.Request(
                            qi,
                            headers={'User-Agent': 'Mozilla/5.0'},
                        )
                        with urllib.request.urlopen(req, timeout=45) as resp:
                            body = resp.read()
                        if body:
                            raw_ct = resp.headers.get('Content-Type') or 'image/jpeg'
                            ctype = raw_ct.split(';')[0].strip() if raw_ct else 'image/jpeg'
                            if not ctype or ctype == 'application/octet-stream':
                                ctype = 'image/jpeg'
                            cf = ContentFile(body)
                            cf.name = 'question_remote.jpg'
                            question.question_image.put(cf, content_type=ctype)
                            question.question_image_external_url = qi[:2048]
                    except Exception:
                        pass

        # Validate question: must have either text or image (or both)
        question_text = question.question_text.strip() if question.question_text else ''
        ext_u = getattr(question, 'question_image_external_url', None)
        qi_payload = None
        if not is_multipart:
            qiraw = data.get('question_image')
            if isinstance(qiraw, str) and qiraw.strip().startswith(('http://', 'https://')):
                qi_payload = qiraw.strip()
        has_question_image = bool(question.question_image) or (
            isinstance(ext_u, str) and ext_u.strip().startswith(('http://', 'https://'))
        ) or (isinstance(qi_payload, str) and qi_payload.startswith(('http://', 'https://')))

        if not question_text and not has_question_image:
            return JsonResponse({
                "success": False, 
                "message": "Either question_text or question_image must be provided"
            }, status=400)

        # Update other fields (normalize types MongoEngine expects)
        if 'question_type' in data:
            qt = str(data['question_type']).strip().upper()
            if qt in ('MULTIPLE',):
                qt = 'MCQ'
            if qt in ('SINGLE', 'MCQ', 'TRUE_FALSE'):
                question.question_type = qt
        if 'marks' in data:
            try:
                question.marks = int(data['marks'])
            except (TypeError, ValueError):
                question.marks = 1
        if 'explanation' in data:
            question.explanation = data.get('explanation') or ''
        if 'tags' in data:
            t = data['tags']
            if isinstance(t, str):
                question.tags = [x.strip() for x in t.split(',') if x.strip()]
            elif isinstance(t, list):
                question.tags = [str(x) for x in t if x is not None and str(x).strip() != '']
            else:
                question.tags = []

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

            # Use question.options (already replaced if this request included "options")
            current_options = list(question.options) if question.options else []

            # Convert correct answers to option identifiers
            processed_correct_answers = []
            n_opts = len(current_options)
            for ans in correct_answers:
                # If answer is an index (integer or string number) — support 0-based and 1-based
                if isinstance(ans, int) or (isinstance(ans, str) and str(ans).strip().isdigit()):
                    idx = int(str(ans).strip())
                    if 0 <= idx < n_opts:
                        processed_correct_answers.append(str(idx))
                    elif n_opts > 0 and 1 <= idx <= n_opts:
                        processed_correct_answers.append(str(idx - 1))
                    else:
                        return JsonResponse({
                            "success": False,
                            "message": f"Invalid correct answer index: {idx}"
                        }, status=400)
                else:
                    # Match by option text or image URL
                    found = False
                    ans_s = str(ans).strip()
                    for idx, opt in enumerate(current_options):
                        if isinstance(opt, dict):
                            opt_text = (opt.get('text') or '').strip()
                            opt_img = (opt.get('image_url') or opt.get('image') or '').strip()
                        elif isinstance(opt, str):
                            opt_text = opt.strip()
                            opt_img = ''
                        else:
                            opt_text = str(opt).strip()
                            opt_img = ''
                        if opt_text == ans_s or (opt_img and opt_img == ans_s):
                            processed_correct_answers.append(str(idx))
                            found = True
                            break
                    if not found:
                        processed_correct_answers.append(str(ans))
            
            question.correct_answers = processed_correct_answers

        question.updated_at = datetime.utcnow()
        question.save()

        from courses.counts import refresh_course_counts_for_practice_test

        refresh_course_counts_for_practice_test(question.category)

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

        practice_test = question.category

        # ✅ Delete question
        question.delete()

        from courses.counts import refresh_course_counts_for_practice_test

        refresh_course_counts_for_practice_test(practice_test)

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
        
        question = Question.objects(_id=ObjectId(question_id)).first()
        if not question:
            return JsonResponse({"success": False, "message": "Question not found"}, status=404)

        ext = getattr(question, "question_image_external_url", None)
        if (
            isinstance(ext, str)
            and ext.strip().startswith(("http://", "https://"))
        ):
            return HttpResponseRedirect(ext.strip())

        field = question.question_image
        if not field:
            return JsonResponse({"success": False, "message": "Question image not found"}, status=404)

        from django.http import HttpResponse
        try:
            if hasattr(field, "seek"):
                field.seek(0)
            image_data = field.read()
        except Exception:
            image_data = None

        if not image_data:
            return JsonResponse({"success": False, "message": "Question image not found"}, status=404)

        content_type = getattr(field, "content_type", None) or "image/jpeg"
        if not isinstance(content_type, str) or "/" not in content_type:
            content_type = "image/jpeg"
        response = HttpResponse(image_data, content_type=content_type)
        file_ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
        response['Content-Disposition'] = f'inline; filename="question_{question_id}.{file_ext}"'
        return response
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=404)


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

        question = Question.objects(_id=ObjectId(question_id)).first()
        if not question:
            return JsonResponse({"success": False, "message": "Question not found"}, status=404)

        # Prefer external HTTPS URL for admin / clients; else GridFS image endpoint
        question_image_url = None
        ext = getattr(question, "question_image_external_url", None)
        if (
            isinstance(ext, str)
            and ext.strip().startswith(("http://", "https://"))
        ):
            question_image_url = ext.strip()
        elif question.question_image:
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
        course_id = request.GET.get('course_id')
        id_to_check = test_id or category_id

        if not id_to_check:
            return JsonResponse({"success": False, "message": "category_id (or test_id) is required"}, status=400)

        practice_test, resolve_error = _resolve_practice_test(id_to_check, course_id)
        if resolve_error:
            return JsonResponse({"success": False, "message": resolve_error}, status=404 if "not found" in resolve_error.lower() else 400)

        # Filter questions by PracticeTest
        all_questions = list(Question.objects.filter(category=practice_test))
        
        # For admin view, show ALL questions (no limit, no shuffle)
        # The test limit is only used during actual test taking, not in admin view
        # Admin needs to see all uploaded questions to manage them
        questions = all_questions

        question_list = []
        for q in questions:
            # Prefer stored HTTPS URL (Cloudinary) for admin preview; else GridFS image endpoint
            question_image_url = None
            ext = getattr(q, "question_image_external_url", None)
            if (
                isinstance(ext, str)
                and ext.strip().startswith(("http://", "https://"))
            ):
                question_image_url = ext.strip()
            elif q.question_image:
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

        # Try to find PracticeTest first (if test_id is provided)
        practice_test = None
        test_category = None
        
        if test_id:
            practice_test, resolve_error = _resolve_practice_test(test_id, course_id)
            if resolve_error:
                status = 404 if "not found" in resolve_error.lower() else 400
                return JsonResponse({"success": False, "message": resolve_error}, status=status)
            if practice_test.category:
                test_category = practice_test.category
            elif practice_test.course and practice_test.course.category:
                test_category = practice_test.course.category
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
        try:
            raw = csv_file.read()
            # Try multiple encodings to handle different CSV formats
            csv_data = None
            for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    csv_data = raw.decode(encoding)
                    print(f"✅ CSV decoded with {encoding}")
                    break
                except (UnicodeDecodeError, AttributeError):
                    continue
            if not csv_data:
                return JsonResponse({
                    "success": False,
                    "message": "CSV encoding not supported. Please save the file as UTF-8."
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error reading CSV file: {str(e)}"
            }, status=400)
        
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
        try:
            csv_reader = csv.DictReader(io.StringIO(csv_data))
            # Check if CSV has required columns
            if not csv_reader.fieldnames:
                return JsonResponse({
                    "success": False,
                    "message": "CSV file appears to be empty or invalid"
                }, status=400)
        except Exception as e:
            return JsonResponse({
                "success": False,
                "message": f"Error parsing CSV file: {str(e)}"
            }, status=400)

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
        
        # Log CSV headers for debugging (first row only)
        if csv_rows and len(csv_rows) > 0:
            print(f"📋 CSV Headers found: {list(csv_rows[0].keys())}")

        # Calculate how many questions are still needed
        questions_needed = None
        if question_limit is not None:
            questions_needed = question_limit - current_question_count
            if questions_needed <= 0:
                # Already at or over limit, skip all rows
                questions_skipped = total_rows
                questions_needed = 0
            else:
                questions_skipped = 0
        else:
            questions_skipped = 0

        # If already at limit, skip processing all rows
        if questions_skipped == total_rows:
            # Skip the entire loop, all questions will be skipped
            pass
        else:
            for row_num, row in enumerate(csv_rows, start=1):
                # Check if we've already created enough questions to meet the limit
                if question_limit is not None and questions_needed is not None:
                    if questions_created >= questions_needed:
                        # We've created enough questions, skip the rest
                        questions_skipped = total_rows - row_num + 1
                        break  # Stop processing more rows
                
                try:
                    # Skip empty rows
                    if not any(v and str(v).strip() for v in row.values()):
                        continue
                    # Normalize row keys to lowercase for case-insensitive matching
                    row_normalized = {}
                    for k, v in row.items():
                        if k:  # Only process non-empty keys
                            key_normalized = k.strip().lower()
                            if v is None:
                                row_normalized[key_normalized] = ""
                            else:
                                row_normalized[key_normalized] = str(v).strip() if v else ""
                    
                    # Helper function to get value with multiple possible keys (case-insensitive)
                    def get_value(*keys):
                        for key in keys:
                            key_lower = key.lower()
                            if key_lower in row_normalized:
                                val = row_normalized[key_lower]
                                if val and str(val).strip():
                                    return str(val).strip()
                        return ""

                    # Expected columns: question_text, question_type, options, correct_answer/correct_answers
                    # Handle "Question" column (case-insensitive)
                    question_text = get_value("question_text", "question", "question text")
                    if not question_text:
                        # Debug: show available keys for first row
                        if row_num == 1:
                            print(f"🔍 Row 1 - Available keys: {list(row_normalized.keys())}")
                            print(f"🔍 Row 1 - Looking for 'question' in keys: {[k for k in row_normalized.keys() if 'question' in k]}")
                        raise ValueError("Missing 'Question' column. Please ensure your CSV has a 'Question' column.")
                    
                    question_type = get_value("question_type", "question type", "type", "qtype") or "single"
                    
                    # Handle both semicolon and pipe-separated options OR individual option columns
                    options_str = get_value("options", "option", "answer options")
                    options_raw = []
                    option_explanations = {}
                    
                    if options_str and str(options_str).strip():
                        # Try pipe separator first (most common)
                        if "|" in options_str:
                            options_raw = [opt.strip() for opt in options_str.split("|") if opt.strip()]
                        # Then try semicolon
                        elif ";" in options_str:
                            options_raw = [opt.strip() for opt in options_str.split(";") if opt.strip()]
                        # Finally try comma
                        elif "," in options_str:
                            options_raw = [opt.strip() for opt in options_str.split(",") if opt.strip()]
                        else:
                            # Single option
                            options_raw = [options_str.strip()]
                    else:
                        # Try individual option columns: "Answer Option 1", "Answer Option 2", etc. (numeric)
                        # AND "Answer Option A", "Answer Option B", etc. (letter-based)
                        # First try numeric format (1, 2, 3, 4, 5, 6)
                        for num in range(1, 7):  # Support up to 6 options
                            opt_val = get_value(
                                f"answer option {num}",
                                f"answer option{num}",
                                f"answer_option_{num}",
                                f"answer_option{num}",
                                f"option {num}",
                                f"option_{num}",
                                f"option{num}"
                            )
                            if opt_val:
                                options_raw.append(opt_val)
                                # Also get explanation if available
                                exp_val = get_value(
                                    f"explanation {num}",
                                    f"explanation_{num}",
                                    f"explanation{num}"
                                )
                                if exp_val:
                                    option_explanations[len(options_raw) - 1] = exp_val
                        
                        # If no numeric options found, try letter-based format (A, B, C, D, E, F)
                        if len(options_raw) == 0:
                            for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                                opt_val = get_value(
                                    f"answer option {letter}",
                                    f"answer option{letter}",
                                    f"answer_option_{letter}",
                                    f"answer_option{letter}",
                                    f"option {letter}",
                                    f"option_{letter}",
                                    f"option{letter}"
                                )
                                if opt_val:
                                    options_raw.append(opt_val)
                                    # Also get explanation if available
                                    exp_val = get_value(
                                        f"explanation {letter}",
                                        f"explanation_{letter}",
                                        f"explanation{letter}"
                                    )
                                    if exp_val:
                                        option_explanations[len(options_raw) - 1] = exp_val
                        
                        # Debug for first row
                        if row_num == 1:
                            print(f"🔍 Row 1 - Found {len(options_raw)} options from individual columns")
                            if len(options_raw) > 0:
                                print(f"🔍 Row 1 - First 3 options: {options_raw[:3]}")
                            else:
                                print(f"🔍 Row 1 - Available keys with 'option': {[k for k in row_normalized.keys() if 'option' in k]}")
                                # Show actual values for first 3 option columns (both numeric and letter)
                                for num in range(1, 4):
                                    key = f"answer option {num}"
                                    val = row_normalized.get(key, 'NOT FOUND')
                                    print(f"🔍 Row 1 - '{key}' = '{val}'")
                                for letter in ['A', 'B', 'C']:
                                    key = f"answer option {letter}"
                                    val = row_normalized.get(key, 'NOT FOUND')
                                    print(f"🔍 Row 1 - '{key}' = '{val}'")
                    
                    # Convert to list of dicts format required by Question model
                    options = []
                    for idx, opt in enumerate(options_raw):
                        if opt and str(opt).strip():
                            opt_dict = {"text": str(opt).strip()}
                            # Add explanation if available
                            if idx in option_explanations:
                                opt_dict["explanation"] = option_explanations[idx]
                            options.append(opt_dict)
                    
                    # Debug for first row
                    if row_num == 1:
                        print(f"🔍 Row 1 - Final options count: {len(options)}")
                        if len(options) > 0:
                            print(f"🔍 Row 1 - First option: {options[0]}")
                    
                    # Handle both correct_answer (singular) and correct_answers (plural)
                    correct_answer_str = get_value("correct_answers", "correct_answer", "correct answers", "correct answer", "answer")
                    
                    # Parse correct answers - handle both comma/pipe separated and single values
                    # Use string split instead of re.split to avoid scope issues
                    if "," in correct_answer_str or "|" in correct_answer_str:
                        # Split by pipe first, then by comma, and flatten
                        if "|" in correct_answer_str:
                            parts = correct_answer_str.split("|")
                            correct_answer_list = []
                            for part in parts:
                                if "," in part:
                                    correct_answer_list.extend([x.strip() for x in part.split(",") if x.strip()])
                                else:
                                    if part.strip():
                                        correct_answer_list.append(part.strip())
                        else:
                            correct_answer_list = [x.strip() for x in correct_answer_str.split(",") if x.strip()]
                    else:
                        correct_answer_list = [correct_answer_str.strip()] if correct_answer_str.strip() else []
                    
                    # Map letter answers (A, B, C, D) to option index or text
                    # Question model stores correct_answers as option indices (strings) or option text
                    correct_answers = []
                    for ans in correct_answer_list:
                        ans = ans.strip()
                        # Check if answer is a single letter (A, B, C, D, etc.)
                        if len(ans) == 1 and ans.isalpha():
                            # First, try direct letter-to-index mapping (A=0, B=1, C=2, D=3, E=4, F=5)
                            # This works when options are read from "Answer Option A", "Answer Option B" columns
                            letter_idx = ord(ans.upper()) - ord('A')
                            if 0 <= letter_idx < len(options):
                                correct_answers.append(str(letter_idx))
                                continue
                            
                            # If direct mapping didn't work, find the option index that starts with this letter
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
                                raise ValueError(f"Could not find option matching letter '{ans}'. Available options: {len(options)} options found")
                        elif ans.isdigit():
                            # If answer is a number, handle both 0-based and 1-based indexing
                            idx = int(ans)
                            # Try 1-based first (more common in CSV files: 1, 2, 3, 4)
                            if 1 <= idx <= len(options):
                                correct_answers.append(str(idx - 1))
                            # Then try 0-based (0, 1, 2, 3)
                            elif 0 <= idx < len(options):
                                correct_answers.append(str(idx))
                            else:
                                raise ValueError(f"Invalid option index: {idx} (valid range: 0-{len(options)-1} or 1-{len(options)})")
                        else:
                            # Answer is text - find matching option index (case-insensitive)
                            found = False
                            ans_lower = ans.lower().strip()
                            for idx, opt_dict in enumerate(options):
                                opt_text = opt_dict.get("text", "").strip()
                                opt_text_lower = opt_text.lower()
                                # Try exact match first
                                if opt_text_lower == ans_lower:
                                    correct_answers.append(str(idx))
                                    found = True
                                    break
                                # Try if answer is contained in option text
                                elif ans_lower in opt_text_lower:
                                    correct_answers.append(str(idx))
                                    found = True
                                    break
                                # Try if option text is contained in answer
                                elif opt_text_lower in ans_lower:
                                    correct_answers.append(str(idx))
                                    found = True
                                    break
                            if not found:
                                # Try matching by removing common prefixes
                                ans_clean = ans_lower.replace("option ", "").replace("answer ", "").strip()
                                for idx, opt_dict in enumerate(options):
                                    opt_text = opt_dict.get("text", "").strip().lower()
                                    opt_clean = opt_text.replace("option ", "").replace("answer ", "").strip()
                                    if opt_clean == ans_clean or ans_clean in opt_clean or opt_clean in ans_clean:
                                        correct_answers.append(str(idx))
                                        found = True
                                        break
                            if not found:
                                # Last resort: try matching by letter position (A=0, B=1, C=2, etc.)
                                if len(ans) == 1 and ans.isalpha():
                                    letter_idx = ord(ans.upper()) - ord('A')
                                    if 0 <= letter_idx < len(options):
                                        correct_answers.append(str(letter_idx))
                                        found = True
                            if not found:
                                raise ValueError(f"Could not find option matching answer '{ans}'. Available options: {[opt.get('text', '')[:50] for opt in options]}")
                    
                    marks = int(get_value("marks", "mark", "points") or "1")
                    explanation = get_value("explanation", "explain", "overall explanation", "overall_explanation")

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
                    
                    # Check test limit AFTER successfully creating a question
                    if question_limit is not None and questions_needed is not None:
                        # Check if we've created enough questions to meet the limit
                        if questions_created >= questions_needed:
                            # We've created enough questions, skip the rest
                            questions_skipped = total_rows - row_num
                            break  # Stop processing more rows
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    import traceback
                    print(f"❌ Error in row {row_num}: {str(e)}")
                    if row_num <= 3:  # Only print traceback for first 3 errors to avoid spam
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

            from courses.counts import refresh_course_counts_for_practice_test

            practice_test.reload()
            refresh_course_counts_for_practice_test(practice_test)

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
            access_type = getattr(course_obj, 'pricing_access_type', None) or 'paid'
            if str(access_type).lower() == 'free':
                enrolled = True
            else:
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
                    question_obj = Question.objects(_id=ObjectId(str(question_id))).first()
                    if question_obj:
                        tags = getattr(question_obj, 'tags', []) or []
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
        questions = []
        for qid in question_ids:
            if not ObjectId.is_valid(str(qid)):
                return JsonResponse(
                    {"success": False, "message": f"Invalid question ID: {qid}"},
                    status=400,
                )
            q = Question.objects(_id=ObjectId(str(qid))).first()
            if not q:
                return JsonResponse(
                    {"success": False, "message": f"Question not found: {qid}"},
                    status=404,
                )
            questions.append(q)

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
                        # Try to find by slug without ObjectId hash (e.g., "test-name" matches "test-name-694e3de3")
                        import re
                        slug_pattern = re.compile(f"^{re.escape(test_id)}(-[a-f0-9]{{8}})?$", re.IGNORECASE)
                        category = PracticeTest.objects(course=course).filter(slug=slug_pattern).first()
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


@csrf_exempt
@authenticate
def claim_guest_test_attempt(request):
    """
    Persist a guest (local) completed practice attempt against the logged-in user
    so results are saved and visible in admin.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not request.body:
            return JsonResponse({"success": False, "message": "Request body is empty"}, status=400)

        data = json.loads(request.body)
        user_id = request.user.get("id") if isinstance(request.user, dict) else None
        if not user_id or not ObjectId.is_valid(str(user_id)):
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        try:
            user_obj = User.objects.get(id=ObjectId(str(user_id)))
        except User.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"}, status=404)

        exam_id = data.get("exam_id")
        test_id = data.get("test_id") or data.get("category_id")
        user_answers = data.get("user_answers") or []
        questions_snapshot = data.get("questions_snapshot") or []
        score = float(data.get("score") or 0)
        total_marks = int(data.get("total_marks") or len(user_answers) or len(questions_snapshot) or 0)
        percentage = float(data.get("percentage") or 0)
        time_limit = int(data.get("time_limit") or 30)
        start_time_raw = data.get("start_time")

        category, err = _resolve_practice_test(test_id, exam_id)
        if err or not category:
            # Fallback: try get_or_create-style resolution via course practice tests
            if exam_id and ObjectId.is_valid(str(exam_id)) and test_id:
                try:
                    from courses.models import Course
                    course = Course.objects.get(id=ObjectId(str(exam_id)))
                    all_course_tests = list(PracticeTest.objects(course=course).order_by("created_at"))
                    if ObjectId.is_valid(str(test_id)):
                        category = PracticeTest.objects.get(id=ObjectId(str(test_id)))
                    else:
                        try:
                            idx = int(test_id) - 1
                            if 0 <= idx < len(all_course_tests):
                                category = all_course_tests[idx]
                        except (TypeError, ValueError):
                            category = PracticeTest.objects(slug=str(test_id), course=course).first()
                except Exception:
                    category = None
            if not category:
                return JsonResponse(
                    {"success": False, "message": err or "Practice test not found"},
                    status=404,
                )

        exam = None
        if exam_id and ObjectId.is_valid(str(exam_id)):
            try:
                exam = Exam.objects.get(id=ObjectId(str(exam_id)))
            except Exam.DoesNotExist:
                exam = None

        start_time = datetime.utcnow()
        if start_time_raw:
            try:
                start_time = datetime.fromisoformat(str(start_time_raw).replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                start_time = datetime.utcnow()

        end_time = datetime.utcnow()
        duration_taken = max(0, int((end_time - start_time).total_seconds() / 60))

        # Build questions list for the attempt
        answers_by_qid = {
            str(a.get("question_id")): a.get("selected_answers") or []
            for a in user_answers
            if a.get("question_id")
        }

        attempt_questions = []
        if questions_snapshot:
            for q in questions_snapshot:
                qid = str(q.get("question_id") or q.get("id") or q.get("_id") or "")
                attempt_questions.append({
                    "question_id": qid,
                    "question_text": q.get("question_text") or "",
                    "marks": q.get("marks") or 1,
                    "user_selected_answers": answers_by_qid.get(qid, []),
                    "is_correct": False,
                    "marks_awarded": 0,
                })
        else:
            for a in user_answers:
                qid = str(a.get("question_id") or "")
                attempt_questions.append({
                    "question_id": qid,
                    "marks": 1,
                    "user_selected_answers": a.get("selected_answers") or [],
                    "is_correct": False,
                    "marks_awarded": 0,
                })

        if total_marks <= 0:
            total_marks = max(len(attempt_questions), 1)
        if percentage <= 0 and total_marks > 0:
            percentage = round((score / total_marks) * 100, 2)

        # Determine pass/fail server-side, same rules as submit_test:
        # category passing_score -> exam passing_score -> 60% default.
        passing_score = getattr(category, "passing_score", None)
        if passing_score is None and exam:
            passing_score = getattr(exam, "passing_score", None)
        try:
            passing_score = float(passing_score)
            if passing_score <= 0 or passing_score > 100:
                passing_score = 60.0
        except (TypeError, ValueError):
            passing_score = 60.0
        passed = percentage >= passing_score

        attempt = TestAttempt.objects.create(
            user=user_obj,
            exam=exam,
            category=category,
            questions=attempt_questions,
            user_answers=user_answers,
            score=score,
            total_marks=total_marks,
            percentage=percentage,
            passed=passed,
            start_time=start_time,
            end_time=end_time,
            duration_taken=duration_taken,
            time_limit=time_limit,
            is_time_up=False,
            is_completed=True,
            is_trial=True,
        )

        return JsonResponse({
            "success": True,
            "attempt_id": str(attempt.id),
            "score": attempt.score,
            "total_marks": attempt.total_marks,
            "percentage": attempt.percentage,
            "passed": attempt.passed,
        }, status=200)
    except json.JSONDecodeError as e:
        return JsonResponse({"success": False, "message": f"Invalid JSON: {str(e)}"}, status=400)
    except Exception as e:
        import traceback
        print(f"[claim_guest_test_attempt] error: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def _iso_utc(dt):
    """Serialize a (naive-UTC) datetime with an explicit UTC offset so browsers
    convert it to the viewer's local time instead of misreading it as local."""
    if not dt:
        return None
    try:
        iso = dt.isoformat()
        # Model datetimes are stored as naive UTC; add the offset if missing.
        if dt.tzinfo is None:
            iso += "+00:00"
        return iso
    except Exception:
        return None


@csrf_exempt
@authenticate
@restrict(["admin"])
def list_test_attempts(request):
    """
    Admin: list users who took practice tests (completed attempts) with user details.
    Optional query params: exam_id, test_id/category_id, search, page, page_size.
    Response includes an `exams` summary (attempt + unique member counts per exam)
    for building filters.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        exam_id = (request.GET.get("exam_id") or "").strip()
        test_id = (request.GET.get("test_id") or request.GET.get("category_id") or "").strip()
        search = (request.GET.get("search") or "").strip().lower()
        try:
            page = max(1, int(request.GET.get("page") or 1))
        except (TypeError, ValueError):
            page = 1
        try:
            page_size = min(100, max(1, int(request.GET.get("page_size") or 50)))
        except (TypeError, ValueError):
            page_size = 50

        query = {"is_completed": True}
        if test_id:
            category, _err = _resolve_practice_test(test_id, exam_id or None)
            if category:
                query["category"] = category.id

        # Exam filtering happens on the built rows (below) because the exam is
        # usually linked through category.course, not the attempt.exam field.
        # Heavy per-question payloads are excluded and every reference is
        # batch-fetched once (instead of N+1 dereference queries per attempt).
        def _ref_id(value):
            if value is None:
                return None
            ref = getattr(value, "id", value)  # DBRef -> ObjectId
            return ref if isinstance(ref, ObjectId) else None

        attempts_raw = [
            a.to_mongo().to_dict()
            for a in TestAttempt.objects(**query)
            .no_dereference()
            .exclude("questions", "user_answers")
            .order_by("-end_time", "-created_at")
        ]

        user_ids = {_ref_id(r.get("user")) for r in attempts_raw} - {None}
        category_ids = {_ref_id(r.get("category")) for r in attempts_raw} - {None}

        users_map = {}
        if user_ids:
            for u in User.objects(id__in=list(user_ids)).only("fullname", "email"):
                users_map[str(u.id)] = {
                    "name": getattr(u, "fullname", None) or u.email or "Unknown",
                    "email": u.email or "",
                }

        categories_map = {}
        course_ids = set()
        if category_ids:
            for c in (
                PracticeTest.objects(id__in=list(category_ids))
                .no_dereference()
                .only("title", "course")
            ):
                raw_c = c.to_mongo().to_dict()
                course_oid = _ref_id(raw_c.get("course"))
                if course_oid:
                    course_ids.add(course_oid)
                categories_map[str(raw_c.get("_id"))] = {
                    "title": raw_c.get("title") or "",
                    "course_id": str(course_oid) if course_oid else "",
                }

        courses_map = {}
        if course_ids:
            from courses.models import Course
            for co in Course.objects(id__in=list(course_ids)).only("title", "code"):
                courses_map[str(co.id)] = {
                    "title": getattr(co, "title", None) or getattr(co, "name", None) or "",
                    "code": getattr(co, "code", None) or "",
                }

        rows = []
        for raw in attempts_raw:
            uid = _ref_id(raw.get("user"))
            user_info = users_map.get(str(uid)) if uid else None
            user_id_str = str(uid) if uid else ""
            user_name = user_info["name"] if user_info else "Unknown"
            user_email = user_info["email"] if user_info else ""

            if search:
                hay = f"{user_name} {user_email}".lower()
                if search not in hay:
                    continue

            cat_oid = _ref_id(raw.get("category"))
            cat_info = categories_map.get(str(cat_oid)) if cat_oid else None
            test_name = cat_info["title"] if cat_info else ""
            test_id_out = str(cat_oid) if cat_oid else ""
            course_id = cat_info["course_id"] if cat_info else ""
            course_info = courses_map.get(course_id) if course_id else None
            exam_title = course_info["title"] if course_info else ""
            exam_code = course_info["code"] if course_info else ""

            exam_oid = _ref_id(raw.get("exam"))

            rows.append({
                "id": str(raw.get("_id")),
                "user_id": user_id_str,
                "user_name": user_name,
                "user_email": user_email,
                "exam_id": course_id or (str(exam_oid) if exam_oid else ""),
                "exam_title": exam_title,
                "exam_code": exam_code,
                "test_id": test_id_out,
                "test_name": test_name,
                "score": raw.get("score") or 0,
                "total_marks": raw.get("total_marks") or 0,
                "percentage": round(float(raw.get("percentage") or 0), 2),
                "passed": bool(raw.get("passed")),
                "is_trial": bool(raw.get("is_trial")),
                "duration_taken": raw.get("duration_taken"),
                "started_at": _iso_utc(raw.get("start_time")),
                "completed_at": _iso_utc(raw.get("end_time")),
                "created_at": _iso_utc(raw.get("created_at")),
            })

        # Per-exam summary (attempt counts + unique members) computed before the
        # exam filter so the filter dropdown always shows every exam.
        exam_summary = {}
        for row in rows:
            key = row["exam_id"] or "unknown"
            if key not in exam_summary:
                exam_summary[key] = {
                    "exam_id": row["exam_id"],
                    "exam_title": row["exam_title"] or "Unknown Exam",
                    "exam_code": row["exam_code"],
                    "attempts": 0,
                    "members": set(),
                }
            exam_summary[key]["attempts"] += 1
            member_key = row["user_id"] or row["user_email"] or row["user_name"]
            if member_key:
                exam_summary[key]["members"].add(member_key)

        exams_out = sorted(
            (
                {
                    "exam_id": v["exam_id"],
                    "exam_title": v["exam_title"],
                    "exam_code": v["exam_code"],
                    "attempts": v["attempts"],
                    "members": len(v["members"]),
                }
                for v in exam_summary.values()
            ),
            key=lambda x: (-x["attempts"], x["exam_title"].lower()),
        )

        if exam_id:
            rows = [r for r in rows if r["exam_id"] == exam_id]

        total = len(rows)
        unique_members = len({
            (r["user_id"] or r["user_email"] or r["user_name"]) for r in rows
        }) if rows else 0
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = rows[start:end]

        return JsonResponse({
            "success": True,
            "data": page_rows,
            "total": total,
            "unique_members": unique_members,
            "page": page,
            "page_size": page_size,
            "exams": exams_out,
        }, status=200)
    except Exception as e:
        import traceback
        print(f"[list_test_attempts] error: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(["admin"])
def delete_test_attempt(request, attempt_id):
    """Admin: delete a test attempt record."""
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(attempt_id):
            return JsonResponse({"success": False, "message": "Invalid attempt ID"}, status=400)

        try:
            attempt = TestAttempt.objects.get(_id=ObjectId(attempt_id))
        except TestAttempt.DoesNotExist:
            return JsonResponse({"success": False, "message": "Attempt not found"}, status=404)

        attempt.delete()
        return JsonResponse({"success": True, "message": "Attempt deleted"}, status=200)
    except Exception as e:
        import traceback
        print(f"[delete_test_attempt] error: {e}")
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)

