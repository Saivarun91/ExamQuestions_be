from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import PracticeTest
from categories.models import Category
from courses.models import Course
from courses.counts import sync_course_counts
from .serializers import PracticeTestSerializer


# ✅ Get all tests
@api_view(["GET"])
@permission_classes([AllowAny])
def get_all_tests(request):
    """
    Fetch all practice tests. If any test has an invalid category reference,
    it will be skipped (to avoid 500 errors).
    """
    valid_tests = []
    for test in PracticeTest.objects:
        try:
            _ = test.category.id  # try to access to ensure category exists
            valid_tests.append(test)
        except Exception:
            # skip broken references
            continue

    serializer = PracticeTestSerializer(valid_tests, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ✅ Get a single test by slug or ID
@api_view(["GET"])
@permission_classes([AllowAny])
def get_test_by_slug(request, slug):
    """
    Fetch a specific practice test by its slug or ID.
    Supports both ObjectId and slug for backward compatibility.
    """
    from bson import ObjectId
    
    # Try to find by ObjectId first, then by slug
    test = None
    if ObjectId.is_valid(slug):
        try:
            test = PracticeTest.objects(id=ObjectId(slug)).first()
        except:
            pass
    
    if not test:
        test = PracticeTest.objects(slug=slug).first()
    
    if not test:
        return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

    # Expand course and category references
    test_data = {
        "id": str(test.id),
        "title": test.title,
        "slug": test.slug,
        "questions": test.questions,
        "duration": test.duration,
        "avg_score": test.avg_score,
        "attempts": test.attempts,
        "free_trial_questions": test.free_trial_questions,
        "overview": test.overview or "",
        "instructions": test.instructions or "",
        "test_format": test.test_format or "",
        "duration_info": test.duration_info or "",
        "total_questions_info": test.total_questions_info or "",
        "language": test.language or "English",
        "difficulty_level": test.difficulty_level or "Medium",
        "test_type": test.test_type or "Practice Test",
        "additional_info": test.additional_info or "",
        "meta_title": test.meta_title or "",
        "meta_keywords": test.meta_keywords or "",
        "meta_description": test.meta_description or "",
    }
    
    # Add course info if available
    if test.course:
        try:
            course_obj = test.course
            test_data["course"] = {
                "id": str(course_obj.id),
                "name": course_obj.name,
            }
        except:
            pass
    
    # Add category info if available
    if test.category:
        try:
            category_obj = test.category
            test_data["category"] = {
                "id": str(category_obj.id),
                "name": category_obj.name,
            }
        except:
            pass

    return Response(test_data, status=status.HTTP_200_OK)


# ✅ Create a new test
@api_view(["POST"])
def create_test(request):
    """
    Create a new practice test. The request must include a valid `course_id` (preferred) or `category_id` (for backward compatibility).
    Example:
    {
        "slug": "web-dev-basics",
        "title": "Web Development Basics",
        "course_id": "671ffb12abc12345def67890",
        "questions": 10,
        "duration": 30
    }
    """
    course_id = request.data.get("course_id")
    category_id = request.data.get("category_id")  # For backward compatibility
    
    # Validate required fields
    title = request.data.get("title")
    slug = request.data.get("slug")
    questions = request.data.get("questions")
    duration = request.data.get("duration")
    
    if not title:
        return Response({"error": "title is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Prefer course_id over category_id
    course = None
    category = None
    
    if course_id:
        try:
            from bson import ObjectId
            if not ObjectId.is_valid(course_id):
                return Response({"error": f"Invalid course_id format: {course_id}"}, status=status.HTTP_400_BAD_REQUEST)
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({"error": f"Course with id '{course_id}' not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error fetching course: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    elif category_id:
        try:
            from bson import ObjectId
            if not ObjectId.is_valid(category_id):
                return Response({"error": f"Invalid category_id format: {category_id}"}, status=status.HTTP_400_BAD_REQUEST)
            category = Category.objects.get(id=category_id)
        except Category.DoesNotExist:
            return Response({"error": f"Category with id '{category_id}' not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"Error fetching category: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # course_id is now required (category_id kept for backward compatibility but course_id is preferred)
        return Response({"error": "course_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Auto-generate slug from title if not provided
    if not slug:
        from practice_tests.slug_utils import allocate_practice_test_slug
        slug = allocate_practice_test_slug(title, course)
    else:
        from practice_tests.slug_utils import allocate_practice_test_slug, _slug_taken
        slug = str(slug).strip()
        if _slug_taken(slug):
            slug = allocate_practice_test_slug(slug, course)
    
    # Create test directly using the model
    # Retry logic for handling duplicate slugs
    max_retries = 10
    retry_count = 0
    original_slug = slug
    
    while retry_count < max_retries:
        try:
            free_trial_questions = request.data.get("free_trial_questions")
            test = PracticeTest(
                slug=slug,
                title=title,
                questions=int(questions) if questions else 0,
                duration=int(duration) if duration else 0,
                free_trial_questions=int(free_trial_questions) if free_trial_questions else 10,
            )
            
            # Set reference fields
            if course:
                test.course = course
            elif category:
                test.category = category
                
            # Validate before saving
            test.validate()
            test.save()
            
            # Auto-update question count from existing questions ONLY if not provided by admin
            # If admin sets questions=20, that's the limit (how many to show from CSV)
            # If not provided, default to the total count of questions
            if not questions or questions == 0:
                from exams.models import Question
                question_count = Question.objects(category=test).count()
                test.questions = question_count
                test.save()
            
            if course:
                sync_course_counts(course)
            
            # Serialize the created test for response
            serializer = PracticeTestSerializer(test)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            error_message = str(e)
            
            # Check if it's a duplicate/unique error
            if ("duplicate" in error_message.lower() or 
                "unique" in error_message.lower() or 
                "E11000" in error_message or
                "not unique" in error_message.lower()):
                
                # Generate a new unique slug and retry
                retry_count += 1
                if retry_count < max_retries:
                    from bson import ObjectId
                    # Append a unique identifier to make slug unique
                    slug = f"{original_slug}-{ObjectId()}"
                    continue
                else:
                    # If max retries reached, return error
                    return Response(
                        {"error": "Failed to create test after multiple attempts. Please try again."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                # For other errors, return immediately
                import traceback
                error_trace = traceback.format_exc()
                print(f"Error creating test: {error_trace}")
                
                if "validation" in error_message.lower():
                    error_message = f"Validation error: {error_message}"
                
                return Response(
                    {
                        "error": error_message,
                        "details": error_trace
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
    
    # Should not reach here, but just in case
    return Response(
        {"error": "Failed to create test. Please try again."},
        status=status.HTTP_400_BAD_REQUEST
    )


# ✅ Update an existing test
@api_view(["PUT"])
def update_test(request, slug):
    """
    Update details of a specific practice test.
    You can also update its category by passing `category_id`.
    Accepts both slug and ObjectId.
    """
    from bson import ObjectId
    
    # Try to find by ObjectId first, then by slug
    test = None
    if ObjectId.is_valid(slug):
        try:
            test = PracticeTest.objects(id=ObjectId(slug)).first()
        except:
            pass
    
    if not test:
        test = PracticeTest.objects(slug=slug).first()
    
    if not test:
        return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()

    # Handle category update if provided
    category_id = data.get("category_id")
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            data["category"] = category
        except Category.DoesNotExist:
            return Response({"error": "Invalid category_id"}, status=status.HTTP_404_NOT_FOUND)

    serializer = PracticeTestSerializer(test, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        
        if test.course:
            sync_course_counts(test.course)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ✅ Delete a test
@api_view(["DELETE"])
def delete_test(request, slug):
    """
    Delete a specific practice test.
    Accepts both slug and ObjectId.
    """
    from bson import ObjectId
    
    # Try to find by ObjectId first, then by slug
    test = None
    if ObjectId.is_valid(slug):
        try:
            test = PracticeTest.objects(id=ObjectId(slug)).first()
        except Exception:
            pass
    
    if not test:
        test = PracticeTest.objects(slug=slug).first()
    
    if not test:
        return Response({"error": "Test not found"}, status=status.HTTP_404_NOT_FOUND)

    course_ref = None
    try:
        course_ref = test.course if getattr(test, "course", None) else None
    except Exception:
        course_ref = None

    test_id = str(test.id)
    test.delete()

    # Remove dangling reference from the course's practice_tests list
    if course_ref is not None:
        try:
            refs = list(getattr(course_ref, "practice_tests", None) or [])
            cleaned = []
            for ref in refs:
                try:
                    if ref and str(ref.id) != test_id:
                        cleaned.append(ref)
                except Exception:
                    continue
            course_ref.practice_tests = cleaned
            try:
                sync_course_counts(course_ref, save=False)
            except TypeError:
                # Older signature without save kwarg
                sync_course_counts(course_ref)
            course_ref.save()
        except Exception as e:
            print(f"Error updating course after test deletion: {e}")
            try:
                sync_course_counts(course_ref)
            except Exception as sync_err:
                print(f"Error updating course counts after test deletion: {sync_err}")
    
    return Response(
        {"success": True, "message": "Test deleted successfully"},
        status=status.HTTP_200_OK,
    )


# ✅ Get tests by category (for backward compatibility)
@api_view(["GET"])
@permission_classes([AllowAny])
def tests_by_category(request, category_id):
    """
    Get all tests belonging to a specific category (backward compatibility).
    Calculates avg_score and attempts from TestAttempt data.
    """
    try:
        from bson import ObjectId
        from exams.models import TestAttempt
        
        category = Category.objects.get(id=category_id)
    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)

    tests = PracticeTest.objects(category=category)
    serializer = PracticeTestSerializer(tests, many=True)
    test_data = serializer.data
    
    # Calculate avg_score and attempts for each test
    for test_item in test_data:
        # Handle different ID formats from serializer
        test_id = None
        if 'id' in test_item:
            test_id = test_item['id']
        elif '_id' in test_item:
            if isinstance(test_item['_id'], dict) and '$oid' in test_item['_id']:
                test_id = test_item['_id']['$oid']
            elif isinstance(test_item['_id'], str):
                test_id = test_item['_id']
        
        if not test_id or not ObjectId.is_valid(str(test_id)):
            test_item['attempts'] = 0
            test_item['avg_score'] = 0
            continue
            
        try:
            # Get all completed attempts for this test
            attempts = TestAttempt.objects(
                category=ObjectId(test_id),
                is_completed=True
            )
            
            # Calculate attempts count
            attempts_count = attempts.count()
            test_item['attempts'] = attempts_count
            
            # Calculate average score
            if attempts_count > 0:
                total_percentage = sum(attempt.percentage for attempt in attempts)
                avg_score = round(total_percentage / attempts_count, 2)
                test_item['avg_score'] = avg_score
            else:
                test_item['avg_score'] = 0
        except Exception as e:
            print(f"Error calculating stats for test {test_id}: {e}")
            test_item['attempts'] = 0
            test_item['avg_score'] = 0
    
    return Response(test_data, status=status.HTTP_200_OK)


# ✅ Get tests by course
@api_view(["GET"])
@permission_classes([AllowAny])
def tests_by_course(request, course_id):
    """
    Get all tests belonging to a specific course.
    Calculates avg_score and attempts from TestAttempt data.
    """
    try:
        from bson import ObjectId
        from exams.models import TestAttempt
        
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)

    tests = PracticeTest.objects(course=course)
    serializer = PracticeTestSerializer(tests, many=True)
    test_data = serializer.data
    
    # Calculate avg_score and attempts for each test
    for test_item in test_data:
        # Handle different ID formats from serializer
        test_id = None
        if 'id' in test_item:
            test_id = test_item['id']
        elif '_id' in test_item:
            if isinstance(test_item['_id'], dict) and '$oid' in test_item['_id']:
                test_id = test_item['_id']['$oid']
            elif isinstance(test_item['_id'], str):
                test_id = test_item['_id']
        
        if not test_id or not ObjectId.is_valid(str(test_id)):
            test_item['attempts'] = 0
            test_item['avg_score'] = 0
            continue
            
        try:
            # Get all completed attempts for this test
            attempts = TestAttempt.objects(
                category=ObjectId(test_id),
                is_completed=True
            )
            
            # Calculate attempts count
            attempts_count = attempts.count()
            test_item['attempts'] = attempts_count
            
            # Calculate average score
            if attempts_count > 0:
                total_percentage = sum(attempt.percentage for attempt in attempts)
                avg_score = round(total_percentage / attempts_count, 2)
                test_item['avg_score'] = avg_score
            else:
                test_item['avg_score'] = 0
        except Exception as e:
            print(f"Error calculating stats for test {test_id}: {e}")
            test_item['attempts'] = 0
            test_item['avg_score'] = 0
    
    return Response(test_data, status=status.HTTP_200_OK)
