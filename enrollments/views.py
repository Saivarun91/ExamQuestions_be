# # import json
# # from rest_framework.response import Response
# # from rest_framework import status
# # from .serializers import EnrollmentSerializer
# # from django.http import JsonResponse
# # from bson import ObjectId
# # from bson.errors import InvalidId
# # from common.middleware import authenticate
# # from django.views.decorators.csrf import csrf_exempt
# # from .models import Enrollment  
# # from users.models import User

# # @csrf_exempt
# # @authenticate
# # def create_enrollment(request):
# #     """Create a new enrollment."""
# #     if request.method != "POST":
# #         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

# #     try:
# #         data = json.loads(request.body)
# #         userId = request.user['id']  # from authenticate decorator
# #         user = User.Objects.get(id=userId)
# #         user_name = user.get("fullname")

# #         # Inject user_name into data for serializer
# #         data["user_name"] = user_name

# #         serializer = EnrollmentSerializer(data=data)
# #         if serializer.is_valid():
# #             enrollment = serializer.save()
# #             return JsonResponse({
# #                 "success": True,
# #                 "message": "Enrollment created successfully.",
# #                 "data": {
# #                     "id": str(enrollment.id),
# #                     "user_name": enrollment.user_name,
# #                     "course_name": enrollment.course_name,
# #                     "duration_months": enrollment.duration_months,
# #                     "enrolled_date": str(enrollment.enrolled_date),
# #                     "expiry_date": str(enrollment.expiry_date),
# #                 }
# #             }, status=201)

# #         return JsonResponse({
# #             "success": False,
# #             "message": "Invalid data",
# #             "errors": serializer.errors
# #         }, status=400)

# #     except Exception as e:
# #         print(e)
# #         return JsonResponse({
# #             "success": False,
# #             "message": "An error occurred while creating enrollment",
# #             "error": str(e)
# #         }, status=500)

# import json
# from rest_framework.response import Response
# from rest_framework import status
# from django.http import JsonResponse
# from bson import ObjectId
# from bson.errors import InvalidId
# from common.middleware import authenticate
# from django.views.decorators.csrf import csrf_exempt
# from .serializers import EnrollmentSerializer
# from .models import Enrollment  
# import datetime
# from users.models import User
# from practice_tests.models import PracticeTest




# @csrf_exempt
# @authenticate
# def create_enrollment(request):
#     """Create a new enrollment (only if not already enrolled)."""
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         user_id = request.user.get("id")
#         data = json.loads(request.body)
#         category_id = data.get("category_id")   # ✅ category id from frontend
#         print(category_id)
#         duration_months = data.get("duration_months")
#         print(duration_months)
#         if not category_id or not duration_months:
#             return JsonResponse({"success": False, "message": "Missing fields"}, status=400)

#         # ✅ Find the category
#         from categories.models import Category
#         category = Category.objects(id=ObjectId(category_id)).first()
#         if not category:
#             return JsonResponse({"success": False, "message": "Category not found"}, status=404)

#         # ✅ Check if already enrolled
#         existing = Enrollment.objects(user_name=user_id, category=category).first()
#         if existing:
#             return JsonResponse({
#                 "success": False,
#                 "message": "You are already enrolled in this course!"
#             }, status=400)

#         # ✅ Create new enrollment
#         enrolled_date = datetime.date.today()
#         expiry_date = enrolled_date + datetime.timedelta(days=30 * int(duration_months))

#         enrollment = Enrollment(
#             user_name=user_id,
#             category=category,
#             duration_months=duration_months,
#             enrolled_date=enrolled_date,
#             expiry_date=expiry_date
#         )
#         enrollment.save()

#         # ✅ Optionally link course to user (if you maintain that)
#         user = User.objects(id=ObjectId(user_id)).first()
#         if user:
#             user.enrolled_courses.append(category)  # now category instead of course_name
#             user.save()

#         return JsonResponse({
#             "success": True,
#             "message": "Enrollment successful",
#             "data": {
#                 "id": str(enrollment.id),
#                 "user_name": user.fullname if user else user_id,
#                 "category": {
#                     "id": str(category.id),
#                     "name": category.name
#                 },
#                 "duration_months": enrollment.duration_months,
#                 "enrolled_date": str(enrollment.enrolled_date),
#                 "expiry_date": str(enrollment.expiry_date)
#             }
#         })

#     except Exception as e:
#         print("❌ Enrollment error:", e)
#         return JsonResponse({"success": False, "message": str(e)}, status=500)




# @csrf_exempt
# @authenticate
# def check_enrollment(request, category_id):
#     """
#     Check if the logged-in user is already enrolled in the given TestCategory.
#     Uses the 'enrolled_courses' list in the User model.
#     """
#     if request.method != "GET":
#         return JsonResponse(
#             {"success": False, "message": "Method not allowed"},
#             status=405
#         )

#     try:
#         # ✅ Always treat category_id as a string
#         course_id = str(category_id)

#         # ✅ Get authenticated user info
#         user_data = request.user
#         userId = request.user['id']
#         print(userId)
#         user = User.objects.get(id=userId)
#         if not user:
#             return JsonResponse(
#                 {"already_enrolled": False, "error": "User not found"},
#                 status=404
#             )

#         # ✅ Check if the category ID exists in enrolled_courses
#         enrolled = any(str(course.id) == course_id for course in user.enrolled_courses)

#         return JsonResponse({"already_enrolled": enrolled}, status=200)

#     except Exception as e:
#         # ✅ Handle all errors safely
#         return JsonResponse(
#             {"already_enrolled": False, "error": str(e)},
#             status=200
#         )


# @csrf_exempt
# @authenticate
# def check_enrollment(request, category_id):
#     """
#     ✅ Check if user is enrolled in a course by checking user.enrolled_courses references.
#     """
#     if request.method != "GET":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         user_data = request.user or {}
#         user_id = user_data.get("id")

#         if not user_name:
#             return JsonResponse({"already_enrolled": False, "error": "Invalid user"}, status=401)

#         # ✅ Fetch user object
#         user = User.objects.get(id=user_id)
#         if not user:
#             return JsonResponse({"already_enrolled": False, "error": "User not found"}, status=404)

#         # ✅ Check if category_id exists in enrolled_courses
#         enrolled = any(str(course.id) == str(category_id) for course in user.enrolled_courses)

#         return JsonResponse({"already_enrolled": enrolled}, status=200)

#     except Exception as e:
#         return JsonResponse({"already_enrolled": False, "error": str(e)}, status=200)



# @csrf_exempt
# @authenticate
# def check_practice_enrollment(request, practice_id):
#     """
#     ✅ Check if the logged-in user is enrolled in the category
#     linked to a given PracticeTest.
#     """
#     if request.method != "GET":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         user_data = request.user or {}
#         user_id = user_data.get("id")

#         if not user_id:
#             return JsonResponse({"already_enrolled": False, "error": "Invalid user"}, status=401)

#         # ✅ Get User object
#         user = User.objects.get(id=user_id)
#         if not user:
#             return JsonResponse({"already_enrolled": False, "error": "User not found"}, status=404)

#         # ✅ Get Practice Test
#         practice = PracticeTest.objects.get(id=practice_id)
#         if not practice:
#             return JsonResponse({"already_enrolled": False, "error": "Practice test not found"}, status=404)

#         # ✅ Get linked Category
#         category = practice.category
#         if not category:
#             return JsonResponse({"already_enrolled": False, "error": "Category not linked"}, status=404)

#         # ✅ Check if enrolled in that category
#         enrolled = any(str(course.id) == str(category.id) for course in user.enrolled_courses)

#         return JsonResponse({"already_enrolled": enrolled}, status=200)

#     except PracticeTest.DoesNotExist:
#         return JsonResponse({"already_enrolled": False, "error": "Practice test not found"}, status=404)
#     except User.DoesNotExist:
#         return JsonResponse({"already_enrolled": False, "error": "User not found"}, status=404)
#     except Exception as e:
#         return JsonResponse({"already_enrolled": False, "error": str(e)}, status=500)





# import json
# import traceback
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import Enrollment
# from .serializers import EnrollmentSerializer
# from common.middleware import authenticate, restrict  # assuming you have a custom one

# @csrf_exempt
# @authenticate  # custom decorator that sets request.user
# @restrict(['admin'])
# def get_enrollments(request):
#     """
#     Admin-only: Fetch all enrollments
#     """
#     if request.method != "GET":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         user = getattr(request, "user", None)

