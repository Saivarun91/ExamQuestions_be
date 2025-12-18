# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Course
# from .serializers import CourseSerializer
# from bson import ObjectId
# from common.middleware import authenticate, restrict
# from django.views.decorators.csrf import csrf_exempt


# # ✅ List all active courses (for FeaturedExams)
# @api_view(['GET'])
# @permission_classes([AllowAny])
# @csrf_exempt
# def course_list(request):
#     """Get all active courses for public display"""
#     try:
#         courses = Course.objects(is_active=True).order_by('-created_at')
#         serializer = CourseSerializer(courses, many=True)
#         return Response(serializer.data)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get all courses (Admin)
# @api_view(['GET'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def admin_course_list(request):
#     """Get all courses for admin management"""
#     try:
#         courses = Course.objects.all().order_by('-created_at')
#         serializer = CourseSerializer(courses, many=True)
#         return Response({"success": True, "data": serializer.data})
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Create a new course (Admin)
# @api_view(['POST'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def course_create(request):
#     """Admin: Create a new course"""
#     try:
#         from providers.models import Provider
#         from categories.models import Category
        
#         data = request.data
        
#         # Validate required fields
#         required_fields = ['provider', 'title', 'code', 'slug']
#         for field in required_fields:
#             if field not in data:
#                 return Response(
#                     {"error": f"{field} is required"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
        
#         # Get provider reference - accept both ID and name
#         provider_input = data['provider']
#         try:
#             if ObjectId.is_valid(provider_input):
#                 provider = Provider.objects.get(id=ObjectId(provider_input))
#             else:
#                 # Try to find by name or slug
#                 try:
#                     provider = Provider.objects.get(name=provider_input)
#                 except Provider.DoesNotExist:
#                     provider = Provider.objects.get(slug=provider_input)
#         except Provider.DoesNotExist:
#             return Response(
#                 {"error": f"Provider '{provider_input}' not found"},
#                 status=status.HTTP_400_BAD_REQUEST
#             )
        
#         # Get category reference if provided - accept both ID and title
#         category = None
#         if data.get('category'):
#             category_input = data['category']
#             try:
#                 if ObjectId.is_valid(category_input):
#                     category = Category.objects.get(id=ObjectId(category_input))
#                 else:
#                     # Try to find by title or slug
#                     try:
#                         category = Category.objects.get(title=category_input)
#                     except Category.DoesNotExist:
#                         category = Category.objects.get(slug=category_input)
#             except Category.DoesNotExist:
#                 return Response(
#                     {"error": f"Category '{category_input}' not found"},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )
        
#         # Create course
#         course = Course(
#             provider=provider,
#             title=data['title'],
#             code=data['code'],
#             slug=data['slug'],
#             practice_exams=data.get('practice_exams', 0),
#             questions=data.get('questions', 0),
#             badge=data.get('badge', None),
#             category=category,
#             meta_title=data.get('meta_title', None),
#             meta_keywords=data.get('meta_keywords', None),
#             meta_description=data.get('meta_description', None),
#         )
#         course.save()
        
#         serializer = CourseSerializer(course)
#         return Response(
#             {"success": True, "message": "Course created successfully", "data": serializer.data},
#             status=status.HTTP_201_CREATED
#         )
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Retrieve a single course by ID or slug
# @api_view(['GET'])
# @permission_classes([AllowAny])
# @csrf_exempt
# def course_detail(request, course_identifier):
#     """Get course by ID or slug"""
#     try:
#         from urllib.parse import unquote
#         from providers.models import Provider
        
#         # URL decode the identifier in case it was encoded
#         course_identifier = unquote(course_identifier)
        
#         # Try to find by ObjectId first
#         if ObjectId.is_valid(course_identifier):
#             course = Course.objects.get(id=ObjectId(course_identifier))
#         else:
#             # Try to find by slug (exact match)
#             try:
#             course = Course.objects.get(slug=course_identifier)
#             except Course.DoesNotExist:
#                 # Try to parse as provider-code format (e.g., "aws-saa-c03")
#                 parts = course_identifier.split('-', 1)
#                 if len(parts) == 2:
#                     provider_slug = parts[0]
#                     code = parts[1].upper()
                    
#                     # Find provider by slug or name
#                     try:
#                         provider = Provider.objects.get(slug=provider_slug)
#                     except Provider.DoesNotExist:
#                         try:
#                             provider = Provider.objects.get(name__iexact=provider_slug)
#                         except Provider.DoesNotExist:
#                             raise Course.DoesNotExist()
                    
#                     # Find course by provider and code
#                     course = Course.objects.get(provider=provider, code__iexact=code)
#                 else:
#                     raise Course.DoesNotExist()
        
#         serializer = CourseSerializer(course)
#         return Response(serializer.data)
#     except Course.DoesNotExist:
#         return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Update a course (Admin)
# @api_view(['PUT'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def course_update(request, course_id):
#     """Admin: Update a course"""
#     try:
#         if not ObjectId.is_valid(course_id):
#             return Response({"error": "Invalid course ID"}, status=status.HTTP_400_BAD_REQUEST)
        
#         course = Course.objects.get(id=ObjectId(course_id))
#         data = request.data
#         print("=" * 50)
#         print("Updating course:", course.title)
#         print("Received data keys:", list(data.keys()))
#         print("Sample data:", {k: v for k, v in list(data.items())[:5]})
#         print("=" * 50)
        
#         # Update fields only if provided
#         if 'provider' in data:
#             from providers.models import Provider
#             provider_input = data['provider']
#             if provider_input:
#                 try:
#                     if ObjectId.is_valid(provider_input):
#                         provider = Provider.objects.get(id=ObjectId(provider_input))
#                     else:
#                         # Try to find by name or slug
#                         try:
#                             provider = Provider.objects.get(name=provider_input)
#                         except Provider.DoesNotExist:
#                             provider = Provider.objects.get(slug=provider_input)
#                     course.provider = provider
#                 except Provider.DoesNotExist:
#                     return Response(
#                         {"error": f"Provider '{provider_input}' not found"},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
        
