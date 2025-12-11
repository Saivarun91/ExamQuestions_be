from rest_framework import serializers
from .models import Enrollment
from users.models import User
from categories.models import Category
from bson import ObjectId

class EnrollmentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_name = serializers.CharField()  # stores user_id as string
    # Remove category from base fields to avoid lazy loading errors
    # It will be handled in to_representation method
    duration_months = serializers.IntegerField()
    enrolled_date = serializers.DateField()
    expiry_date = serializers.DateField()

    def to_representation(self, obj):
        """Customize API output to include user full name and category name."""
        # Build data dictionary manually to avoid lazy loading issues
        data = {
            "id": str(obj.id),
            "user_name": obj.user_name,
            "duration_months": obj.duration_months,
            "enrolled_date": str(obj.enrolled_date),
            "expiry_date": str(obj.expiry_date)
        }

        # ✅ Convert user_name (user_id string) → full name and email
        try:
            user_obj = User.objects(id=ObjectId(obj.user_name)).first()
            if user_obj:
                user_fullname = user_obj.fullname if user_obj else "Unknown User"
                user_email = user_obj.email if user_obj else "N/A"
            else:
                user_fullname = "Unknown User"
                user_email = "N/A"
            data["user_name"] = user_fullname  # Use user_name for frontend compatibility
            data["user_fullname"] = user_fullname  # Also keep user_fullname
            data["user_email"] = user_email  # Add email for admin display
        except Exception as e:
            print(f"Error getting user info: {e}")
            data["user_name"] = "Invalid User ID"
            data["user_fullname"] = "Invalid User ID"
            data["user_email"] = "N/A"

        # ✅ Convert course reference → course info (prefer course over category)
        # Handle deleted/missing references gracefully
        try:
            # Try to access course first
            course_obj = None
            try:
                if hasattr(obj, 'course') and obj.course:
                    from courses.models import Course
                    # Try to access the course - will raise DoesNotExist if deleted
                    course_obj = obj.course
                    # Force load to check if it exists
                    _ = course_obj.id
            except Exception as course_err:
                # Course was deleted or reference is broken
                course_obj = None
            
            if course_obj:
                data["course_id"] = str(course_obj.id)
                data["course_name"] = course_obj.title
                data["course_code"] = getattr(course_obj, 'code', '')
                data["course_description"] = getattr(course_obj, 'about', '')
                data["course_actual_price"] = getattr(course_obj, 'actual_price', None)
                data["course_offer_price"] = getattr(course_obj, 'offer_price', None)
                
                # Also include category info if available
                try:
                    if hasattr(course_obj, 'category') and course_obj.category:
                        # Force load category to check if it exists
                        _ = course_obj.category.id
                        data["category_id"] = str(course_obj.category.id)
                        data["category_name"] = course_obj.category.title
                        data["category"] = {
                            "id": str(course_obj.category.id),
                            "name": course_obj.category.title
                        }
                    else:
                        data["category"] = None
                except Exception:
                    # Category was deleted
                    data["category"] = None
            else:
                # Try category-level enrollment (backward compatibility)
                category_obj = None
                try:
                    if hasattr(obj, 'category') and obj.category:
                        category_obj = obj.category
                        # Force load to check if it exists
                        _ = category_obj.id
                except Exception:
                    # Category was deleted or reference is broken
                    category_obj = None
                
                if category_obj:
                    data["category_id"] = str(category_obj.id)
                    category_name = category_obj.title
                    data["category_name"] = category_name
                    data["course_name"] = category_name
                    data["category"] = {
                        "id": str(category_obj.id),
                        "name": category_name
                    }
                    data["category_description"] = getattr(category_obj, 'description', '')
                    data["category_price"] = getattr(category_obj, 'price', None)
                else:
                    # Both course and category references are invalid or deleted
                    data["category_name"] = "Deleted/Unknown"
                    data["course_name"] = "Deleted/Unknown"
                    data["category"] = None
        except Exception as e:
            print(f"Error serializing course/category: {e}")
            import traceback
            traceback.print_exc()
            data["category_name"] = "Error Loading"
            data["course_name"] = "Error Loading"
            data["category"] = None

        # ✅ Add payment information if exists
        try:
            if obj.payment:
                payment = obj.payment
                data["payment"] = {
                    "id": str(payment.id),
                    "razorpay_order_id": payment.razorpay_order_id,
                    "razorpay_payment_id": getattr(payment, "razorpay_payment_id", None) or "",
                    "amount": payment.amount,
                    "currency": payment.currency or "INR",
                    "status": payment.status or "pending",
                    "paid_at": str(payment.paid_at) if hasattr(payment, "paid_at") and payment.paid_at else None
                }
            else:
                data["payment"] = None
        except Exception as e:
            data["payment"] = None

        return data



    def create(self, validated_data):
        enrollment = Enrollment(**validated_data)
        enrollment.save()
        return enrollment