#         # ✅ Handle missing or invalid user
#         if not user:
#             return JsonResponse({
#                 "success": False,
#                 "message": "Authentication required."
#             }, status=401)

#         # ✅ Only admins allowed
#         if not getattr(user, "is_admin", False):
#             return JsonResponse({
#                 "success": False,
#                 "message": "Unauthorized access. Admins only."
#             }, status=403)

#         # ✅ Fetch and serialize enrollments
#         enrollments = Enrollment.objects.all()
#         serializer = EnrollmentSerializer(enrollments, many=True)

#         return JsonResponse({
#             "success": True,
#             "count": len(serializer.data),
#             "data": serializer.data
#         }, status=200)

#     except Exception as e:
#         print(traceback.format_exc())  # for debugging
#         return JsonResponse({
#             "success": False,
#             "message": "An error occurred while fetching enrollments",
#             "error": str(e)
#         }, status=500)



# @csrf_exempt
# @authenticate
# def get_enrollment_detail(request, enrollment_id):
#     """Fetch a single enrollment by ID."""
#     if request.method != "GET":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         enrollment = Enrollment.objects.get(id=enrollment_id)
#         serializer = EnrollmentSerializer(enrollment)
#         return JsonResponse({
#             "success": True,
#             "data": serializer.data
#         }, status=200)

#     except Enrollment.DoesNotExist:
#         return JsonResponse({
#             "success": False,
#             "message": "Enrollment not found"
#         }, status=404)
#     except Exception as e:
#         return JsonResponse({
#             "success": False,
#             "message": "An error occurred while retrieving enrollment",
#             "error": str(e)
#         }, status=500)



# @csrf_exempt
# @authenticate
# def delete_enrollment(request, enrollment_id):
#     """Delete an enrollment (admin use only)."""
#     if request.method != "DELETE":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         enrollment = Enrollment.objects.get(id=enrollment_id)
#         enrollment.delete()
#         return JsonResponse({
#             "success": True,
#             "message": "Enrollment deleted successfully"
#         }, status=200)

#     except Enrollment.DoesNotExist:
#         return JsonResponse({
#             "success": False,
#             "message": "Enrollment not found"
#         }, status=404)
#     except Exception as e:
#         return JsonResponse({
#             "success": False,
#             "message": "An error occurred while deleting enrollment",
#             "error": str(e)
#         }, status=500)


# @csrf_exempt
# @authenticate
# def update_enrollment(request, enrollment_id):
#     """Update enrollment details."""
#     if request.method != "PUT":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     from bson import ObjectId
#     import json

#     try:
#         data = json.loads(request.body)
#         enrollment = Enrollment.objects.get(id=ObjectId(enrollment_id))

#         enrollment.user_name = data.get("user_name", enrollment.user_name)
#         enrollment.course_name = data.get("course_name", enrollment.course_name)
#         enrollment.duration_months = data.get("duration_months", enrollment.duration_months)
#         enrollment.enrolled_date = data.get("enrolled_date", enrollment.enrolled_date)
#         enrollment.expiry_date = data.get("expiry_date", enrollment.expiry_date)

#         enrollment.save()

#         return JsonResponse({
#             "success": True,
#             "message": "Enrollment updated successfully",
#             "data": {
#                 "id": str(enrollment.id),
#                 "user_name": enrollment.user_name,
#                 "course_name": enrollment.course_name,
#                 "duration_months": enrollment.duration_months,
#                 "enrolled_date": str(enrollment.enrolled_date),
#                 "expiry_date": str(enrollment.expiry_date)
#             }
#         }, status=200)

#     except Enrollment.DoesNotExist:
#         return JsonResponse({"success": False, "message": "Enrollment not found"}, status=404)
#     except Exception as e:
#         return JsonResponse({"success": False, "message": "An error occurred while updating enrollment", "error": str(e)}, status=500)




     



     # import json
# from rest_framework.response import Response
# from rest_framework import status
# from .serializers import EnrollmentSerializer
# from django.http import JsonResponse
# from bson import ObjectId
# from bson.errors import InvalidId
# from common.middleware import authenticate
# from django.views.decorators.csrf import csrf_exempt
# from .models import Enrollment  
# from users.models import User

# @csrf_exempt
# @authenticate
# def create_enrollment(request):
#     """Create a new enrollment."""
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         data = json.loads(request.body)
#         userId = request.user['id']  # from authenticate decorator
#         user = User.Objects.get(id=userId)
#         user_name = user.get("fullname")

#         # Inject user_name into data for serializer
#         data["user_name"] = user_name

#         serializer = EnrollmentSerializer(data=data)
#         if serializer.is_valid():
#             enrollment = serializer.save()
#             return JsonResponse({
#                 "success": True,
#                 "message": "Enrollment created successfully.",
#                 "data": {
#                     "id": str(enrollment.id),
#                     "user_name": enrollment.user_name,
#                     "course_name": enrollment.course_name,
#                     "duration_months": enrollment.duration_months,
#                     "enrolled_date": str(enrollment.enrolled_date),
#                     "expiry_date": str(enrollment.expiry_date),
#                 }
#             }, status=201)

#         return JsonResponse({
#             "success": False,
#             "message": "Invalid data",
#             "errors": serializer.errors
#         }, status=400)

#     except Exception as e:
#         print(e)
#         return JsonResponse({
#             "success": False,
#             "message": "An error occurred while creating enrollment",
#             "error": str(e)
#         }, status=500)

import json
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from bson import ObjectId
from bson.errors import InvalidId
from common.middleware import authenticate
from django.views.decorators.csrf import csrf_exempt
from .serializers import EnrollmentSerializer
from .models import Enrollment  
import datetime
from users.models import User
from practice_tests.models import PracticeTest