#         if 'title' in data:
#             course.title = data['title']
#         if 'code' in data:
#             course.code = data['code']
#         if 'slug' in data:
#             course.slug = data['slug']
#         if 'practice_exams' in data:
#             course.practice_exams = int(data['practice_exams']) if data['practice_exams'] else 0
#         if 'questions' in data:
#             course.questions = int(data['questions']) if data['questions'] else 0
#         if 'badge' in data:
#             course.badge = data['badge'] if data['badge'] else None
#         if 'category' in data:
#             from categories.models import Category
#             category_input = data['category']
#             if category_input:
#                 try:
#                     if ObjectId.is_valid(category_input):
#                         category = Category.objects.get(id=ObjectId(category_input))
#                     else:
#                         # Try to find by title or slug
#                         try:
#                             category = Category.objects.get(title=category_input)
#                         except Category.DoesNotExist:
#                             category = Category.objects.get(slug=category_input)
#                     course.category = category
#                 except Category.DoesNotExist:
#                     return Response(
#                         {"error": f"Category '{category_input}' not found"},
#                         status=status.HTTP_400_BAD_REQUEST
#                     )
#             else:
#                 course.category = None
#         if 'meta_title' in data:
#             course.meta_title = data['meta_title'] if data['meta_title'] else None
#         if 'meta_keywords' in data:
#             course.meta_keywords = data['meta_keywords'] if data['meta_keywords'] else None
#         if 'meta_description' in data:
#             course.meta_description = data['meta_description'] if data['meta_description'] else None
#         if 'is_active' in data:
#             course.is_active = bool(data['is_active'])
        
#         # ✅ Update exam details fields
#         if 'about' in data:
#             course.about = data['about'] if data['about'] else None
#         if 'eligibility' in data:
#             course.eligibility = data['eligibility'] if data['eligibility'] else None
#         if 'exam_pattern' in data:
#             course.exam_pattern = data['exam_pattern'] if data['exam_pattern'] else None
#         if 'pass_rate' in data:
#             course.pass_rate = int(data['pass_rate']) if data['pass_rate'] else None
#         if 'rating' in data:
#             course.rating = float(data['rating']) if data['rating'] else None
#         if 'difficulty' in data:
#             course.difficulty = data['difficulty'] if data['difficulty'] else None
#         if 'duration' in data:
#             course.duration = data['duration'] if data['duration'] else None
#         if 'passing_score' in data:
#             course.passing_score = data['passing_score'] if data['passing_score'] else None
#         if 'why_matters' in data:
#             course.why_matters = data['why_matters'] if data['why_matters'] else None
        
#         # ✅ Update list fields
#         if 'whats_included' in data:
#             course.whats_included = data['whats_included'] if isinstance(data['whats_included'], list) else []
#         if 'topics' in data:
#             course.topics = data['topics'] if isinstance(data['topics'], list) else []
#         if 'practice_tests_list' in data:
#             course.practice_tests_list = data['practice_tests_list'] if isinstance(data['practice_tests_list'], list) else []
#         if 'testimonials' in data:
#             course.testimonials = data['testimonials'] if isinstance(data['testimonials'], list) else []
#         if 'faqs' in data:
#             course.faqs = data['faqs'] if isinstance(data['faqs'], list) else []
#         if 'test_instructions' in data:
#             course.test_instructions = data['test_instructions'] if isinstance(data['test_instructions'], list) else []
#         if 'test_description' in data:
#             course.test_description = data['test_description'] if data['test_description'] else None
        
#         import datetime
#         course.updated_at = datetime.datetime.utcnow()
#         course.save()
        
#         # ✅ Sync practice_tests_list to PracticeTest collection
#         if 'practice_tests_list' in data and isinstance(data['practice_tests_list'], list):
#             from practice_tests.models import PracticeTest
#             from django.utils.text import slugify
            
#             synced_tests = []
#             for test_data in data['practice_tests_list']:
#                 if not test_data.get('name'):
#                     continue  # Skip tests without a name
                
#                 try:
#                     # Generate slug from test name
#                     test_name = test_data.get('name', '')
#                     base_slug = slugify(test_name)
                    
#                     # Try to find existing test by name for this course
#                     existing_test = PracticeTest.objects(title=test_name, course=course).first()
                    
#                     if existing_test:
#                         # Update existing test
#                         practice_test = existing_test
#                         print(f"   📝 Updating existing test: {test_name}")
#                     else:
#                         # Create new test with unique slug
#                         slug = base_slug
#                         counter = 1
#                         max_checks = 100
                        
#                         # Ensure slug is unique for this course
#                         while counter <= max_checks:
#                             if not PracticeTest.objects(slug=slug, course=course).first():
#                                 break
#                             slug = f"{base_slug}-{counter}"
#                             counter += 1
                        
#                         if counter > max_checks:
#                             # Use ObjectId for uniqueness if needed
#                             slug = f"{base_slug}-{ObjectId()}"
                        
#                         practice_test = PracticeTest(
#                             slug=slug,
#                             title=test_name,
#                             course=course,
#                             category=course.category if hasattr(course, 'category') else None
#                         )
#                         print(f"   ✨ Creating new test: {test_name} (slug: {slug})")
                    
#                     # Update test fields
#                     practice_test.questions = int(test_data.get('questions', 0))
#                     practice_test.duration = int(test_data.get('duration', 0)) if test_data.get('duration') else 0
#                     practice_test.difficulty_level = test_data.get('difficulty', 'Intermediate')
#                     practice_test.overview = test_data.get('description', '')
                    
