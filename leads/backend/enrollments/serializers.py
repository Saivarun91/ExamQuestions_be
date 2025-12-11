from rest_framework import serializers
from .models import Enrollment
from users.models import User
from categories.models import TestCategory
from bson import ObjectId

class EnrollmentSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    user_name = serializers.CharField()  # stores user_id as string
    category = serializers.CharField()   # store as string to avoid ObjectId issues
    duration_months = serializers.IntegerField()
    enrolled_date = serializers.DateField()
    expiry_date = serializers.DateField()

    def to_representation(self, obj):
        """Customize API output to include user full name and category name."""
        data = super().to_representation(obj)

        # ✅ Convert ObjectId to string for the enrollment id
        data["id"] = str(obj.id)

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
        try:
            if obj.course:
                from courses.models import Course
                course_obj = obj.course
                data["course_id"] = str(course_obj.id)
                data["course_name"] = course_obj.name
                data["course_description"] = getattr(course_obj, 'description', '')
                data["course_price"] = getattr(course_obj, 'price', None)
                data["course_offer_price"] = getattr(course_obj, 'offer_price', None)
                
                # Also include category info if available
                if course_obj.category:
                    data["category_id"] = str(course_obj.category.id)
                    data["category_name"] = course_obj.category.name
                    data["category"] = {
                        "id": str(course_obj.category.id),
                        "name": course_obj.category.name
                    }
                else:
                    data["category"] = None
            elif obj.category:
                # Category-level enrollment (backward compatibility)
                data["category_id"] = str(obj.category.id)
                category_name = obj.category.name
                data["category_name"] = category_name
                data["course_name"] = category_name  # Use course_name for frontend compatibility
                data["category"] = {
                    "id": str(obj.category.id),
                    "name": category_name
                }
                data["category_description"] = obj.category.description
                data["category_price"] = obj.category.price
            else:
                data["category_name"] = "Unknown"
                data["course_name"] = "Unknown"
                data["category"] = None
        except Exception as e:
            print(f"Error serializing course/category: {e}")
            data["category_name"] = "Invalid"
            data["course_name"] = "Invalid"
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