@csrf_exempt
@authenticate
def create_enrollment(request):
    """Create a new enrollment (only if not already enrolled). Supports both course and category enrollment."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        data = json.loads(request.body)
        print("RAW BODY:", request.body)
        course_id = data.get("course_id")  # Course ID for course-level enrollment
        category_id = data.get("category_id")  # Category ID for backward compatibility
        duration_months = data.get("duration_months")
        print(f"Course ID: {course_id}, Category ID: {category_id}, Duration: {duration_months}")
        
        if not duration_months:
            return JsonResponse({"success": False, "message": "Duration is required"}, status=400)

        # Prefer course_id over category_id
        if course_id:
            # Course-level enrollment
            from courses.models import Course
            course = Course.objects(id=ObjectId(course_id)).first()
            if not course:
                return JsonResponse({"success": False, "message": "Course not found"}, status=404)

            # Check if already enrolled in this course
            existing = Enrollment.objects(user_name=user_id, course=course).first()
            if existing:
                return JsonResponse({
                    "success": False,
                    "message": "You are already enrolled in this course!"
                }, status=400)

            # Create new enrollment
            enrolled_date = datetime.date.today()
            expiry_date = enrolled_date + datetime.timedelta(days=30 * int(duration_months))

            enrollment = Enrollment(
                user_name=user_id,
                course=course,
                category=course.category,  # Also store category for reference
                duration_months=duration_months,
                enrolled_date=enrolled_date,
                expiry_date=expiry_date
            )
            enrollment.save()

            # Update user's enrolled courses
            user = User.objects(id=ObjectId(user_id)).first()
            if user:
                # Check if course is already in enrolled_courses
                course_already_enrolled = False
                for enrolled_item in user.enrolled_courses:
                    if hasattr(enrolled_item, 'id') and str(enrolled_item.id) == str(course.id):
                        course_already_enrolled = True
                        break
                    try:
                        if str(enrolled_item) == str(course.id):
                            course_already_enrolled = True
                            break
                    except:
                        pass
                
                if not course_already_enrolled:
                    # Ensure we're appending the actual course document
                    # Reload course to ensure it's a proper document object
                    from courses.models import Course
                    course_doc = Course.objects(id=course.id).first()
                    if course_doc:
                        user.enrolled_courses.append(course_doc)
                        try:
                            user.save()
                        except Exception as e:
                            print(f"Error saving user enrolled_courses with course: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Send enrollment confirmation email
                try:
                    from .email_utils import send_enrollment_confirmation_email
                    send_enrollment_confirmation_email(
                        user_email=user.email,
                        user_name=user.fullname,
                        category_name=course.name,
                        enrolled_date=enrollment.enrolled_date,
                        expiry_date=enrollment.expiry_date
                    )
                except Exception as e:
                    print(f"Error sending enrollment email: {e}")

            return JsonResponse({
                "success": True,
                "message": "Enrollment successful",
                "data": {
                    "id": str(enrollment.id),
                    "user_name": user.fullname if user else user_id,
                    "course_id": str(course.id),
                    "course_name": course.name,
                    "category": {
                        "id": str(course.category.id) if course.category else None,
                        "name": course.category.name if course.category else None
                    },
                    "duration_months": enrollment.duration_months,
                    "enrolled_date": str(enrollment.enrolled_date),
                    "expiry_date": str(enrollment.expiry_date)
                }
            })
        
        elif category_id:
            # Category-level enrollment (backward compatibility)
            from categories.models import Category
            category = Category.objects(id=ObjectId(category_id)).first()
            if not category:
                return JsonResponse({"success": False, "message": "Category not found"}, status=404)

            # Check if already enrolled
            existing = Enrollment.objects(user_name=user_id, category=category).first()
            if existing:
                return JsonResponse({
                    "success": False,
                    "message": "You are already enrolled in this category!"
                }, status=400)

            # Create new enrollment
            enrolled_date = datetime.date.today()
            expiry_date = enrolled_date + datetime.timedelta(days=30 * int(duration_months))

            enrollment = Enrollment(
                user_name=user_id,
                category=category,
                duration_months=duration_months,
                enrolled_date=enrolled_date,
                expiry_date=expiry_date
            )
            enrollment.save()

            # Update user's enrolled courses
            user = User.objects(id=ObjectId(user_id)).first()
            if user:
                # Check if category is already in enrolled_courses
                category_already_enrolled = False
                for enrolled_item in user.enrolled_courses:
                    if hasattr(enrolled_item, 'id') and str(enrolled_item.id) == str(category.id):
                        category_already_enrolled = True
                        break
                    try:
                        if str(enrolled_item) == str(category.id):
                            category_already_enrolled = True
                            break
                    except:
                        pass
                
                if not category_already_enrolled:
                    # Ensure we're appending the actual category document
                    # Reload category to ensure it's a proper document object
                    from categories.models import Category
                    category_doc = Category.objects(id=category.id).first()
                    if category_doc:
                        user.enrolled_courses.append(category_doc)
                        try:
                            user.save()
                        except Exception as e:
                            print(f"Error saving user enrolled_courses with category: {e}")
                            import traceback
                            traceback.print_exc()
                
                # Send enrollment confirmation email
                try:
                    from .email_utils import send_enrollment_confirmation_email
                    send_enrollment_confirmation_email(
                        user_email=user.email,
                        user_name=user.fullname,
                        category_name=category.name,
                        enrolled_date=enrollment.enrolled_date,
                        expiry_date=enrollment.expiry_date
                    )
                except Exception as e:
                    print(f"Error sending enrollment email: {e}")

            return JsonResponse({
                "success": True,
                "message": "Enrollment successful",
                "data": {
                    "id": str(enrollment.id),
                    "user_name": user.fullname if user else user_id,
                    "category": {
                        "id": str(category.id),
                        "name": category.name
                    },
                    "duration_months": enrollment.duration_months,
                    "enrolled_date": str(enrollment.enrolled_date),
                    "expiry_date": str(enrollment.expiry_date)
                }
            })
        else:
            return JsonResponse({"success": False, "message": "Either course_id or category_id is required"}, status=400)

    except Exception as e:
        print("❌ Enrollment error:", e)
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": str(e)}, status=500)



@csrf_exempt
@authenticate
def check_enrollment(request, category_id):
    """
    Check if the logged-in user is already enrolled in the given TestCategory or Course.
    Supports both course_id and category_id (for backward compatibility).
    """
    if request.method != "GET":
        return JsonResponse(
            {"success": False, "message": "Method not allowed"},
            status=405
        )

    try:
        # ✅ Validate category_id is not undefined, null, or invalid
        if not category_id or category_id in ['undefined', 'null', '']:
            return JsonResponse(
                {"already_enrolled": False, "error": "Invalid ID"},
                status=400
            )
        
        # ✅ Validate ObjectId format
        if not ObjectId.is_valid(category_id):
            return JsonResponse(
                {"already_enrolled": False, "error": "Invalid ID format"},
                status=400
            )

        # ✅ Get authenticated user info
        user_data = request.user
        userId = request.user.get('id')
        if not userId:
            return JsonResponse(
                {"already_enrolled": False, "error": "User not authenticated"},
                status=401
            )
        
        # Convert userId to ObjectId if it's a string
        user_object_id = ObjectId(userId) if isinstance(userId, str) else userId
        user_id_str = str(userId)  # String format for user_name field
        
        try:
            user = User.objects.get(id=user_object_id)
        except User.DoesNotExist:
            return JsonResponse(
                {"already_enrolled": False, "error": "User not found"},
                status=404
            )

        # ✅ Check if it's a course or category
        from courses.models import Course
        course = Course.objects(id=ObjectId(category_id)).first()
        
        enrolled = False
        
        if course:
            # Check enrollment by course - try multiple user_name formats
            user_id_str = str(userId)
            
            print(f"[ENROLLMENT CHECK] Checking enrollment for course: {course.id}, user: {user_id_str}")
            print(f"[ENROLLMENT CHECK] Course slug: {getattr(course, 'slug', 'N/A')}, title: {getattr(course, 'title', 'N/A')}")
            
            # Method 1: Check with string user_id
            enrollment = Enrollment.objects(user_name=user_id_str, course=course).first()
            if enrollment:
                enrolled = True
                print(f"[ENROLLMENT CHECK] ✅ Found enrollment via Method 1 (string user_id): {enrollment.id}")
            
            # Method 2: Check with ObjectId user_id
            if not enrolled:
                try:
                    enrollment = Enrollment.objects(user_name=ObjectId(userId), course=course).first()
                    if enrollment:
                        enrolled = True
                        print(f"[ENROLLMENT CHECK] ✅ Found enrollment via Method 2 (ObjectId user_id): {enrollment.id}")
                except Exception as e:
                    print(f"[ENROLLMENT CHECK] Method 2 error: {e}")
            
            # Method 3: Check in user's enrolled_courses list
            if not enrolled and hasattr(user, 'enrolled_courses') and user.enrolled_courses:
                print(f"[ENROLLMENT CHECK] Checking user.enrolled_courses list ({len(user.enrolled_courses)} items)")
                for enrolled_item in user.enrolled_courses:
                    try:
                        enrolled_course_id = None
                        if hasattr(enrolled_item, 'id'):
                            enrolled_course_id = str(enrolled_item.id)
                        elif isinstance(enrolled_item, dict) and 'id' in enrolled_item:
                            enrolled_course_id = str(enrolled_item['id'])
                        elif isinstance(enrolled_item, ObjectId):
                            enrolled_course_id = str(enrolled_item)
                        else:
                            enrolled_course_id = str(enrolled_item)
                        
                        if enrolled_course_id == str(course.id):
                            enrolled = True
                            print(f"[ENROLLMENT CHECK] ✅ Found enrollment via Method 3 (user.enrolled_courses): {enrolled_course_id}")
                            break
                    except Exception as e:
                        print(f"[ENROLLMENT CHECK] Error processing enrolled_item: {e}")
                        continue
            
            if not enrolled:
                print(f"[ENROLLMENT CHECK] ❌ No enrollment found for course {course.id}, user {user_id_str}")
                # Debug: Check all enrollments for this user
                all_user_enrollments = Enrollment.objects(user_name=user_id_str)
                print(f"[ENROLLMENT CHECK] Total enrollments for user: {all_user_enrollments.count()}")
                for e in all_user_enrollments[:5]:  # Show first 5
                    e_course_id = str(e.course.id) if e.course else "None"
                    print(f"[ENROLLMENT CHECK]   - Enrollment {e.id}: course_id={e_course_id}, matches={e_course_id == str(course.id)}")
            else:
                print(f"[ENROLLMENT CHECK] ✅ User IS enrolled in course {course.id}")
        else:
            # Check enrollment by category (backward compatibility)
            from categories.models import Category
            category = Category.objects(id=ObjectId(category_id)).first()
            if category:
                user_id_str = str(userId)
                
                # Method 1: Check with string user_id
                enrollment = Enrollment.objects(user_name=user_id_str, category=category).first()
                if enrollment:
                    enrolled = True
                
                # Method 2: Check with ObjectId user_id
                if not enrolled:
                    try:
                        enrollment = Enrollment.objects(user_name=ObjectId(userId), category=category).first()
                        if enrollment:
                            enrolled = True
                    except:
                        pass
                
                # Method 3: Check in user's enrolled_courses list
                if not enrolled and hasattr(user, 'enrolled_courses') and user.enrolled_courses:
                    for enrolled_item in user.enrolled_courses:
                        try:
                            enrolled_cat_id = None
                            if hasattr(enrolled_item, 'id'):
                                enrolled_cat_id = str(enrolled_item.id)
                            elif isinstance(enrolled_item, dict) and 'id' in enrolled_item:
                                enrolled_cat_id = str(enrolled_item['id'])
                            elif isinstance(enrolled_item, ObjectId):
                                enrolled_cat_id = str(enrolled_item)
                            else:
                                enrolled_cat_id = str(enrolled_item)
                            
                            if enrolled_cat_id == str(category.id):
                                enrolled = True
                                break
                        except:
                            continue
            else:
                # Fallback: Check in user's enrolled_courses list by ID string
                if hasattr(user, 'enrolled_courses') and user.enrolled_courses:
                    enrolled = any(str(c.id) == str(category_id) for c in user.enrolled_courses if hasattr(c, 'id'))

        return JsonResponse({"already_enrolled": enrolled}, status=200)

    except Exception as e:
        # ✅ Handle all errors safely
        return JsonResponse(
            {"already_enrolled": False, "error": str(e)},
            status=200
        )





@csrf_exempt
@authenticate
def check_practice_enrollment(request, practice_id):
    """
    ✅ Check if the logged-in user is enrolled in the course or category
    linked to a given PracticeTest. Prefers course enrollment over category enrollment.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_data = request.user or {}
        user_id = user_data.get("id")

        if not user_id:
            return JsonResponse({"already_enrolled": False, "error": "Invalid user"}, status=401)

        # ✅ Get User object
        user = User.objects.get(id=user_id)
        if not user:
            return JsonResponse({"already_enrolled": False, "error": "User not found"}, status=404)

        # ✅ Get Practice Test
        practice = PracticeTest.objects.get(id=practice_id)
        if not practice:
            return JsonResponse({"already_enrolled": False, "error": "Practice test not found"}, status=404)

        # ✅ Check enrollment by course first (preferred)
        if practice.course:
            # Check if enrolled in the course
            enrollment = Enrollment.objects(user_name=user_id, course=practice.course).first()
            if enrollment:
                return JsonResponse({"already_enrolled": True}, status=200)
            
            # Also check in user's enrolled_courses list
            enrolled = any(str(c.id) == str(practice.course.id) for c in user.enrolled_courses if hasattr(c, 'id'))
            if enrolled:
                return JsonResponse({"already_enrolled": True}, status=200)

        # ✅ Fallback: Check enrollment by category (backward compatibility)
        category = None
        if practice.category:
            category = practice.category
        elif practice.course and practice.course.category:
            category = practice.course.category
        
        if category:
            # Check enrollment by category
            enrollment = Enrollment.objects(user_name=user_id, category=category).first()
            if enrollment:
                return JsonResponse({"already_enrolled": True}, status=200)
            
            # Also check in user's enrolled_courses list
            enrolled = any(str(c.id) == str(category.id) for c in user.enrolled_courses if hasattr(c, 'id'))
            if enrolled:
                return JsonResponse({"already_enrolled": True}, status=200)

        return JsonResponse({"already_enrolled": False}, status=200)

    except PracticeTest.DoesNotExist:
        return JsonResponse({"already_enrolled": False, "error": "Practice test not found"}, status=404)
    except User.DoesNotExist:
        return JsonResponse({"already_enrolled": False, "error": "User not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"already_enrolled": False, "error": str(e)}, status=500)





import json
import traceback
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Enrollment
from .serializers import EnrollmentSerializer
from common.middleware import authenticate, restrict  # assuming you have a custom one

@csrf_exempt
@authenticate
@restrict("admin")
def get_enrollments(request):
    """Admin-only: Fetch all enrollments"""
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user = getattr(request, "user", None)

        # ✅ Check authentication
        if not user:
            return JsonResponse({
                "success": False,
                "message": "Authentication required."
            }, status=401)

        # ✅ Handle both dict and object cases
        
        # ✅ Fetch all enrollments
        enrollments = Enrollment.objects.all()
        serializer = EnrollmentSerializer(enrollments, many=True)
        print("serializer : ",serializer.data)

        return JsonResponse({
            "success": True,
            "count": len(serializer.data),
            "data": serializer.data
        }, status=200)

    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({
            "success": False,
            "message": "An error occurred while fetching enrollments",
            "error": str(e)
        }, status=500)




@csrf_exempt
@authenticate
def get_enrollment_detail(request, enrollment_id):
    """Fetch a single enrollment by ID."""
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        serializer = EnrollmentSerializer(enrollment)
        return JsonResponse({
            "success": True,
            "data": serializer.data
        }, status=200)

    except Enrollment.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Enrollment not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "An error occurred while retrieving enrollment",
            "error": str(e)
        }, status=500)