#                     # Save the practice test
#                     practice_test.updated_at = datetime.datetime.utcnow()
#                     practice_test.save()
                    
#                     synced_tests.append({
#                         'name': practice_test.title,
#                         'slug': practice_test.slug,
#                         'id': str(practice_test.id)
#                     })
                    
#                 except Exception as e:
#                     print(f"   ⚠️  Error syncing test '{test_data.get('name')}': {str(e)}")
#                     # Continue with other tests even if one fails
#                     continue
            
#             print(f"   ✅ Synced {len(synced_tests)} practice tests to PracticeTest collection")
#             print(f"   Tests: {[t['name'] for t in synced_tests]}")
        
#         # Reload the course from database to ensure we get the saved data
#         course.reload()
        
#         serializer = CourseSerializer(course)
#         print("=" * 50)
#         print("Course updated successfully!")
#         print("Saved topics count:", len(course.topics) if course.topics else 0)
#         print("Saved testimonials count:", len(course.testimonials) if course.testimonials else 0)
#         print("Saved FAQs count:", len(course.faqs) if course.faqs else 0)
#         print("=" * 50)
        
#         return Response({"success": True, "message": "Course updated successfully", "data": serializer.data})
#     except Course.DoesNotExist:
#         return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         import traceback
#         error_trace = traceback.format_exc()
#         print(f"Error updating course: {error_trace}")
#         return Response({"error": str(e), "details": error_trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Delete a course (Admin)
# @api_view(['DELETE'])
# @authenticate
# @restrict(['admin'])
# @csrf_exempt
# def course_delete(request, course_id):
#     """Admin: Delete a course"""
#     try:
#         if not ObjectId.is_valid(course_id):
#             return Response({"error": "Invalid course ID"}, status=status.HTTP_400_BAD_REQUEST)
        
#         course = Course.objects.get(id=ObjectId(course_id))
#         course.delete()
#         return Response(
#             {"success": True, "message": "Course deleted successfully"},
#             status=status.HTTP_200_OK
#         )
#     except Course.DoesNotExist:
#         return Response({"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# # ✅ Get courses by category
# @api_view(['GET'])
# @permission_classes([AllowAny])
# @csrf_exempt
# def courses_by_category(request, category_slug):
#     """Get all courses for a specific category"""
#     try:
#         from categories.models import Category
        
#         # First find the category by slug
#         try:
#             category = Category.objects.get(slug=category_slug)
#         except Category.DoesNotExist:
#             return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Find courses that reference this category
#         courses = Course.objects(category=category, is_active=True).order_by('-created_at')
#         serializer = CourseSerializer(courses, many=True)
#         return Response(serializer.data)
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import datetime

from bson import ObjectId
from common.middleware import authenticate, restrict

from .models import Course
from .serializers import CourseSerializer


