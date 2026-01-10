from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from common.middleware import authenticate, restrict
from courses.models import Course
from enrollments.models import Enrollment
from enrollments.payment_models import Payment
from users.models import User
from bson import ObjectId
from datetime import datetime

@csrf_exempt
@authenticate
@restrict(['admin'])
def get_analytics(request):
    """
    Admin API: Get analytics data including courses, enrollments, and revenue.
    """
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        # Get all active courses
        all_courses = Course.objects(is_active=True)
        total_courses = all_courses.count()
        
        # Get all enrollments
        all_enrollments = Enrollment.objects()
        total_enrolled_students = all_enrollments.count()
        
        # Get unique enrolled students - Enrollment uses user_name (StringField with user_id)
        unique_students = set()
        for enrollment in all_enrollments:
            try:
                if enrollment.user_name:
                    # user_name field stores user_id as string
                    unique_students.add(str(enrollment.user_name))
            except:
                pass
        total_unique_students = len(unique_students)
        
        # Calculate total revenue from payments - Payment status is 'completed', not 'success'
        # Count all completed payments for total revenue (even if enrollment_id is missing)
        all_payments = Payment.objects(status='completed')
        total_revenue = 0
        for payment in all_payments:
            try:
                # amount is a FloatField, convert to float safely
                if hasattr(payment, 'amount') and payment.amount is not None:
                    amount = float(payment.amount)
                    total_revenue += amount
            except (ValueError, TypeError) as e:
                print(f"Error converting payment amount to float: {e}, payment_id: {payment.id}")
                pass
        
        # Enrollment per course
        enrollment_per_course = []
        course_enrollment_map = {}
        for enrollment in all_enrollments:
            try:
                course_id = str(enrollment.course.id) if enrollment.course else None
                if course_id:
                    if course_id not in course_enrollment_map:
                        course_enrollment_map[course_id] = {
                            'course_id': course_id,
                            'course_name': enrollment.course.title if enrollment.course else 'Unknown',
                            'count': 0
                        }
                    course_enrollment_map[course_id]['count'] += 1
            except:
                pass
        
        enrollment_per_course = [
            {
                'course': item['course_name'],
                'students': item['count']
            }
            for item in course_enrollment_map.values()
        ]
        enrollment_per_course.sort(key=lambda x: x['students'], reverse=True)
        
        # Revenue per course - Payment has enrollment_id as ReferenceField
        revenue_per_course = []
        course_revenue_map = {}
        for payment in all_payments:
            try:
                # Payment has enrollment_id as ReferenceField to Enrollment
                if payment.enrollment_id:
                    enrollment = payment.enrollment_id
                    if enrollment and enrollment.course:
                        course_id = str(enrollment.course.id)
                        amount = float(payment.amount) if payment.amount else 0
                        if course_id not in course_revenue_map:
                            course_revenue_map[course_id] = {
                                'course_id': course_id,
                                'course_name': enrollment.course.title if enrollment.course else 'Unknown',
                                'revenue': 0
                            }
                        course_revenue_map[course_id]['revenue'] += amount
            except Exception as e:
                import traceback
                print(f"Error processing payment revenue: {e}")
                traceback.print_exc()
                pass
        
        revenue_per_course = [
            {
                'course': item['course_name'],
                'revenue': item['revenue']
            }
            for item in course_revenue_map.values()
        ]
        revenue_per_course.sort(key=lambda x: x['revenue'], reverse=True)
        
        # Top courses (by enrollment)
        top_courses = enrollment_per_course[:10]  # Top 10
        
        return JsonResponse({
            "success": True,
            "totalCourses": total_courses,
            "totalEnrolledStudents": total_unique_students,
            "totalRevenue": total_revenue,
            "enrollmentPerCourse": enrollment_per_course,
            "revenuePerCourse": revenue_per_course,
            "topCourses": top_courses
        }, status=200)
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            "success": False,
            "error": str(e),
            "message": "Failed to fetch analytics data"
        }, status=500)