@csrf_exempt
@authenticate
def delete_enrollment(request, enrollment_id):
    """Delete an enrollment (admin use only)."""
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        enrollment = Enrollment.objects.get(id=enrollment_id)
        enrollment.delete()
        return JsonResponse({
            "success": True,
            "message": "Enrollment deleted successfully"
        }, status=200)

    except Enrollment.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "Enrollment not found"
        }, status=404)
    except Exception as e:
        return JsonResponse({
            "success": False,
            "message": "An error occurred while deleting enrollment",
            "error": str(e)
        }, status=500)


@csrf_exempt
@authenticate
def update_enrollment(request, enrollment_id):
    """Update enrollment details."""
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    from bson import ObjectId
    import json

    try:
        data = json.loads(request.body)
        enrollment = Enrollment.objects.get(id=ObjectId(enrollment_id))

        enrollment.user_name = data.get("user_name", enrollment.user_name)
        enrollment.course_name = data.get("course_name", enrollment.course_name)
        enrollment.duration_months = data.get("duration_months", enrollment.duration_months)
        enrollment.enrolled_date = data.get("enrolled_date", enrollment.enrolled_date)
        enrollment.expiry_date = data.get("expiry_date", enrollment.expiry_date)

        enrollment.save()

        return JsonResponse({
            "success": True,
            "message": "Enrollment updated successfully",
            "data": {
                "id": str(enrollment.id),
                "user_name": enrollment.user_name,
                "course_name": enrollment.course_name,
                "duration_months": enrollment.duration_months,
                "enrolled_date": str(enrollment.enrolled_date),
                "expiry_date": str(enrollment.expiry_date)
            }
        }, status=200)

    except Enrollment.DoesNotExist:
        return JsonResponse({"success": False, "message": "Enrollment not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": "An error occurred while updating enrollment", "error": str(e)}, status=500)