# ------------------------------------------------------------
# ✅ PUBLIC: Get all active courses
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def course_list(request):
    """Get all active courses for public display"""
    try:
        from practice_tests.models import PracticeTest
        
        courses = Course.objects(is_active=True).order_by('-created_at')
        
        # ✅ AUTO-SYNC: Ensure practice_exams and questions counts are accurate for each course
        from questions.models import Question
        for course in courses:
            practice_test_count = PracticeTest.objects(course=course).count()
            question_count = Question.objects(course=course).count()
            if course.practice_exams != practice_test_count or course.questions != question_count:
                course.practice_exams = practice_test_count
                course.questions = question_count
                course.save()
        
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Get all courses
# ------------------------------------------------------------
@api_view(['GET'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_course_list(request):
    try:
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        courses = Course.objects.all().order_by('-created_at')
        
        # ✅ AUTO-SYNC: Ensure counts are accurate for each course
        for course in courses:
            # Sync practice_exams count
            practice_test_count = PracticeTest.objects(course=course).count()
            if course.practice_exams != practice_test_count:
                course.practice_exams = practice_test_count
            
            # Sync questions count
            question_count = Question.objects(course=course).count()
            if course.questions != question_count:
                course.questions = question_count
            
            # Save if any changes
            if course.practice_exams != practice_test_count or course.questions != question_count:
                course.save()
        
        serializer = CourseSerializer(courses, many=True)
        return Response({"success": True, "data": serializer.data})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Create Course
# ------------------------------------------------------------
@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_create(request):
    """Admin: Create new course"""
    try:
        from providers.models import Provider
        from categories.models import Category

        data = request.data

        # Required fields
        required_fields = ['provider', 'title', 'code', 'slug']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Provider (id or name or slug)
        provider_input = data['provider']
        try:
            if ObjectId.is_valid(provider_input):
                provider = Provider.objects.get(id=ObjectId(provider_input))
            else:
                try:
                    provider = Provider.objects.get(name=provider_input)
                except Provider.DoesNotExist:
                    provider = Provider.objects.get(slug=provider_input)
        except Provider.DoesNotExist:
            return Response({"error": f"Provider '{provider_input}' not found"}, status=400)

        # Category (optional)
        category = None
        if data.get('category'):
            category_input = data['category']
            try:
                if ObjectId.is_valid(category_input):
                    category = Category.objects.get(id=ObjectId(category_input))
                else:
                    try:
                        category = Category.objects.get(title=category_input)
                    except Category.DoesNotExist:
                        category = Category.objects.get(slug=category_input)
            except Category.DoesNotExist:
                return Response({"error": f"Category '{category_input}' not found"}, status=400)

        # ✅ AUTO-SYNC: If category is assigned, automatically mark as featured
        # If is_featured is explicitly set, use that; otherwise, mark as featured if category exists
        is_featured = data.get('is_featured', False)
        if category and not is_featured:
            is_featured = True  # Auto-mark as featured when category is assigned

        # ✅ AUTO-CALCULATE: Get actual counts from related documents
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        # ✅ Normalize slug for SEO-friendly URLs (use hyphens, not underscores)
        slug = data['slug'].replace('_', '-').lower()
        
        # Create course first (with 0 counts, will be updated)
        course = Course(
            provider=provider,
            title=data['title'],
            code=data['code'],
            slug=slug,  # Use normalized slug
            practice_exams=0,  # Will be auto-calculated
            questions=0,  # Will be auto-calculated
            badge=data.get('badge'),
            category=category,
            actual_price=float(data.get('actual_price', 0)),
            offer_price=float(data.get('offer_price', 0)),
            currency=data.get('currency', 'INR'),
            is_featured=is_featured,
            meta_title=data.get('meta_title'),
            meta_keywords=data.get('meta_keywords'),
            meta_description=data.get('meta_description'),
        )

        course.save()
        
        # ✅ AUTO-SYNC: Calculate and update counts from related documents
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        course.practice_exams = practice_test_count
        course.questions = question_count
        course.save()
        
        serializer = CourseSerializer(course)
        return Response({"success": True, "message": "Course created successfully", "data": serializer.data}, status=201)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get course by ID or slug
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def course_detail(request, course_identifier):
    """Get course by ID or slug - SEO-friendly URL support"""
    try:
        from urllib.parse import unquote
        from providers.models import Provider

        course_identifier = unquote(course_identifier)
        # Normalize identifier: convert to lowercase and replace underscores with hyphens for SEO
        course_identifier = course_identifier.lower().replace('_', '-')

        # 1️⃣ Try by ID
        if ObjectId.is_valid(course_identifier):
            course = Course.objects.get(id=ObjectId(course_identifier))

        else:
            course = None
            # 2️⃣ Try by slug (exact match first) - SEO-friendly URL
            try:
                course = Course.objects.get(slug=course_identifier)
            except Course.DoesNotExist:
                # 2b️⃣ Try by slug with case-insensitive match
                try:
                    course = Course.objects.get(slug__iexact=course_identifier)
                except Course.DoesNotExist:
                    # 3️⃣ Try provider-code format → example: aws-saa-c03 or sap-se-c-bw4h-2505
                    # SEO URLs should use hyphens, normalize underscores to hyphens
                    normalized_identifier = course_identifier.replace('_', '-')
                    
                    # Split by hyphens - need to handle multi-word providers
                    # For "sap-se-c-bw4h-2505", provider might be "sap-se" and code "c-bw4h-2505"
                    # Or provider might be "sap" and code "se-c-bw4h-2505"
                    # Try multiple split strategies
                    if '-' in normalized_identifier:
                        all_parts = normalized_identifier.split('-')
                        provider = None
                        provider_slug = None
                        code_part = None
                        
                        # Strategy 1: Try two-word provider first (e.g., "sap-se")
                        if len(all_parts) >= 3:
                            provider_slug_alt = f"{all_parts[0]}-{all_parts[1]}"
                            code_part_alt = '-'.join(all_parts[2:])
                            
                            # Try to find provider with two-word slug
                            provider_variants_alt = [
                                provider_slug_alt,
                                provider_slug_alt.upper(),
                                provider_slug_alt.capitalize(),
                                provider_slug_alt.replace('-', ' '),
                                provider_slug_alt.replace('-', ' ').title(),
                            ]
                            
                            for variant in provider_variants_alt:
                                try:
                                    provider = Provider.objects.get(slug=variant)
                                    provider_slug = provider_slug_alt
                                    code_part = code_part_alt
                                    break
                                except Provider.DoesNotExist:
                                    try:
                                        provider = Provider.objects.get(name__iexact=variant)
                                        provider_slug = provider_slug_alt
                                        code_part = code_part_alt
                                        break
                                    except Provider.DoesNotExist:
                                        continue
                        
                        # Strategy 2: Try single-word provider (e.g., "sap")
                        if not provider and len(all_parts) >= 2:
                            provider_slug = all_parts[0]
                            code_part = '-'.join(all_parts[1:])
                            
                            provider_variants = [
                                provider_slug,
                                provider_slug.upper(),
                                provider_slug.capitalize(),
                                provider_slug.replace('-', ' '),
                                provider_slug.replace('-', ' ').title(),
                            ]
                            
                            for variant in provider_variants:
                                try:
                                    provider = Provider.objects.get(slug=variant)
                                    break
                                except Provider.DoesNotExist:
                                    try:
                                        provider = Provider.objects.get(name__iexact=variant)
                                        break
                                    except Provider.DoesNotExist:
                                        continue
                            
                            # If still not found, try partial match
                            if not provider:
                                try:
                                    providers = Provider.objects.filter(slug__icontains=provider_slug)
                                    if providers.count() == 1:
                                        provider = providers.first()
                                except Exception:
                                    pass
                        
                        # Now try to find course with the found provider
                        if provider and code_part:
                            # Try multiple code format variations
                            # The code might be stored as: SE-C_BW4H_2505, SE-C-BW4H-2505, SE-C-BW4H_2505, etc.
                            code_variants = [
                                code_part.upper(),  # se-c-bw4h-2505 -> SE-C-BW4H-2505
                                code_part.upper().replace('-', '_'),  # SE-C_BW4H_2505
                                code_part.upper().replace('_', '-'),  # SE-C-BW4H-2505
                                code_part,  # se-c-bw4h-2505
                                code_part.replace('-', '_').upper(),  # SE_C_BW4H_2505
                            ]
                            
                            # Try to find course by provider and code (try all variants)
                            for code_variant in code_variants:
                                try:
                                    course = Course.objects.get(provider=provider, code__iexact=code_variant)
                                    break
                                except Course.DoesNotExist:
                                    continue
                            
                            # If not found by code, try by slug variations
                            if not course:
                                slug_variants = [
                                    f"{provider_slug}-{code_part.lower()}",  # sap-se-c-bw4h-2505
                                    f"{provider_slug}-{code_part.lower().replace('_', '-')}",  # normalize underscores
                                    course_identifier,  # original identifier
                                    normalized_identifier,  # normalized identifier
                                ]
                                
                                for slug_variant in slug_variants:
                                    try:
                                        course = Course.objects.get(provider=provider, slug=slug_variant)
                                        break
                                    except Course.DoesNotExist:
                                        try:
                                            course = Course.objects.get(provider=provider, slug__iexact=slug_variant)
                                            break
                                        except Course.DoesNotExist:
                                            continue
                            
                            # Last resort: try to find any course with this provider and matching slug pattern
                            if not course:
                                try:
                                    # Try partial slug match
                                    courses = Course.objects.filter(provider=provider, slug__icontains=code_part.lower())
                                    if courses.count() == 1:
                                        course = courses.first()
                                except Exception:
                                    pass
                    
                    # Final fallback: Try to find by slug pattern (case-insensitive, partial match)
                    if not course:
                        try:
                            # Try exact slug match (case-insensitive)
                            course = Course.objects.get(slug__iexact=course_identifier)
                        except Course.DoesNotExist:
                            try:
                                # Try normalized slug match
                                course = Course.objects.get(slug__iexact=normalized_identifier)
                            except Course.DoesNotExist:
                                try:
                                    # Try slug containing the identifier
                                    courses = Course.objects.filter(slug__icontains=course_identifier.lower())
                                    if courses.count() == 1:
                                        course = courses.first()
                                except Exception:
                                    pass
                    
                    # Ultimate fallback: Search all courses by code pattern
                    if not course and '-' in normalized_identifier:
                        # Extract potential code from the identifier
                        # For "sap-se-c-bw4h-2505", try to find course with code containing "se-c" or "bw4h"
                        code_parts = normalized_identifier.split('-')
                        if len(code_parts) >= 2:
                            # Try to find by code pattern (e.g., "SE-C" or "BW4H")
                            # Build code variations: "se-c-bw4h-2505" -> ["SE-C-BW4H-2505", "SE-C", "BW4H", "2505"]
                            code_variations = []
                            
                            # Full code (uppercase)
                            full_code = '-'.join(code_parts[1:]).upper()
                            code_variations.append(full_code)
                            
                            # Code with underscores
                            code_variations.append(full_code.replace('-', '_'))
                            
                            # Individual meaningful parts
                            for part in code_parts[1:]:
                                if len(part) >= 2 and part.isalnum():
                                    code_variations.append(part.upper())
                            
                            # Try each variation
                            for code_var in code_variations:
                                try:
                                    courses = Course.objects.filter(code__icontains=code_var)
                                    if courses.count() == 1:
                                        course = courses.first()
                                        break
                                    elif courses.count() > 1:
                                        # If multiple matches, try to find one with matching slug pattern
                                        for c in courses:
                                            c_slug_lower = c.slug.lower()
                                            identifier_lower = normalized_identifier.lower()
                                            if identifier_lower in c_slug_lower or c_slug_lower in identifier_lower:
                                                course = c
                                                break
                                        if course:
                                            break
                                except Exception:
                                    continue
                            
                            # Last resort: search by slug containing any part of the code
                            if not course:
                                for code_var in code_variations[:3]:  # Try first 3 variations
                                    try:
                                        courses = Course.objects.filter(slug__icontains=code_var.lower())
                                        if courses.count() == 1:
                                            course = courses.first()
                                            break
                                    except Exception:
                                        continue
                    
                    # If still not found, raise DoesNotExist
                    if not course:
                        # Log for debugging
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Course not found for identifier: {course_identifier}")
                        raise Course.DoesNotExist()

        # Ensure course was found
        if not course:
                    raise Course.DoesNotExist()

        # ✅ AUTO-SYNC: Ensure counts are accurate
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        if course.practice_exams != practice_test_count or course.questions != question_count:
            course.practice_exams = practice_test_count
            course.questions = question_count
            course.save()

        serializer = CourseSerializer(course)
        return Response(serializer.data)

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ ADMIN: Update Course
# ------------------------------------------------------------
@api_view(['PUT'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_update(request, course_id):
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))
        data = request.data

        # Update category if provided
        if 'category' in data:
            from categories.models import Category
            category_input = data['category']
            try:
                if ObjectId.is_valid(category_input):
                    category = Category.objects.get(id=ObjectId(category_input))
                else:
                    try:
                        category = Category.objects.get(title=category_input)
                    except Category.DoesNotExist:
                        category = Category.objects.get(slug=category_input)
                course.category = category
                # ✅ AUTO-SYNC: If category is assigned, automatically mark as featured
                if not course.is_featured:
                    course.is_featured = True
            except Category.DoesNotExist:
                return Response({"error": f"Category '{category_input}' not found"}, status=400)

        # Update fields
        if 'title' in data:
            course.title = data['title']
        if 'code' in data:
            course.code = data['code']
        if 'slug' in data:
            # ✅ Normalize slug for SEO-friendly URLs (use hyphens, not underscores)
            course.slug = data['slug'].replace('_', '-').lower()
        if 'questions' in data:
            course.questions = int(data['questions'])
        if 'practice_exams' in data:
            course.practice_exams = int(data['practice_exams'])
        if 'badge' in data:
            course.badge = data['badge']
        
        # Update pricing fields
        if 'actual_price' in data:
            course.actual_price = float(data['actual_price']) if data['actual_price'] else 0.0
        if 'offer_price' in data:
            course.offer_price = float(data['offer_price']) if data['offer_price'] else 0.0
        if 'currency' in data:
            course.currency = data['currency']
        if 'is_featured' in data:
            course.is_featured = bool(data['is_featured'])
            # ✅ AUTO-SYNC: If marked as featured, ensure it has a category
            if course.is_featured and not course.category:
                # Try to find a default category or use the first available category
                from categories.models import Category
                default_category = Category.objects.first()
                if default_category:
                    course.category = default_category
        if 'is_active' in data:
            course.is_active = bool(data['is_active'])

        # Update metadata
        course.meta_title = data.get('meta_title')
        course.meta_keywords = data.get('meta_keywords')
        course.meta_description = data.get('meta_description')

        # Update extra details
        for field in ["about", "eligibility", "exam_pattern", "difficulty", "duration", "passing_score", "why_matters"]:
            if field in data:
                setattr(course, field, data[field])

        # List fields (excluding practice_tests_list - handled separately)
        for field in ["whats_included", "topics", "testimonials", "faqs", "test_instructions"]:
            if field in data and isinstance(data[field], list):
                setattr(course, field, data[field])

        # ✅ AUTO-SYNC: Sync practice_tests_list to PracticeTest collection and update references
        if 'practice_tests_list' in data and isinstance(data['practice_tests_list'], list):
            from practice_tests.models import PracticeTest
            from django.utils.text import slugify
            import datetime
            from pymongo.errors import DuplicateKeyError
            
            synced_tests = []
            for test_data in data['practice_tests_list']:
                if not test_data.get('name'):
                    continue  # Skip tests without a name
                
                try:
                    # Generate slug from test name
                    test_name = test_data.get('name', '')
                    base_slug = slugify(test_name)
                    
                    # Try to find existing test by ID first (if provided), then by name AND course
                    existing_test = None
                    test_id = test_data.get('id')
                    
                    # If ID is provided and looks like a MongoDB ObjectId, try to find by ID
                    if test_id and ObjectId.is_valid(str(test_id)):
                        try:
                            existing_test = PracticeTest.objects(id=ObjectId(test_id), course=course).first()
                        except:
                            pass  # If lookup fails, continue to name-based lookup
                    
                    # If not found by ID, try by name AND course (ensures course-specific lookup)
                    if not existing_test:
                        existing_test = PracticeTest.objects(title=test_name, course=course).first()
                    
                    if existing_test:
                        # Update existing test for this course
                        practice_test = existing_test
                        print(f"   📝 Updating existing test '{test_name}' for course '{course.title}'")
                    else:
                        # Create new test with unique slug for this course
                        # First try with simple slug (relying on composite index for uniqueness per course)
                        slug = base_slug
                        counter = 1
                        max_checks = 100
                        
                        # Ensure slug is unique for this specific course
                        while counter <= max_checks:
                            existing_by_slug = PracticeTest.objects(slug=slug, course=course).first()
                            if not existing_by_slug:
                                # Also check if slug exists globally (in case of single-field index)
                                # If it exists in another course, we can still use it (composite index allows this)
                                # But if there's a single-field index issue, we'll handle it in the save retry
                                break
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        if counter > max_checks:
                            # Use ObjectId for uniqueness if needed
                            slug = f"{base_slug}-{ObjectId()}"
                        
                        practice_test = PracticeTest(
                            slug=slug,
                            title=test_name,
                            course=course,
                            category=course.category if hasattr(course, 'category') and course.category else None
                        )
                        print(f"   ✨ Creating new test '{test_name}' for course '{course.title}' (slug: {slug})")
                    
                    # Update test fields (including title to ensure it matches the sent data)
                    # Always update title with the value from the request
                    if test_name:
                        practice_test.title = test_name
                    
                    # Parse duration string (e.g., "90 minutes" -> 90)
                    duration_str = str(test_data.get('duration', '0'))
                    duration_int = 0
                    if duration_str:
                        # Extract numbers from duration string
                        import re
                        numbers = re.findall(r'\d+', duration_str)
                        if numbers:
                            duration_int = int(numbers[0])
                    
                    practice_test.questions = int(test_data.get('questions', 0))
                    practice_test.duration = duration_int
                    practice_test.difficulty_level = test_data.get('difficulty', 'Intermediate')
                    practice_test.overview = test_data.get('description', '')
                    
                    # Save the practice test with retry logic for duplicate key errors
                    practice_test.updated_at = datetime.datetime.utcnow()
                    
                    # Retry logic to handle any duplicate key errors (e.g., if single-field index exists on slug)
                    max_retries = 3
                    retry_count = 0
                    saved = False
                    
                    while retry_count < max_retries and not saved:
                        try:
                            practice_test.save()
                            saved = True
                        except DuplicateKeyError as dke:
                            retry_count += 1
                            if retry_count < max_retries:
                                # Generate a new unique slug by including course identifier
                                course_slug = slugify(course.slug) if course.slug else slugify(course.title)
                                # Use a short course identifier (first few chars of course slug or course ID)
                                course_id_short = str(course.id)[:8]  # Use first 8 chars of ObjectId
                                practice_test.slug = f"{course_slug}-{base_slug}-{course_id_short}"
                                print(f"   🔄 Retry {retry_count}: Generated course-specific slug due to duplicate key: {practice_test.slug}")
                            else:
                                # Last resort: use ObjectId for complete uniqueness
                                practice_test.slug = f"{base_slug}-{ObjectId()}"
                                print(f"   🔄 Final retry: Using ObjectId for slug: {practice_test.slug}")
                                try:
                                    practice_test.save()
                                    saved = True
                                except:
                                    raise  # Re-raise if still fails
                        except Exception as save_error:
                            # Check if it's a duplicate key error (might be wrapped)
                            if "duplicate key" in str(save_error).lower() or "E11000" in str(save_error):
                                retry_count += 1
                                if retry_count < max_retries:
                                    # Generate a new unique slug by including course identifier
                                    course_slug = slugify(course.slug) if course.slug else slugify(course.title)
                                    course_id_short = str(course.id)[:8]
                                    practice_test.slug = f"{course_slug}-{base_slug}-{course_id_short}"
                                    print(f"   🔄 Retry {retry_count}: Generated course-specific slug: {practice_test.slug}")
                                    continue
                            # For other errors, re-raise immediately
                            raise
                    
                    synced_tests.append({
                        'name': practice_test.title,
                        'slug': practice_test.slug,
                        'id': str(practice_test.id)
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Error syncing test '{test_data.get('name')}': {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other tests even if one fails
                    continue
            
            # ✅ Update practice_tests reference field in course document
            if synced_tests:
                # Get all synced PracticeTest objects
                synced_practice_test_ids = [st['id'] for st in synced_tests]
                synced_practice_tests = []
                for pt_id in synced_practice_test_ids:
                    try:
                        pt = PracticeTest.objects.get(id=ObjectId(pt_id))
                        synced_practice_tests.append(pt)
                    except PracticeTest.DoesNotExist:
                        continue
                
                # Update course's practice_tests reference field
                course.practice_tests = synced_practice_tests

        # ✅ AUTO-SYNC: Calculate and update counts from related documents
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        course.practice_exams = practice_test_count
        course.questions = question_count
        
        import datetime
        course.updated_at = datetime.datetime.utcnow()

        course.save()
        course.reload()

        serializer = CourseSerializer(course)
        return Response({"success": True, "message": "Course updated successfully", "data": serializer.data})

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ ADMIN: Delete Course
# ------------------------------------------------------------
@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_delete(request, course_id):
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))
        course.delete()

        return Response({"success": True, "message": "Course deleted successfully"})

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get courses by category
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def courses_by_category(request, category_slug):
    try:
        from categories.models import Category
        from practice_tests.models import PracticeTest

        category = Category.objects.get(slug=category_slug)
        courses = Course.objects(category=category, is_active=True).order_by('-created_at')

        # ✅ AUTO-SYNC: Ensure practice_exams count is accurate for each course
        for course in courses:
            actual_count = PracticeTest.objects(course=course).count()
            if course.practice_exams != actual_count:
                course.practice_exams = actual_count
                course.save()

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get featured courses for homepage
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def featured_courses(request):
    """Get all featured courses for homepage Featured Exams section"""
    try:
        from practice_tests.models import PracticeTest
        
        courses = Course.objects(is_active=True, is_featured=True).order_by('-created_at')
        
        # ✅ AUTO-SYNC: Ensure practice_exams count is accurate for each course
        for course in courses:
            try:
                actual_count = PracticeTest.objects(course=course).count()
                if course.practice_exams != actual_count:
                    course.practice_exams = actual_count
                    course.save()
            except Exception:
                pass  # Skip sync if it fails, continue with existing count
        
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Manage Pricing Data for a Course
# ------------------------------------------------------------
@api_view(['GET', 'PUT'])
@csrf_exempt
def manage_course_pricing(request, course_id):
    """
    GET: Fetch pricing data for a course
    PUT: Update pricing data for a course (Admin only)
    """
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))

        if request.method == 'GET':
            # Public can view pricing
            pricing_data = {
                "course_id": str(course.id),
                "course_title": course.title,
                "course_code": course.code,
                "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
                "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
                "pricing_plans": course.pricing_plans or [],
                "pricing_features": course.pricing_features or [],
                "pricing_testimonials": course.pricing_testimonials or [],
                "pricing_faqs": course.pricing_faqs or [],
                "pricing_comparison": course.pricing_comparison or [],
            }
            return Response(pricing_data)

        elif request.method == 'PUT':
            # Admin only for updates
            authenticate(lambda req: req)(request)
            restrict(['admin'])(lambda req: req)(request)
            
            data = request.data
            
            # Update hero section
            if 'hero_title' in data:
                course.hero_title = data['hero_title']
            if 'hero_subtitle' in data:
                course.hero_subtitle = data['hero_subtitle']
            
            # Update pricing fields
            if 'pricing_plans' in data:
                course.pricing_plans = data['pricing_plans']
            if 'pricing_features' in data:
                course.pricing_features = data['pricing_features']
            if 'pricing_testimonials' in data:
                course.pricing_testimonials = data['pricing_testimonials']
            if 'pricing_faqs' in data:
                course.pricing_faqs = data['pricing_faqs']
            if 'pricing_comparison' in data:
                course.pricing_comparison = data['pricing_comparison']
            
            course.updated_at = datetime.datetime.utcnow()
            course.save()
            course.reload()

            return Response({
                "success": True,
                "message": "Pricing data updated successfully",
                "data": {
                    "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
                    "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
                    "pricing_plans": course.pricing_plans,
                    "pricing_features": course.pricing_features,
                    "pricing_testimonials": course.pricing_testimonials,
                    "pricing_faqs": course.pricing_faqs,
                    "pricing_comparison": course.pricing_comparison,
                }
            })

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get Pricing by Course Slug (SEO-Friendly)
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_pricing_by_slug(request, provider, exam_code):
    """Get pricing data using provider and exam code (e.g., /api/pricing/azure/az-104/)"""
    try:
        from providers.models import Provider
        
        # Normalize inputs
        provider_normalized = provider.lower().replace('_', '-')
        exam_code_normalized = exam_code.lower().replace('_', '-')
        course_identifier = f"{provider_normalized}-{exam_code_normalized}"
        
        print(f"[DEBUG] Looking for course with identifier: {course_identifier}")
        
        course = None
        
        # 1️⃣ Try exact slug match first
        try:
            course = Course.objects.get(slug=course_identifier, is_active=True)
        except Course.DoesNotExist:
            # 2️⃣ Try case-insensitive slug match
            try:
                course = Course.objects.get(slug__iexact=course_identifier, is_active=True)
            except Course.DoesNotExist:
                # 3️⃣ Try provider-code format lookup (same logic as course_detail)
                all_parts = course_identifier.split('-')
                provider_obj = None
                provider_slug = None
                code_part = None
                
                # Strategy 1: Try two-word provider first (e.g., "sap-se")
                if len(all_parts) >= 3:
                    provider_slug_alt = f"{all_parts[0]}-{all_parts[1]}"
                    code_part_alt = '-'.join(all_parts[2:])
                    
                    provider_variants_alt = [
                        provider_slug_alt,
                        provider_slug_alt.upper(),
                        provider_slug_alt.capitalize(),
                        provider_slug_alt.replace('-', ' '),
                        provider_slug_alt.replace('-', ' ').title(),
                    ]
                    
                    for variant in provider_variants_alt:
                        try:
                            provider_obj = Provider.objects.get(slug=variant)
                            provider_slug = provider_slug_alt
                            code_part = code_part_alt
                            break
                        except Provider.DoesNotExist:
                            try:
                                provider_obj = Provider.objects.get(name__iexact=variant)
                                provider_slug = provider_slug_alt
                                code_part = code_part_alt
                                break
                            except Provider.DoesNotExist:
                                continue
                
                # Strategy 2: Try single-word provider (e.g., "sap")
                if not provider_obj and len(all_parts) >= 2:
                    provider_slug = all_parts[0]
                    code_part = '-'.join(all_parts[1:])
                    
                    provider_variants = [
                        provider_slug,
                        provider_slug.upper(),
                        provider_slug.capitalize(),
                        provider_slug.replace('-', ' '),
                        provider_slug.replace('-', ' ').title(),
                    ]
                    
                    for variant in provider_variants:
                        try:
                            provider_obj = Provider.objects.get(slug=variant)
                            break
                        except Provider.DoesNotExist:
                            try:
                                provider_obj = Provider.objects.get(name__iexact=variant)
                                break
                            except Provider.DoesNotExist:
                                continue
                    
                    # If still not found, try partial match
                    if not provider_obj:
                        try:
                            providers = Provider.objects.filter(slug__icontains=provider_slug)
                            if providers.count() == 1:
                                provider_obj = providers.first()
                        except Exception:
                            pass
                
                # Now try to find course with the found provider
                if provider_obj and code_part:
                    # Try multiple code format variations
                    code_variants = [
                        code_part.upper(),
                        code_part.upper().replace('-', '_'),
                        code_part.upper().replace('_', '-'),
                        code_part,
                        code_part.replace('-', '_').upper(),
                    ]
                    
                    # Try to find course by provider and code (try all variants)
                    for code_variant in code_variants:
                        try:
                            course = Course.objects.get(provider=provider_obj, code__iexact=code_variant, is_active=True)
                            break
                        except Course.DoesNotExist:
                            continue
                    
                    # If not found by code, try by slug variations
                    if not course:
                        slug_variants = [
                            f"{provider_slug}-{code_part.lower()}",
                            f"{provider_slug}-{code_part.lower().replace('_', '-')}",
                            course_identifier,
                        ]
                        
                        for slug_variant in slug_variants:
                            try:
                                course = Course.objects.get(provider=provider_obj, slug=slug_variant, is_active=True)
                                break
                            except Course.DoesNotExist:
                                try:
                                    course = Course.objects.get(provider=provider_obj, slug__iexact=slug_variant, is_active=True)
                                    break
                                except Course.DoesNotExist:
                                    continue
                    
                    # Last resort: try partial slug match
                    if not course:
                        try:
                            courses = Course.objects.filter(provider=provider_obj, slug__icontains=code_part.lower(), is_active=True)
                            if courses.count() == 1:
                                course = courses.first()
                        except Exception:
                            pass
                
                # Final fallback: Try to find by slug pattern
                if not course:
                    try:
                        courses = Course.objects.filter(slug__icontains=course_identifier.lower(), is_active=True)
                        if courses.count() == 1:
                            course = courses.first()
                    except Exception:
                        pass
        
        if not course:
            # Get available courses for better error message
            all_courses = Course.objects.filter(is_active=True).only('slug')[:10]
            available_slugs = [course.slug for course in all_courses if course.slug]
            
            print(f"[DEBUG] Course '{course_identifier}' not found. Available courses: {available_slugs}")
            
            return Response({
                "error": "Course not found",
                "message": f"No active course found with identifier '{course_identifier}'",
                "requested_provider": provider,
                "requested_exam_code": exam_code,
                "requested_slug": course_identifier,
                "available_courses": available_slugs,
                "suggestion": "Please create this course in the admin panel or check the provider and exam code format"
            }, status=404)
        
        pricing_data = {
            "course_id": str(course.id),
            "course_title": course.title,
            "course_code": course.code,
            "provider": course.provider.name if course.provider else "",
            "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
            "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
            "pricing_plans": course.pricing_plans or [],
            "pricing_features": course.pricing_features or [],
            "pricing_testimonials": course.pricing_testimonials or [],
            "pricing_faqs": course.pricing_faqs or [],
            "pricing_comparison": course.pricing_comparison or [],
        }
        print(f"[DEBUG] Found course: {course.title} with {len(pricing_data['pricing_plans'])} pricing plans")
        return Response(pricing_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
