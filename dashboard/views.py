from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from common.middleware import authenticate
from bson import ObjectId
import datetime


@api_view(['GET'])
@authenticate
@csrf_exempt
def get_dashboard_data(request):
    """Get student dashboard data with dynamic performance metrics"""
    try:
        # Get user info from request.user (set by authenticate decorator)
        user_data = request.user
        if not user_data:
            return Response({"error": "User authentication data not found"}, status=401)
        
        user_id = user_data.get('id')
        if not user_id or user_id == '':
            return Response({"error": "User ID not found in authentication data"}, status=401)
        
        # Fetch actual user from database
        from users.models import User
        from courses.models import Course
        from questions.models import Question
        from enrollments.models import Enrollment
        from exams.models import TestAttempt
        
        try:
            # Convert user_id to ObjectId safely
            user_object_id = ObjectId(user_id)
            user = User.objects.get(id=user_object_id)
        except (ValueError, TypeError) as e:
            return Response({"error": f"Invalid user ID format: {str(e)}"}, status=400)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            return Response({"error": f"Error fetching user: {str(e)}"}, status=500)
        
        # Validate user object has required attributes
        if not hasattr(user, 'email') or not user.email:
            return Response({"error": "User email not found"}, status=500)
        
        user_email = user.email
        user_name = getattr(user, 'fullname', None) or user_email.split('@')[0].capitalize()
        
        # Get enrolled courses from both Enrollment collection AND user.enrolled_courses
        # This ensures courses are shown for both regular and OAuth users
        user_id_str = str(user.id)
        enrollments = Enrollment.objects(user_name=user_id_str)
        purchased_exams_data = []
        
        # Track processed course IDs to avoid duplicates
        processed_course_ids = set()
        
        # First, process courses from Enrollment collection
        for enrollment in enrollments:
            try:
                course = enrollment.course
                if course:
                    course_id_str = str(course.id)
                    if course_id_str in processed_course_ids:
                        continue
                    processed_course_ids.add(course_id_str)
                    
                    # Calculate days left
                    expiry_date = enrollment.expiry_date
                    today = datetime.datetime.utcnow()
                    # Convert expiry_date to datetime if it's a date object
                    if expiry_date:
                        if isinstance(expiry_date, datetime.date) and not isinstance(expiry_date, datetime.datetime):
                            # Convert date to datetime at midnight UTC
                            expiry_date_dt = datetime.datetime.combine(expiry_date, datetime.datetime.min.time())
                            days_left = max(0, (expiry_date_dt - today).days)
                        else:
                            days_left = max(0, (expiry_date - today).days)
                    else:
                        days_left = 0
                    
                    # Get test attempts for this course
                    # Query ReferenceField with User object for proper MongoDB query
                    course_attempts = TestAttempt.objects(
                        user=user,
                        exam=course,
                        is_completed=True
                    )
                    attempts_count = course_attempts.count()
                    
                    # Calculate best score and progress
                    best_score = 0
                    if attempts_count > 0:
                        best_score = max([attempt.percentage for attempt in course_attempts] or [0])
                    
                    # Calculate progress (percentage of questions attempted)
                    total_questions = course.questions or 0
                    questions_attempted = 0
                    for attempt in course_attempts:
                        questions_attempted += len(attempt.questions) if attempt.questions else 0
                    progress = int((questions_attempted / total_questions * 100)) if total_questions > 0 else 0
                    
                    purchased_exams_data.append({
                        "id": str(enrollment.id),
                        "courseId": str(course.id),  # Add course ID for enrollment check
                        "provider": course.provider.name if course.provider else "",
                        "name": course.title,
                        "code": course.code,
                        "daysLeft": days_left,
                        "progress": min(progress, 100),
                        "attempts": attempts_count,
                        "bestScore": int(best_score),
                        "slug": course.slug
                    })
            except Exception as e:
                # Silently handle enrollment processing errors
                continue
        
        # Also check user.enrolled_courses (for OAuth users and direct course enrollments)
        if hasattr(user, 'enrolled_courses') and user.enrolled_courses:
            for enrolled_item in user.enrolled_courses:
                try:
                    # Handle both DBRef and direct Course objects
                    course = None
                    course_id_str = None
                    
                    # Check if it's a DBRef (from MongoDB)
                    if hasattr(enrolled_item, 'id'):
                        course_id_str = str(enrolled_item.id)
                        # Try to get the course
                        course = Course.objects(id=ObjectId(course_id_str)).first()
                    elif isinstance(enrolled_item, dict) and 'id' in enrolled_item:
                        # Handle dict-like DBRef
                        course_id_str = str(enrolled_item['id'])
                        course = Course.objects(id=ObjectId(course_id_str)).first()
                    else:
                        # Try to convert to ObjectId directly
                        try:
                            course_id_str = str(enrolled_item)
                            course = Course.objects(id=ObjectId(course_id_str)).first()
                        except:
                            pass
                    
                    if not course or not course_id_str:
                        continue
                    
                    # Skip if already processed
                    if course_id_str in processed_course_ids:
                        continue
                    processed_course_ids.add(course_id_str)
                    
                    # Try to find enrollment for expiry date, otherwise use default
                    enrollment = Enrollment.objects(user_name=user_id_str, course=course).first()
                    expiry_date = enrollment.expiry_date if enrollment else None
                    today = datetime.datetime.utcnow()
                    # Convert expiry_date to datetime if it's a date object
                    if expiry_date:
                        if isinstance(expiry_date, datetime.date) and not isinstance(expiry_date, datetime.datetime):
                            # Convert date to datetime at midnight UTC
                            expiry_date_dt = datetime.datetime.combine(expiry_date, datetime.datetime.min.time())
                            days_left = max(0, (expiry_date_dt - today).days)
                        else:
                            days_left = max(0, (expiry_date - today).days)
                    else:
                        days_left = 365  # Default 1 year if no enrollment record
                    
                    # Get test attempts for this course
                    # Query ReferenceField with User object for proper MongoDB query
                    course_attempts = TestAttempt.objects(
                        user=user,
                        exam=course,
                        is_completed=True
                    )
                    attempts_count = course_attempts.count()
                    
                    # Calculate best score and progress
                    best_score = 0
                    if attempts_count > 0:
                        best_score = max([attempt.percentage for attempt in course_attempts] or [0])
                    
                    # Calculate progress (percentage of questions attempted)
                    total_questions = course.questions or 0
                    questions_attempted = 0
                    for attempt in course_attempts:
                        questions_attempted += len(attempt.questions) if attempt.questions else 0
                    progress = int((questions_attempted / total_questions * 100)) if total_questions > 0 else 0
                    
                    purchased_exams_data.append({
                        "id": course_id_str,  # Use course ID if no enrollment ID
                        "courseId": course_id_str,  # Add course ID for enrollment check
                        "provider": course.provider.name if course.provider else "",
                        "name": course.title,
                        "code": course.code,
                        "daysLeft": days_left,
                        "progress": min(progress, 100),
                        "attempts": attempts_count,
                        "bestScore": int(best_score),
                        "slug": course.slug
                    })
                except Exception as e:
                    # Silently handle enrolled_courses processing errors
                    continue
        
        # Get all test attempts for performance calculation
        # Query ReferenceField - use User object for proper MongoDB query
        # (user object is already fetched above)
        all_attempts = TestAttempt.objects(
            user=user,
            is_completed=True
        )
        
        # Calculate overall performance metrics
        total_questions_answered = 0
        total_correct = 0
        total_time_practicing = 0  # in minutes
        tests_completed = all_attempts.count()
        
        # Topic performance map
        topic_performance_map = {}
        
        for attempt in all_attempts:
            # Count questions answered
            if attempt.questions:
                total_questions_answered += len(attempt.questions)
                
                # Count correct answers
                for q in attempt.questions:
                    if q.get('is_correct', False):
                        total_correct += 1
                    
                    # Get topic from question tags
                    tags = q.get('tags', [])
                    if tags:
                        topic = tags[0] if isinstance(tags, list) and len(tags) > 0 else "General"
                    else:
                        topic = "General"
                    
                    if topic not in topic_performance_map:
                        topic_performance_map[topic] = {"correct": 0, "total": 0}
                    
                    topic_performance_map[topic]["total"] += 1
                    if q.get('is_correct', False):
                        topic_performance_map[topic]["correct"] += 1
            
            # Calculate time practicing
            if attempt.duration_taken:
                total_time_practicing += attempt.duration_taken  # duration_taken is in minutes
            elif attempt.start_time and attempt.end_time:
                time_diff = attempt.end_time - attempt.start_time
                total_time_practicing += int(time_diff.total_seconds() / 60)
        
        # Calculate overall accuracy
        overall_accuracy = int((total_correct / total_questions_answered * 100)) if total_questions_answered > 0 else 0
        
        # Calculate average score from all completed attempts
        # Only count attempts that have a valid percentage value
        average_score = 0
        if tests_completed > 0:
            valid_percentages = [attempt.percentage for attempt in all_attempts if hasattr(attempt, 'percentage') and attempt.percentage is not None]
            if valid_percentages and len(valid_percentages) > 0:
                total_percentage = sum(valid_percentages)
                average_score = int(round(total_percentage / len(valid_percentages))) if len(valid_percentages) > 0 else 0
            else:
                average_score = 0
        
        # Format time practicing
        hours = total_time_practicing // 60
        minutes = total_time_practicing % 60
        time_practicing = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"
        
        # Convert topic performance to list
        topic_performance = []
        for topic, stats in topic_performance_map.items():
            percentage = int((stats["correct"] / stats["total"] * 100)) if stats["total"] > 0 else 0
            topic_performance.append({
                "topic": topic,
                "score": percentage,
                "correct": stats["correct"],
                "total": stats["total"]
            })
        
        # Sort by score descending
        topic_performance.sort(key=lambda x: x["score"], reverse=True)
        
        # Get coupons that are specifically assigned to this user or that the user has used
        # Only show coupons that belong to this user (not common coupons for all users)
        coupons = []
        try:
            from reviews.models import Coupon
            user_object_id = ObjectId(user_id)
            
            # Get all active coupons (we'll filter by used_by in Python for better compatibility)
            all_active_coupons = Coupon.objects(is_active=True)
            
            # Filter coupons where user is in used_by list OR assigned to user
            # Do NOT include common coupons - only user-specific coupons
            all_coupons = {}
            for coupon in all_active_coupons:
                # Check if user has used this coupon
                user_has_used = user_object_id in (coupon.used_by or [])
                
                # Check if coupon is assigned to this specific user
                coupon_assigned_to_user = coupon.user and str(coupon.user.id) == user_id
                
                # Include ONLY if: user has used it OR it's assigned to this specific user
                # Do NOT include common coupons (coupon.is_common)
                if user_has_used or coupon_assigned_to_user:
                    all_coupons[str(coupon.id)] = coupon
            
            # Convert to list format
            for coupon in all_coupons.values():
                # Check if user has used this coupon
                user_has_used = user_object_id in (coupon.used_by or [])
                
                # Get discount value (handle both discount_value and old field names)
                discount_value = getattr(coupon, 'discount_value', None)
                if discount_value is None:
                    discount_value = getattr(coupon, 'discount_percentage', None) or getattr(coupon, 'discount_amount', 0)
                
                discount_type = getattr(coupon, 'discount_type', 'percentage')
                discount_display = f"{discount_value}{'%' if discount_type == 'percentage' else '₹'}"
                
                coupons.append({
                    "id": str(coupon.id),
                    "code": coupon.code,
                    "discount": discount_display,
                    "discount_value": discount_value,
                    "discount_type": discount_type,
                    "expiry_date": coupon.valid_until.isoformat() if hasattr(coupon, 'valid_until') and coupon.valid_until else None,
                    "is_used": user_has_used,
                    "used_at": coupon.used_at.isoformat() if hasattr(coupon, 'used_at') and coupon.used_at and user_has_used else None
                })
            
            # Sort by used_at (most recently used first) or expiry_date
            coupons.sort(key=lambda x: (
                x.get('used_at') or '' if x.get('is_used') else '',
                x.get('expiry_date') or ''
            ), reverse=True)
        except Exception as e:
            # Silently handle coupon errors - don't break dashboard
            pass
        
        # Get test attempts history
        test_attempts = []
        # Sort attempts by end_time (most recent first), handling None values
        all_attempts_list = list(all_attempts)
        all_attempts_list.sort(
            key=lambda x: (
                x.end_time if x.end_time else datetime.datetime.min,
                x.created_at if x.created_at else datetime.datetime.min
            ),
            reverse=True
        )
        recent_attempts = all_attempts_list[:10]
        for attempt in recent_attempts:
            try:
                course_name = ""
                course_slug = ""
                provider = ""
                exam_code = ""
                
                if attempt.exam:
                    course_name = attempt.exam.title
                    course_slug = getattr(attempt.exam, 'slug', '')
                    if course_slug:
                        # Extract provider and examCode from slug (format: provider-examcode)
                        slug_parts = course_slug.split('-', 1)
                        if len(slug_parts) >= 2:
                            provider = slug_parts[0]
                            exam_code = slug_parts[1]
                elif attempt.category:
                    course_name = getattr(attempt.category, 'title', 'Practice Test')
                    # Try to get course from category
                    if hasattr(attempt.category, 'course') and attempt.category.course:
                        course_slug = getattr(attempt.category.course, 'slug', '')
                        if course_slug:
                            slug_parts = course_slug.split('-', 1)
                            if len(slug_parts) >= 2:
                                provider = slug_parts[0]
                                exam_code = slug_parts[1]
                
                test_attempts.append({
                    "id": str(attempt.id),
                    "course_name": course_name,
                    "course_slug": course_slug,
                    "provider": provider,
                    "exam_code": exam_code,
                    "score": int(attempt.percentage),
                    "date": attempt.end_time.isoformat() if attempt.end_time else attempt.created_at.isoformat(),
                    "passed": attempt.passed,
                    "is_trial": getattr(attempt, 'is_trial', False)
                })
            except Exception as e:
                # Silently handle attempt processing errors - don't break dashboard
                continue
        
        # Recommended exams
        recommended = Course.objects(is_active=True).order_by('-created_at')[:4]
        recommended_exams = []
        for course in recommended:
            recommended_exams.append({
                "id": str(course.id),
                "provider": course.provider.name if course.provider else "",
                "name": course.title,
                "code": course.code,
                "questions": course.questions or 0,
                "trending": True,
                "slug": course.slug
            })
        
        # Achievements (calculate based on actual data)
        achievements = []
        if tests_completed > 0:
            achievements.append({"id": 1, "title": "First Test Complete", "icon": "🎯", "earned": True})
        if total_questions_answered >= 100:
            achievements.append({"id": 2, "title": "100 Questions Practiced", "icon": "💯", "earned": True})
        if overall_accuracy >= 80:
            achievements.append({"id": 4, "title": "Score 80%+", "icon": "⭐", "earned": True})
        if tests_completed >= 10:
            achievements.append({"id": 5, "title": "Complete 10 Tests", "icon": "🏆", "earned": True})
        
        # Updates (recent course updates)
        updates = []
        recently_updated = Course.objects(is_active=True).order_by('-updated_at')[:3]
        for course in recently_updated:
            updates.append({
                "id": str(course.id),
                "text": f"{course.title} practice questions updated",
                "date": "Recently"
            })
        
        # Ongoing attempt (check for incomplete attempts)
        # Query ReferenceField with User object for proper MongoDB query
        ongoing_attempts = TestAttempt.objects(
            user=user,
            is_completed=False
        )
        # Sort by start_time (most recent first), handling None values
        ongoing_attempts_list = list(ongoing_attempts)
        ongoing_attempts_list.sort(
            key=lambda x: x.start_time if x.start_time else datetime.datetime.min,
            reverse=True
        )
        ongoing_attempt = None
        has_ongoing = False
        
        if len(ongoing_attempts_list) > 0:
            attempt = ongoing_attempts_list[0]
            try:
                course_name = ""
                if attempt.exam:
                    course_name = attempt.exam.title
                    slug = attempt.exam.slug
                elif attempt.category:
                    course_name = getattr(attempt.category, 'title', 'Practice Test')
                    slug = ""
                
                has_ongoing = True
                questions_answered = len([q for q in (attempt.questions or []) if q.get('user_selected_answers')])
                total_questions = len(attempt.questions) if attempt.questions else 0
                
                ongoing_attempt = {
                    "examName": course_name,
                    "testName": getattr(attempt.category, 'title', 'Practice Test') if attempt.category else "Test",
                    "progress": questions_answered,
                    "totalQuestions": total_questions,
                    "progressPercent": int((questions_answered / total_questions * 100)) if total_questions > 0 else 0,
                    "lastAttempt": attempt.start_time.strftime("%Y-%m-%d") if attempt.start_time else "",
                    "timeSpent": f"{int((datetime.datetime.utcnow() - attempt.start_time).total_seconds() / 60)}m" if attempt.start_time else "0m",
                    "slug": slug,
                    "testId": str(attempt.category.id) if attempt.category else "1"
                }
            except Exception as e:
                # Silently handle ongoing attempt processing errors
                pass
        
        dashboard_data = {
            "userName": user_name,
            "userEmail": user_email,
            "hasOngoingAttempt": has_ongoing,
            "ongoingAttempt": ongoing_attempt,
            "purchasedExams": purchased_exams_data,
            "freeAttempts": [],
            "recommendedExams": recommended_exams,
            "topicPerformance": topic_performance,
            "achievements": achievements,
            "updates": updates,
            # New performance metrics
            "overallAccuracy": overall_accuracy,
            "questionsAnswered": total_questions_answered,
            "timePracticing": time_practicing,
            "testsCompleted": tests_completed,
            "averageScore": average_score,
            "coupons": coupons,
            "testAttempts": test_attempts
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