@csrf_exempt
@authenticate
def get_user_enrollments(request):
    """Get all enrollments for the logged-in user with payment info."""
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get('id')
        if not user_id:
            return JsonResponse({
                "success": False,
                "message": "Authentication required."
            }, status=401)

        # Convert userId to ObjectId if needed
        if ObjectId.is_valid(user_id):
            user_obj = User.objects.get(id=ObjectId(user_id))
        else:
            user_obj = User.objects.get(id=user_id)

        # Fetch enrollments for this user ONLY - ensure we're filtering by the logged-in user
        user_id_str = str(user_obj.id)
        # Double-check: ensure we're only getting enrollments for this specific user
        # This prevents any potential issues where enrollments from other users might be returned
        enrollments = Enrollment.objects(user_name=user_id_str)
        
        # Log for debugging (can be removed in production)
        print(f"Fetching enrollments for user_id: {user_id_str}, found {enrollments.count()} enrollments")
        
        enrollments_data = []
        for enrollment in enrollments:
            try:
                # Safely access course fields
                course = None
                course_id = None
                course_name = None
                course_code = None
                course_slug = None
                provider = None
                
                if enrollment.course:
                    try:
                        course = enrollment.course
                        course_id = str(course.id)
                        course_name = course.title if hasattr(course, 'title') else None
                        course_code = course.code if hasattr(course, 'code') else None
                        course_slug = course.slug if hasattr(course, 'slug') else None
                        if course.provider:
                            try:
                                provider = course.provider.name if hasattr(course.provider, 'name') else None
                            except:
                                provider = None
                    except Exception as e:
                        # Course reference might be broken
                        print(f"Error accessing course for enrollment {enrollment.id}: {e}")
                
                enrollment_dict = {
                    "id": str(enrollment.id),
                    "course_id": course_id,
                    "course_name": course_name,
                    "course_code": course_code,
                    "course_slug": course_slug,
                    "provider": provider,
                    "category": {
                        "id": str(enrollment.category.id),
                        "name": enrollment.category.name
                    } if enrollment.category else None,
                    "duration_months": enrollment.duration_months,
                    "enrolled_date": str(enrollment.enrolled_date),
                    "expiry_date": str(enrollment.expiry_date),
                    "payment": None
                }
                # Add payment info if exists
                if enrollment.payment:
                    try:
                        payment = enrollment.payment
                        enrollment_dict["payment"] = {
                            "id": str(payment.id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "status": payment.status,
                            "paid_at": str(payment.paid_at) if payment.paid_at else None
                        }
                    except Exception as e:
                        print(f"Error accessing payment for enrollment {enrollment.id}: {e}")
                
                enrollments_data.append(enrollment_dict)
            except Exception as e:
                # Skip enrollments that can't be processed
                print(f"Error processing enrollment {enrollment.id}: {e}")
                continue

        return JsonResponse({
            "success": True,
            "count": len(enrollments_data),
            "data": enrollments_data
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "User not found"
        }, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({
            "success": False,
            "message": "An error occurred while fetching enrollments",
            "error": str(e)
        }, status=500)


# ==================== RAZORPAY PAYMENT VIEWS ====================

import razorpay
import hashlib
import hmac
from django.conf import settings
from .payment_models import Payment
from datetime import datetime, date, timedelta

@csrf_exempt
@authenticate
def create_razorpay_order(request):
    """Create Razorpay order for enrollment payment"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = request.user.get("id")
        course_id = data.get("course_id")
        category_id = data.get("category_id")
        duration_months = data.get("duration_months")
        amount = data.get("amount")  # Amount in rupees
        coupon_code = data.get("coupon_code")  # Optional coupon code

        if (not course_id and not category_id) or not duration_months or not amount:
            return JsonResponse({"success": False, "message": "Missing required fields (course_id or category_id, duration_months, amount)"}, status=400)

        # Apply coupon if provided
        final_amount = float(amount)
        discount_amount = 0
        coupon_data = None
        
        if coupon_code:
            from reviews.models import Coupon
            
            # Verify coupon
            coupon = Coupon.objects(code=coupon_code.upper()).first()
            if coupon:
                # Check if coupon is valid - per-user usage tracking
                if coupon.is_active:
                    now = datetime.utcnow()
                    user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
                    
                    # Check if user has already used this coupon
                    user_already_used = user_object_id in coupon.used_by
                    
                    # For backward compatibility, also check is_used for non-authenticated cases
                    if not user_already_used and (not coupon.is_used or coupon.is_common):
                        if coupon.valid_from <= now and coupon.valid_until >= now:
                            # Check minimum purchase
                            if final_amount >= coupon.min_purchase:
                                # Calculate discount
                                if coupon.discount_type == 'percentage':
                                    discount_amount = (final_amount * coupon.discount_value) / 100
                                    if coupon.max_discount:
                                        discount_amount = min(discount_amount, coupon.max_discount)
                                else:
                                    discount_amount = coupon.discount_value
                                
                                final_amount = max(0, final_amount - discount_amount)
                                coupon_data = {
                                    "code": coupon.code,
                                    "discount_amount": round(discount_amount, 2),
                                    "coupon_id": str(coupon.id)
                                }

        # Validate Razorpay credentials
        if not hasattr(settings, 'RAZORPAY_KEY_ID') or not hasattr(settings, 'RAZORPAY_KEY_SECRET'):
            return JsonResponse({
                "success": False, 
                "message": "Razorpay credentials not configured. Please contact administrator."
            }, status=500)
        
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return JsonResponse({
                "success": False, 
                "message": "Razorpay credentials not configured. Please contact administrator."
            }, status=500)

        # Initialize Razorpay client
        try:
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        except Exception as e:
            print(f"Error initializing Razorpay client: {e}")
            return JsonResponse({
                "success": False, 
                "message": "Failed to initialize payment gateway. Please try again."
            }, status=500)
        
        # Validate amount
        if final_amount <= 0:
            return JsonResponse({
                "success": False, 
                "message": "Invalid amount. Amount must be greater than 0."
            }, status=400)
        
        # Create order with final amount after discount
        amount_in_paise = int(round(final_amount * 100))  # Convert to paise, ensure integer
        
        # Ensure minimum amount (Razorpay requires minimum 1 rupee = 100 paise)
        if amount_in_paise < 100:
            amount_in_paise = 100
            final_amount = 1.0
        
        # Generate short receipt (max 40 chars for Razorpay)
        # Remove any special characters and ensure alphanumeric only
        import re
        timestamp_str = str(int(datetime.now().timestamp()))
        user_id_clean = re.sub(r'[^a-zA-Z0-9]', '', str(user_id))[:8]
        id_for_receipt = re.sub(r'[^a-zA-Z0-9]', '', str(course_id or category_id))[:8]
        receipt = f"ENR{user_id_clean}{id_for_receipt}{timestamp_str[-8:]}"
        receipt = receipt[:40]  # Ensure max 40 chars
        
        # Ensure receipt is not empty
        if not receipt or len(receipt) < 3:
            receipt = f"ENR{timestamp_str}"
            receipt = receipt[:40]
        
        # CRITICAL: Ensure amount is integer (Razorpay requires integer, not float)
        amount_in_paise = int(amount_in_paise)
        
        order_data = {
            "amount": amount_in_paise,  # Must be integer in paise
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "user_id": str(user_id),
                "course_id": str(course_id) if course_id else "",
                "category_id": str(category_id) if category_id else "",
                "duration_months": str(duration_months)
            }
        }
        
        # Log order data for debugging mozart service errors
        print(f"Creating Razorpay order: amount={amount_in_paise} paise (₹{amount_in_paise/100:.2f}), receipt={receipt}")

        try:
            # Validate order data before creating
            if amount_in_paise < 100:
                return JsonResponse({
                    "success": False, 
                    "message": "Amount must be at least ₹1.00"
                }, status=400)
            
            if not receipt or len(receipt) > 40:
                return JsonResponse({
                    "success": False, 
                    "message": "Invalid receipt format"
                }, status=400)
            
            razorpay_order = razorpay_client.order.create(data=order_data)
            print(f"Razorpay order created successfully: {razorpay_order.get('id')}")
            print(f"Order amount: {razorpay_order.get('amount')} paise")
            
            # Validate the order response
            if not razorpay_order.get('id'):
                return JsonResponse({
                    "success": False, 
                    "message": "Invalid order response from payment gateway"
                }, status=500)
                
        except razorpay.errors.BadRequestError as e:
            print(f"Razorpay BadRequestError: {e}")
            error_msg = str(e)
            # Provide more helpful error messages
            if "amount" in error_msg.lower():
                return JsonResponse({
                    "success": False, 
                    "message": "Invalid payment amount. Please contact support."
                }, status=400)
            return JsonResponse({
                "success": False, 
                "message": f"Payment gateway error: {error_msg}"
            }, status=400)
        except razorpay.errors.ServerError as e:
            print(f"Razorpay ServerError: {e}")
            return JsonResponse({
                "success": False, 
                "message": "Payment gateway server error. Please try again later."
            }, status=500)
        except Exception as e:
            print(f"Razorpay order creation error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "success": False, 
                "message": f"Failed to create payment order: {str(e)}"
            }, status=500)

        # Check if order_id already exists (prevent duplicate orders)
        existing_payment = Payment.objects(razorpay_order_id=razorpay_order['id']).first()
        if existing_payment:
            # If payment exists and is completed, return error
            if existing_payment.status == "completed":
                return JsonResponse({
                    "success": False, 
                    "message": "This payment order has already been used. Please create a new payment."
                }, status=400)
            # If payment exists but is pending, delete it and create new one
            existing_payment.delete()

        # Create payment record with final amount after discount
        payment = Payment(
            user_id=user_id,
            razorpay_order_id=razorpay_order['id'],
            amount=final_amount,  # Use final amount after discount
            currency="INR",
            status="pending"
        )
        payment.save()
        
        # Store coupon info in payment if applied
        if coupon_data:
            payment.coupon_code = coupon_data.get("code")
            payment.discount_amount = coupon_data.get("discount_amount", 0)
        payment.save()

        print(f"Payment record created: payment_id={payment.id}, order_id={razorpay_order['id']}, amount={final_amount}")

        # CRITICAL: Use the EXACT amount from Razorpay order response
        # This ensures frontend uses the same amount Razorpay expects
        order_amount = int(razorpay_order.get('amount', amount_in_paise))
        
        # Validate the order amount matches what we sent
        if order_amount != amount_in_paise:
            print(f"WARNING: Order amount mismatch. Sent: {amount_in_paise}, Received: {order_amount}")
            # Use what Razorpay returned to avoid mozart service errors
            order_amount = int(razorpay_order.get('amount'))

        response_data = {
            "success": True,
            "order_id": str(razorpay_order['id']),  # Must be exact string from Razorpay
            "amount": order_amount,  # EXACT amount from Razorpay (in paise as integer)
            "currency": str(razorpay_order.get('currency', 'INR')),
            "key_id": str(settings.RAZORPAY_KEY_ID),
            "payment_id": str(payment.id),
            "original_amount": float(amount),
            "final_amount": final_amount,
            "discount_amount": discount_amount
        }
        
        # Log for debugging
        print(f"Razorpay order response: order_id={response_data['order_id']}, amount={response_data['amount']} paise")
        
        if coupon_data:
            response_data["coupon"] = coupon_data
        
        return JsonResponse(response_data, status=200)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def create_pricing_plan_order(request):
    """Create Razorpay order for pricing plan payment"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        user_id = request.user.get("id")
        provider = data.get("provider")
        exam_code = data.get("exam_code")
        plan_name = data.get("plan_name")
        amount = data.get("amount")  # Amount in rupees

        if not provider or not exam_code or not plan_name or not amount:
            return JsonResponse({
                "success": False, 
                "message": "Missing required fields (provider, exam_code, plan_name, amount)"
            }, status=400)

        # Find course by provider and exam_code (using improved lookup logic)
        from courses.models import Course
        from providers.models import Provider
        
        # Normalize inputs
        provider_normalized = provider.lower().replace('_', '-')
        exam_code_normalized = exam_code.lower().replace('_', '-')
        
        # Try to find provider
        provider_obj = None
        try:
            provider_obj = Provider.objects.get(slug=provider_normalized)
        except Provider.DoesNotExist:
            try:
                provider_obj = Provider.objects.get(name__iexact=provider_normalized)
            except Provider.DoesNotExist:
                try:
                    provider_obj = Provider.objects.get(name__iexact=provider_normalized.replace('-', ' '))
                except Provider.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Provider not found"}, status=404)
        
        # Try to find course using improved lookup (same as course_detail)
        course = None
        slug = f"{provider_normalized}-{exam_code_normalized}"
        
        # Try exact slug match
        try:
            course = Course.objects.get(slug=slug, is_active=True)
        except Course.DoesNotExist:
            # Try case-insensitive
            try:
                course = Course.objects.get(slug__iexact=slug, is_active=True)
            except Course.DoesNotExist:
                # Try by provider and code
                code_variants = [
                    exam_code_normalized.upper(),
                    exam_code_normalized.upper().replace('-', '_'),
                    exam_code_normalized.upper().replace('_', '-'),
                    exam_code_normalized,
                ]
                
                for code_variant in code_variants:
                    try:
                        course = Course.objects.get(provider=provider_obj, code__iexact=code_variant, is_active=True)
                        break
                    except Course.DoesNotExist:
                        continue
                
                # Last resort: partial match
                if not course:
                    try:
                        courses = Course.objects.filter(provider=provider_obj, slug__icontains=exam_code_normalized.lower(), is_active=True)
                        if courses.count() == 1:
                            course = courses.first()
                    except Exception:
                        pass
        
        if not course:
            return JsonResponse({"success": False, "message": "Course not found"}, status=404)

        # Validate Razorpay credentials
        if not hasattr(settings, 'RAZORPAY_KEY_ID') or not hasattr(settings, 'RAZORPAY_KEY_SECRET'):
            return JsonResponse({
                "success": False, 
                "message": "Razorpay credentials not configured. Please contact administrator."
            }, status=500)
        
        if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
            return JsonResponse({
                "success": False, 
                "message": "Razorpay credentials not configured. Please contact administrator."
            }, status=500)

        # Initialize Razorpay client
        try:
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        except Exception as e:
            print(f"Error initializing Razorpay client: {e}")
            return JsonResponse({
                "success": False, 
                "message": "Failed to initialize payment gateway. Please try again."
            }, status=500)
        
        # Validate amount
        final_amount = float(amount)
        if final_amount <= 0:
            return JsonResponse({
                "success": False, 
                "message": "Invalid amount. Amount must be greater than 0."
            }, status=400)
        
        # Create order
        amount_in_paise = int(round(final_amount * 100))
        if amount_in_paise < 100:
            amount_in_paise = 100
            final_amount = 1.0
        
        # Generate receipt
        import re
        timestamp_str = str(int(datetime.utcnow().timestamp()))
        user_id_clean = re.sub(r'[^a-zA-Z0-9]', '', str(user_id))[:8]
        course_id_clean = re.sub(r'[^a-zA-Z0-9]', '', str(course.id))[:8]
        receipt = f"PRC{user_id_clean}{course_id_clean}{timestamp_str[-8:]}"
        receipt = receipt[:40]
        
        if not receipt or len(receipt) < 3:
            receipt = f"PRC{timestamp_str}"
            receipt = receipt[:40]
        
        amount_in_paise = int(amount_in_paise)
        
        order_data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": {
                "user_id": str(user_id),
                "course_id": str(course.id),
                "provider": provider,
                "exam_code": exam_code,
                "plan_name": plan_name
            }
        }
        
        try:
            if amount_in_paise < 100:
                return JsonResponse({
                    "success": False, 
                    "message": "Amount must be at least ₹1.00"
                }, status=400)
            
            razorpay_order = razorpay_client.order.create(data=order_data)
            print(f"Razorpay order created successfully: {razorpay_order.get('id')}")
            
            if not razorpay_order.get('id'):
                return JsonResponse({
                    "success": False, 
                    "message": "Invalid order response from payment gateway"
                }, status=500)
                
        except razorpay.errors.BadRequestError as e:
            print(f"Razorpay BadRequestError: {e}")
            return JsonResponse({
                "success": False, 
                "message": f"Payment gateway error: {str(e)}"
            }, status=400)
        except Exception as e:
            print(f"Razorpay order creation error: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                "success": False, 
                "message": f"Failed to create payment order: {str(e)}"
            }, status=500)

        # Check if order_id already exists
        existing_payment = Payment.objects(razorpay_order_id=razorpay_order['id']).first()
        if existing_payment:
            if existing_payment.status == "completed":
                return JsonResponse({
                    "success": False, 
                    "message": "This payment order has already been used. Please create a new payment."
                }, status=400)
            existing_payment.delete()

        # Create payment record
        payment = Payment(
            user_id=user_id,
            razorpay_order_id=razorpay_order['id'],
            amount=final_amount,
            currency="INR",
            status="pending"
        )
        payment.save()

        print(f"Payment record created: payment_id={payment.id}, order_id={razorpay_order['id']}, amount={final_amount}")

        order_amount = int(razorpay_order.get('amount', amount_in_paise))
        
        response_data = {
            "success": True,
            "order_id": str(razorpay_order['id']),
            "amount": order_amount,
            "currency": str(razorpay_order.get('currency', 'INR')),
            "key_id": str(settings.RAZORPAY_KEY_ID),
            "payment_id": str(payment.id),
            "final_amount": final_amount
        }
        
        print(f"Razorpay order response: order_id={response_data['order_id']}, amount={response_data['amount']} paise")
        
        return JsonResponse(response_data, status=200)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def verify_razorpay_payment(request):
    """Verify Razorpay payment and create enrollment"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Parse JSON with better error handling
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({"success": False, "message": f"Invalid JSON: {str(e)}"}, status=400)
        
        # Check if user is authenticated
        if not hasattr(request, 'user') or not request.user:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)
        
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User ID not found in token"}, status=401)
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        payment_id = data.get("payment_id")
        course_id = data.get("course_id")
        category_id = data.get("category_id")
        duration_months = data.get("duration_months")
        pricing_plan_id = data.get("pricing_plan_id")
        duration_days = data.get("duration_days")

        # Check for missing fields with detailed error message
        missing_fields = []
        if not razorpay_order_id:
            missing_fields.append("razorpay_order_id")
        if not razorpay_payment_id:
            missing_fields.append("razorpay_payment_id")
        if not razorpay_signature:
            missing_fields.append("razorpay_signature")
        if not payment_id:
            missing_fields.append("payment_id")
        if not course_id and not category_id:
            missing_fields.append("course_id or category_id")
        if duration_months is None:
            missing_fields.append("duration_months")

        if missing_fields:
            return JsonResponse({
                "success": False, 
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }, status=400)

        # Get payment record
        payment = Payment.objects.get(id=ObjectId(payment_id))
        if payment.user_id != user_id:
            return JsonResponse({"success": False, "message": "Unauthorized"}, status=403)

        # Verify signature
        message = f"{razorpay_order_id}|{razorpay_payment_id}"
        generated_signature = hmac.new(
            settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if generated_signature != razorpay_signature:
            payment.status = "failed"
            payment.save()
            return JsonResponse({"success": False, "message": "Invalid payment signature"}, status=400)

        # Set paid_at timestamp (payment is verified at this point)
        paid_at = datetime.utcnow()
        payment.paid_at = paid_at
        payment.status = "completed"
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.updated_at = datetime.utcnow()
        payment.save()

        # Get duration_days from pricing plan if pricing_plan_id is provided
        if pricing_plan_id and not duration_days:
            try:
                from pricing.models import PricingPlan
                pricing_plan = PricingPlan.objects(id=ObjectId(pricing_plan_id)).first()
                if pricing_plan:
                    duration_days = pricing_plan.duration_days
            except Exception as e:
                print(f"Error fetching pricing plan: {e}")
        
        # Fallback: calculate duration_days from duration_months if not provided
        if not duration_days:
            if duration_months:
                duration_days = 30 * int(duration_months)
            else:
                duration_days = 365  # Default to 1 year if nothing is provided

        # Prefer course_id over category_id
        if course_id:
            # Course-level enrollment
            from courses.models import Course
            course = Course.objects(id=ObjectId(course_id)).first()
            if not course:
                return JsonResponse({"success": False, "message": "Course not found"}, status=404)

            # Check if already enrolled
            existing = Enrollment.objects(user_name=payment.user_id, course=course).first()
            if existing:
                # Payment already updated above, just return
                return JsonResponse({
                    "success": True,
                    "message": "You are already enrolled in this course!",
                    "already_enrolled": True,
                    "enrollment_id": str(existing.id)
                }, status=200)

            # Create enrollment
            # Calculate expiry_date from paid_at + duration_days
            # paid_at is already a datetime object from datetime.utcnow()
            enrolled_date = paid_at.date()
            # paid_at is already datetime, so use it directly
            expiry_date = (paid_at + timedelta(days=int(duration_days))).date()

            enrollment = Enrollment(
                user_name=payment.user_id,
                course=course,
                category=course.category,  # Also store category for reference
                duration_months=duration_months,
                enrolled_date=enrolled_date,
                expiry_date=expiry_date,
                payment=payment
            )
            enrollment.save()

            # Update user's enrolled courses
            user = User.objects(id=ObjectId(payment.user_id)).first()
            if user:
                # Check if course is already in enrolled_courses
                course_already_enrolled = False
                for enrolled_item in user.enrolled_courses:
                    if hasattr(enrolled_item, 'id') and str(enrolled_item.id) == str(course.id):
                        course_already_enrolled = True
                        break
                    # Also check if it's the same course by comparing IDs
                    try:
                        if str(enrolled_item) == str(course.id):
                            course_already_enrolled = True
                            break
                    except:
                        pass
                
                if not course_already_enrolled:
                    # Ensure we're appending the actual course document
                    # Reload course to ensure it's a proper document object
                    from courses.models import Course
                    course_doc = Course.objects(id=course.id).first()
                    if course_doc:
                        user.enrolled_courses.append(course_doc)
                        try:
                            user.save()
                        except Exception as e:
                            print(f"Error saving user enrolled_courses with course: {e}")
                            import traceback
                            traceback.print_exc()
        elif category_id:
            # Category-level enrollment (backward compatibility)
            from categories.models import Category
            category = Category.objects(id=ObjectId(category_id)).first()
            if not category:
                return JsonResponse({"success": False, "message": "Category not found"}, status=404)

            # Check if already enrolled
            existing = Enrollment.objects(user_name=payment.user_id, category=category).first()
            if existing:
                # Payment already updated above, just return
                return JsonResponse({
                    "success": True,
                    "message": "You are already enrolled in this category!",
                    "already_enrolled": True,
                    "enrollment_id": str(existing.id)
                }, status=200)

            # Create enrollment
            # Calculate expiry_date from paid_at + duration_days
            # paid_at is already a datetime object from datetime.utcnow()
            enrolled_date = paid_at.date()
            # paid_at is already datetime, so use it directly
            expiry_date = (paid_at + timedelta(days=int(duration_days))).date()

            enrollment = Enrollment(
                user_name=payment.user_id,
                category=category,
                duration_months=duration_months,
                enrolled_date=enrolled_date,
                expiry_date=expiry_date,
                payment=payment
            )
            enrollment.save()

            # Update user's enrolled courses
            user = User.objects(id=ObjectId(payment.user_id)).first()
            if user:
                # Check if category is already in enrolled_courses
                category_already_enrolled = False
                for enrolled_item in user.enrolled_courses:
                    if hasattr(enrolled_item, 'id') and str(enrolled_item.id) == str(category.id):
                        category_already_enrolled = True
                        break
                    try:
                        if str(enrolled_item) == str(category.id):
                            category_already_enrolled = True
                            break
                    except:
                        pass
                
                if not category_already_enrolled:
                    # Ensure we're appending the actual category document
                    # Reload category to ensure it's a proper document object
                    from categories.models import Category
                    category_doc = Category.objects(id=category.id).first()
                    if category_doc:
                        user.enrolled_courses.append(category_doc)
                        try:
                            user.save()
                        except Exception as e:
                            print(f"Error saving user enrolled_courses with category: {e}")
                            import traceback
                            traceback.print_exc()
        else:
            return JsonResponse({"success": False, "message": "Either course_id or category_id is required"}, status=400)

        # Check if user was a lead with assigned coupon and assign it to them
        try:
            from leads.models import Lead
            from reviews.models import Coupon
            
            # Find lead by email or phone
            user = User.objects(id=ObjectId(user_id)).first()
            if user:
                lead = None
                # Try to find lead by email
                try:
                    lead = Lead.objects(email=user.email.lower()).first()
                except:
                    pass
                
                # If no lead by email, try by phone
                if not lead and hasattr(user, 'phone_number'):
                    try:
                        lead = Lead.objects(whatsapp_number=user.phone_number).first()
                    except:
                        pass
                
                # If lead found, check for assigned coupon
                if lead:
                    # Find coupon assigned to this lead (where user is not set yet)
                    lead_coupons = Coupon.objects(lead=lead)
                    for lead_coupon in lead_coupons:
                        if not lead_coupon.user:  # Only assign if not already assigned
                            # Assign the coupon to the user
                            lead_coupon.user = user
                            lead_coupon.lead = None  # Remove lead reference
                            lead_coupon.save()
                            print(f"✅ Coupon {lead_coupon.code} assigned to user {user_id} from lead {lead.id}")
                            
                            # Create notification for coupon received
                            try:
                                from notifications.views import create_notification
                                create_notification(
                                    user=user,
                                    notification_type='coupon',
                                    title='Special Coupon for You! 🎉',
                                    message=f'You received a special coupon code: {lead_coupon.code}. Get {lead_coupon.discount_value}{"%" if lead_coupon.discount_type == "percentage" else "₹"} off!',
                                    link='/dashboard',
                                    metadata={'coupon_id': str(lead_coupon.id), 'coupon_code': lead_coupon.code}
                                )
                            except Exception as e:
                                print(f"Error creating notification: {e}")
                            
                            break  # Only assign one coupon
        except Exception as e:
            # Ignore errors - enrollment should still succeed
            print(f"Warning: Could not assign coupon from lead: {str(e)}")
            import traceback
            traceback.print_exc()
            pass

        # Mark coupon as used if payment has coupon code (per-user tracking)
        if payment.coupon_code:
            try:
                from reviews.models import Coupon
                coupon = Coupon.objects(code=payment.coupon_code.upper()).first()
                if coupon:
                    user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
                    # Add user to used_by list if not already there (one coupon per user)
                    if user_object_id not in coupon.used_by:
                        coupon.used_by.append(user_object_id)
                        coupon.used_at = datetime.utcnow()
                        # Also set is_used for backward compatibility
                        coupon.is_used = True
                        coupon.save()
            except Exception as e:
                # Ignore coupon errors - payment should still succeed
                print(f"Warning: Could not mark coupon as used: {str(e)}")
                import traceback
                traceback.print_exc()
                pass

        # Update payment (paid_at already set earlier when payment was verified)
        payment.enrollment_id = enrollment
        # Status, payment IDs, and paid_at already set earlier, just update enrollment_id
        payment.updated_at = datetime.utcnow()
        payment.save()

        # Create enrollment success notification
        try:
            from notifications.views import create_notification
            course_name = course.name if course else (category.name if category else "Course")
            create_notification(
                user=user,
                notification_type='enrollment',
                title='Enrollment Successful! 🎓',
                message=f'Congratulations! You are now enrolled in {course_name}. Start learning now!',
                link='/dashboard',
                metadata={'enrollment_id': str(enrollment.id), 'course_id': str(course.id) if course else None, 'category_id': str(category.id) if category else None}
            )
        except Exception as e:
            print(f"Error creating enrollment notification: {e}")

        # Note: User's enrolled_courses are already updated in the respective blocks above
        # (course_id block updates with course, category_id block updates with category)
        
        # Return response immediately to avoid delay
        response_data = {
            "success": True,
            "message": "Payment verified and enrollment created successfully",
            "enrollment_id": str(enrollment.id)
        }
        
        # Send emails asynchronously (non-blocking) to avoid delay
        try:
            import threading
            import traceback
            from .email_utils import send_enrollment_confirmation_email, send_invoice_email
            
            def send_emails_async():
                try:
                    if user and user.email:
                        print(f"Attempting to send enrollment email to: {user.email}")
                        
                        # Send enrollment confirmation email
                        email_sent = send_enrollment_confirmation_email(
                            user_email=user.email,
                            user_name=user.fullname or "Student",
                            category_name=category.name,
                            enrolled_date=enrollment.enrolled_date,
                            expiry_date=enrollment.expiry_date
                        )
                        
                        if email_sent:
                            print(f"✓ Enrollment confirmation email sent to {user.email}")
                        else:
                            print(f"✗ Failed to send enrollment confirmation email to {user.email}")
                        
                        # Send invoice email
                        payment_details = {
                            "payment_id": str(payment.id),
                            "amount": payment.amount,
                            "currency": payment.currency,
                            "payment_method": payment.payment_method,
                            "razorpay_payment_id": payment.razorpay_payment_id,
                            "razorpay_order_id": payment.razorpay_order_id,
                            "paid_at": payment.paid_at
                        }
                        enrollment_details = {
                            "category_name": category.name,
                            "duration_months": duration_months
                        }
                        
                        invoice_sent = send_invoice_email(
                            user_email=user.email,
                            user_name=user.fullname or "Student",
                            payment_details=payment_details,
                            enrollment_details=enrollment_details
                        )
                        
                        if invoice_sent:
                            print(f"✓ Invoice email sent to {user.email}")
                        else:
                            print(f"✗ Failed to send invoice email to {user.email}")
                    else:
                        print(f"Warning: User or user email not found. User: {user}, Email: {user.email if user else 'N/A'}")
                except Exception as e:
                    print(f"Error sending emails asynchronously: {e}")
                    print(traceback.format_exc())
            
            # Start email sending in background thread
            email_thread = threading.Thread(target=send_emails_async)
            email_thread.daemon = True
            email_thread.start()
            print("Email thread started")
        except Exception as e:
            print(f"Error setting up email thread: {e}")
            import traceback
            print(traceback.format_exc())
            # Don't fail the enrollment if email setup fails

        return JsonResponse(response_data, status=200)

    except Payment.DoesNotExist:
        return JsonResponse({"success": False, "message": "Payment not found"}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ==================== NEWSLETTER VIEWS ====================

from .newsletter_models import Newsletter
from datetime import datetime

@csrf_exempt
@authenticate
@restrict("admin")
def create_newsletter(request):
    """Admin-only: Create a new newsletter"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        subject = data.get("subject")
        content = data.get("content")
        sent_to_purchased_users = data.get("sent_to_purchased_users", True)

        if not subject or not content:
            return JsonResponse({"success": False, "message": "Subject and content are required"}, status=400)

        newsletter = Newsletter(
            subject=subject,
            content=content,
            sent_to_purchased_users=sent_to_purchased_users,
            is_sent=False
        )
        newsletter.save()

        return JsonResponse({
            "success": True,
            "message": "Newsletter created successfully",
            "data": {
                "id": str(newsletter.id),
                "subject": newsletter.subject,
                "sent_to_purchased_users": newsletter.sent_to_purchased_users,
                "created_at": str(newsletter.created_at)
            }
        }, status=201)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict("admin")
def send_newsletter(request, newsletter_id):
    """Admin-only: Send newsletter to all purchased users"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        newsletter = Newsletter.objects.get(id=ObjectId(newsletter_id))
        
        if newsletter.is_sent:
            return JsonResponse({"success": False, "message": "Newsletter has already been sent"}, status=400)

        # Get all users who have made purchases (have completed payments)
        from .payment_models import Payment
        completed_payments = Payment.objects(status="completed")
        
        # Get unique user IDs from payments
        user_ids = set()
        for payment in completed_payments:
            user_ids.add(payment.user_id)
        
        # Get user details and send emails
        sent_count = 0
        failed_count = 0
        
        from .email_utils import send_newsletter_email
        
        for user_id in user_ids:
            try:
                if ObjectId.is_valid(user_id):
                    user = User.objects(id=ObjectId(user_id)).first()
                else:
                    user = User.objects(id=user_id).first()
                
                if user and user.email:
                    send_newsletter_email(
                        user_email=user.email,
                        user_name=user.fullname,
                        subject=newsletter.subject,
                        content=newsletter.content
                    )
                    sent_count += 1
            except Exception as e:
                print(f"Error sending newsletter to user {user_id}: {e}")
                failed_count += 1

        # Update newsletter
        newsletter.is_sent = True
        newsletter.sent_count = sent_count
        newsletter.sent_at = datetime.utcnow()
        newsletter.save()

        return JsonResponse({
            "success": True,
            "message": f"Newsletter sent to {sent_count} users",
            "data": {
                "sent_count": sent_count,
                "failed_count": failed_count,
                "sent_at": str(newsletter.sent_at)
            }
        }, status=200)

    except Newsletter.DoesNotExist:
        return JsonResponse({"success": False, "message": "Newsletter not found"}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict("admin")
def get_newsletters(request):
    """Admin-only: Get all newsletters"""
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        newsletters = Newsletter.objects.all().order_by("-created_at")
        
        newsletters_data = []
        for newsletter in newsletters:
            newsletters_data.append({
                "id": str(newsletter.id),
                "subject": newsletter.subject,
                "content": newsletter.content,
                "sent_to_purchased_users": newsletter.sent_to_purchased_users,
                "sent_count": newsletter.sent_count,
                "is_sent": newsletter.is_sent,
                "created_at": str(newsletter.created_at),
                "sent_at": str(newsletter.sent_at) if newsletter.sent_at else None
            })

        return JsonResponse({
            "success": True,
            "count": len(newsletters_data),
            "data": newsletters_data
        }, status=200)

    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict("admin")
def get_newsletter_detail(request, newsletter_id):
    """Admin-only: Get a single newsletter by ID"""
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        newsletter = Newsletter.objects.get(id=ObjectId(newsletter_id))
        
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(newsletter.id),
                "subject": newsletter.subject,
                "content": newsletter.content,
                "sent_to_purchased_users": newsletter.sent_to_purchased_users,
                "sent_count": newsletter.sent_count,
                "is_sent": newsletter.is_sent,
                "created_at": str(newsletter.created_at),
                "sent_at": str(newsletter.sent_at) if newsletter.sent_at else None
            }
        }, status=200)

    except Newsletter.DoesNotExist:
        return JsonResponse({"success": False, "message": "Newsletter not found"}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict("admin")
def delete_newsletter(request, newsletter_id):
    """Admin-only: Delete a newsletter"""
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        newsletter = Newsletter.objects.get(id=ObjectId(newsletter_id))
        
        if newsletter.is_sent:
            return JsonResponse({"success": False, "message": "Cannot delete a newsletter that has already been sent"}, status=400)
        
        newsletter.delete()

        return JsonResponse({
            "success": True,
            "message": "Newsletter deleted successfully"
        }, status=200)

    except Newsletter.DoesNotExist:
        return JsonResponse({"success": False, "message": "Newsletter not found"}, status=404)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)

     