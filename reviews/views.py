import json
import random
import string
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from .models import Review, Coupon
from users.models import User
from categories.models import Category
from courses.models import Course
from common.middleware import authenticate, restrict


@csrf_exempt
@authenticate
def submit_review(request):
    """
    Submit a review and automatically generate a coupon code.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Parse JSON with better error handling
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError as e:
            return JsonResponse({"success": False, "message": f"Invalid JSON: {str(e)}"}, status=400)
        
        user_id = request.user.get("id")
        
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        rating = data.get("rating")
        comment = data.get("comment")
        category_id = data.get("category_id")  # Optional

        if not rating or not comment:
            return JsonResponse({"success": False, "message": "Rating and comment are required"}, status=400)

        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return JsonResponse({"success": False, "message": "Rating must be between 1 and 5"}, status=400)

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        # Get category if provided (optional - review can be submitted without category)
        category = None
        if category_id:
            # Handle empty string or None
            if not category_id or category_id == "null" or category_id == "undefined":
                category_id = None
            elif ObjectId.is_valid(category_id):
                try:
                    category = Category.objects.get(id=ObjectId(category_id))
                except Category.DoesNotExist:
                    # Category not found, but allow review submission without category
                    category = None
            # If category_id is not a valid ObjectId, just proceed without category

        # Create review
        review = Review(
            user=user,
            category=category,
            rating=rating,
            comment=comment,
            is_approved=False,  # Admin approval required
            is_active=True,
            coupon_generated=False
        )
        review.save()

        # Find an active common coupon that the user hasn't used yet
        now = datetime.utcnow()
        user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        
        common_coupon = Coupon.objects(
            is_common=True,
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        ).first()
        
        # Check if user has already used this common coupon
        if common_coupon and user_object_id in common_coupon.used_by:
            common_coupon = None
        
        if common_coupon:
            # Return the common coupon code (all students get the same code)
            coupon = common_coupon
        else:
            # No common coupon available, generate a unique one (fallback)
            coupon_code = generate_coupon_code()
        valid_until = datetime.utcnow() + timedelta(days=10)
        coupon = Coupon(
            code=coupon_code,
            user=user,
            review=review,
            discount_type='percentage',
            discount_value=10.0,  # 10% discount
            min_purchase=0,
            max_discount=None,
            valid_from=datetime.utcnow(),
            valid_until=valid_until,
            is_active=True,
                is_common=False,
                created_by_admin=False
        )
        coupon.save()

        # Update review to mark coupon as generated
        review.coupon_generated = True
        review.save()

        # Create notification for coupon received
        try:
            from notifications.views import create_notification
            create_notification(
                user=user,
                notification_type='coupon',
                title='Coupon Received for Review! 🎁',
                message=f'Thank you for your review! You received coupon code: {coupon.code}. Get {coupon.discount_value}{"%" if coupon.discount_type == "percentage" else "₹"} off!',
                link='/dashboard',
                metadata={'coupon_id': str(coupon.id), 'coupon_code': coupon.code}
            )
        except Exception as e:
            print(f"Error creating notification: {e}")

        return JsonResponse({
            "success": True,
            "message": "Review submitted successfully! Your coupon code has been generated.",
            "review": {
                "id": str(review.id),
                "rating": review.rating,
                "comment": review.comment,
                "created_at": str(review.created_at)
            },
            "coupon": {
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "valid_until": str(coupon.valid_until),
                "min_purchase": coupon.min_purchase
            }
        }, status=201)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# =================== TEST REVIEW SUBMISSION ===================
@csrf_exempt
@authenticate
def create_review(request):
    """Create a review for a test/course after completion and generate coupon"""
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = request.user.get('id')
        
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)
        
        # Get user
        user = User.objects(id=ObjectId(user_id)).first()
        if not user:
            return JsonResponse({"success": False, "message": "User not found"}, status=404)
        
        # Get review data
        rating = data.get('rating')
        review_text = data.get('review_text', '')
        exam_code = data.get('exam_code')
        provider = data.get('provider')
        score = data.get('score', 0)
        
        if not rating:
            return JsonResponse({"success": False, "message": "Rating is required"}, status=400)
        
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return JsonResponse({"success": False, "message": "Rating must be between 1 and 5"}, status=400)
        
        # Find course by provider and exam_code
        course = None
        if provider and exam_code:
            slug = f"{provider.lower()}-{exam_code.lower()}"
            course = Course.objects(slug=slug).first()
        
        # Create review
        review = Review(
            user=user,
            rating=rating,
            text=review_text,
            comment=review_text,  # Also set comment for compatibility
            created_at=datetime.utcnow()
        )
        
        # Link to course if found
        if course:
            review.course = course
        
        review.save()
        
        # Generate coupon code for the review
        now = datetime.utcnow()
        user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        
        # First, check if there's an active common coupon the user hasn't used
        common_coupon = Coupon.objects(
            is_common=True,
            is_active=True,
            valid_from__lte=now,
            valid_until__gte=now
        ).first()
        
        # Check if user has already used this common coupon
        if common_coupon and user_object_id in common_coupon.used_by:
            common_coupon = None
        
        coupon = None
        if common_coupon:
            # Use the common coupon
            coupon = common_coupon
        else:
            # Generate a unique coupon for this review
            coupon_code = generate_coupon_code()
            valid_until = datetime.utcnow() + timedelta(days=10)
            
            coupon = Coupon(
                code=coupon_code,
                user=user,
                review=review,
                discount_type='percentage',
                discount_value=10.0,  # 10% discount
                min_purchase=0,
                max_discount=None,
                valid_from=datetime.utcnow(),
                valid_until=valid_until,
                is_active=True,
                is_common=False,
                created_by_admin=False
            )
            coupon.save()
        
        # Update review to mark coupon as generated
        review.coupon_generated = True
        review.save()
        
        # Create notification for coupon received
        try:
            from notifications.views import create_notification
            create_notification(
                user=user,
                notification_type='coupon',
                title='Coupon Received for Review! 🎁',
                message=f'Thank you for your review! You received coupon code: {coupon.code}. Get {coupon.discount_value}{"%" if coupon.discount_type == "percentage" else "₹"} off!',
                link='/dashboard',
                metadata={'coupon_id': str(coupon.id), 'coupon_code': coupon.code}
            )
        except Exception as e:
            print(f"Error creating notification: {e}")
        
        return JsonResponse({
            "success": True,
            "message": "Review submitted successfully",
            "review_id": str(review.id),
            "coupon": {
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "valid_until": str(coupon.valid_until)
            }
        }, status=200)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_all_reviews(request):
    """Get all reviews for admin panel"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    try:
        reviews = Review.objects.all().order_by('-created_at')
        
        data = []
        for review in reviews:
            # Get user info
            user_name = "Unknown"
            user_email = "N/A"
            try:
                if review.user:
                    user_name = review.user.fullname
                    user_email = review.user.email
            except:
                pass
            
            # Get course info
            course_name = "General Review"
            try:
                if hasattr(review, 'course') and review.course:
                    course_name = review.course.title
            except:
                pass
            
            data.append({
                "id": str(review.id),
                "user_name": user_name,
                "user_email": user_email,
                "course_name": course_name,
                "rating": review.rating,
                "text": review.text or review.comment or "",
                "comment": review.comment or review.text or "",
                "is_approved": getattr(review, 'is_approved', False),
                "is_active": getattr(review, 'is_active', True),
                "is_testimonial": getattr(review, 'is_testimonial', False),
                "created_at": str(review.created_at) if review.created_at else ""
            })
        
        return JsonResponse({"success": True, "data": data}, status=200)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


def generate_coupon_code(length=8):
    """Generate a unique coupon code (for review-generated coupons)"""
    while True:
        # Generate code: 4 letters + 4 numbers
        letters = ''.join(random.choices(string.ascii_uppercase, k=4))
        numbers = ''.join(random.choices(string.digits, k=4))
        code = f"{letters}{numbers}"
        
        # Check if code already exists (for review coupons, we want unique codes)
        # Note: Admin-created common coupons can have same code for multiple users
        existing = Coupon.objects(code=code, is_common=False, created_by_admin=False).first()
        if not existing:
            return code


@csrf_exempt
def get_reviews(request, category_id=None):
    """
    Get all approved and active reviews.
    Optionally filter by category.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Get approved and active reviews
        reviews_query = Review.objects(is_approved=True, is_active=True)
        
        # Filter by category if provided
        if category_id:
            # Handle empty string or None
            if not category_id or category_id == "null" or category_id == "undefined":
                category_id = None
            elif ObjectId.is_valid(category_id):
                try:
                    category = Category.objects.get(id=ObjectId(category_id))
                    reviews_query = reviews_query.filter(category=category)
                except Category.DoesNotExist:
                    # Category not found - return empty reviews list instead of error
                    return JsonResponse({
                        "success": True,
                        "reviews": [],
                        "total": 0,
                        "message": "Category not found"
                    }, status=200)
            # If category_id is not a valid ObjectId, just return all reviews

        reviews = reviews_query.order_by('-created_at').limit(50)

        reviews_data = []
        for review in reviews:
            try:
                user_name = review.user.fullname if hasattr(review.user, 'fullname') else (
                    review.user.email if hasattr(review.user, 'email') else "Anonymous"
                )
            except:
                user_name = "Anonymous"

            review_data = {
                "id": str(review.id),
                "user_name": user_name,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": str(review.created_at),
                "category": None,
                "courses": []
            }

            # Add category info if exists
            if review.category:
                try:
                    review_data["category"] = {
                        "id": str(review.category.id),
                        "name": review.category.name
                    }
                    
                    # Find courses that belong to this category
                    try:
                        from courses.models import Course
                        courses = Course.objects(category=review.category, is_active=True)
                        review_data["courses"] = [
                            {
                                "id": str(course.id),
                                "name": course.name
                            }
                            for course in courses
                        ]
                    except Exception as e:
                        print(f"Error fetching courses for category {review.category.id}: {e}")
                        pass
                except:
                    pass

            reviews_data.append(review_data)

        return JsonResponse({
            "success": True,
            "reviews": reviews_data,
            "total": len(reviews_data)
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def get_user_coupons(request):
    """
    Get all active coupons for the logged-in user.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        # Get all coupons for the user (including used and expired ones for history)
        now = datetime.utcnow()
        coupons = Coupon.objects(
            user=user,
            is_active=True
        ).order_by('-created_at')

        coupons_data = []
        for coupon in coupons:
            coupons_data.append({
                "id": str(coupon.id),
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "min_purchase": coupon.min_purchase,
                "max_discount": coupon.max_discount,
                "valid_until": str(coupon.valid_until),
                "created_at": str(coupon.created_at),
                "is_used": coupon.is_used
            })

        return JsonResponse({
            "success": True,
            "coupons": coupons_data,
            "total": len(coupons_data)
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def verify_coupon(request):
    """
    Verify if a coupon code is valid and return discount details.
    Now supports per-user usage tracking (one coupon per user).
    Supports both authenticated and non-authenticated requests.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        coupon_code = data.get("code")
        amount = data.get("amount", 0)  # Purchase amount
        
        # Try to get user_id from authenticated request, fallback to data
        user_id = None
        # Check if request has user attribute (from authenticate middleware)
        try:
            if hasattr(request, 'user') and request.user and isinstance(request.user, dict):
                user_id = request.user.get("id")
        except:
            pass
        if not user_id:
            user_id = data.get("user_id")  # Optional: for non-authenticated requests

        if not coupon_code:
            return JsonResponse({"success": False, "message": "Coupon code is required"}, status=400)

        # If user_id is provided, find coupon for that specific user first
        # Otherwise, find any active coupon with this code
        coupon = None
        if user_id:
            user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            # Try to find user-specific coupon first
            coupon = Coupon.objects(code=coupon_code.upper(), user=user_object_id, is_active=True).first()
            # If not found, try to find common coupon
            if not coupon:
                coupon = Coupon.objects(code=coupon_code.upper(), is_common=True, is_active=True).first()
        else:
            # For non-authenticated users, find any active coupon with this code
            coupon = Coupon.objects(code=coupon_code.upper(), is_active=True).first()

        if not coupon:
            return JsonResponse({"success": False, "message": "Invalid coupon code"}, status=404)

        # Check if coupon is active
        if not coupon.is_active:
            return JsonResponse({"success": False, "message": "Coupon is not active"}, status=400)

        # Check if coupon is expired
        now = datetime.utcnow()
        if coupon.valid_until < now:
            return JsonResponse({"success": False, "message": "Coupon has expired"}, status=400)
        
        if coupon.valid_from > now:
            return JsonResponse({"success": False, "message": "Coupon is not yet valid"}, status=400)

        # Check per-user usage (one coupon per user)
        if user_id:
            user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            if user_object_id in coupon.used_by:
                return JsonResponse({"success": False, "message": "You have already used this coupon code"}, status=400)
        else:
            # For non-authenticated users, check old is_used flag (backward compatibility)
            if coupon.is_used and not coupon.is_common:
                return JsonResponse({"success": False, "message": "This coupon has already been used"}, status=400)

        # Check minimum purchase
        if amount < coupon.min_purchase:
            return JsonResponse({
                "success": False,
                "message": f"Minimum purchase of ₹{coupon.min_purchase} required"
            }, status=400)

        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount_amount = (amount * coupon.discount_value) / 100
            if coupon.max_discount:
                discount_amount = min(discount_amount, coupon.max_discount)
        else:
            discount_amount = coupon.discount_value

        final_amount = max(0, amount - discount_amount)

        return JsonResponse({
            "success": True,
            "discount_amount": round(discount_amount, 2),
            "final_amount": round(final_amount, 2),
            "coupon": {
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "discount_amount": round(discount_amount, 2),
                "original_amount": amount,
                "final_amount": round(final_amount, 2),
                "coupon_id": str(coupon.id),
                "is_common": coupon.is_common
            }
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def get_all_reviews_admin(request):
    """
    Admin API: Get all reviews (including pending ones) for admin review.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Get all reviews (including pending)
        reviews = Review.objects().order_by('-created_at')

        reviews_data = []
        for review in reviews:
            try:
                user_name = review.user.fullname if hasattr(review.user, 'fullname') else (
                    review.user.email if hasattr(review.user, 'email') else "Anonymous"
                )
            except:
                user_name = "Anonymous"

            review_data = {
                "id": str(review.id),
                "user_name": user_name,
                "rating": review.rating,
                "comment": review.comment,
                "created_at": str(review.created_at),
                "is_approved": review.is_approved,
                "is_active": review.is_active,
                "is_testimonial": getattr(review, 'is_testimonial', False),
                "category": None,
                "courses": []
            }

            # Add category info if exists
            if review.category:
                try:
                    review_data["category"] = {
                        "id": str(review.category.id),
                        "name": review.category.name
                    }
                    
                    # Find courses that belong to this category
                    try:
                        from courses.models import Course
                        courses = Course.objects(category=review.category, is_active=True)
                        review_data["courses"] = [
                            {
                                "id": str(course.id),
                                "name": course.name
                            }
                            for course in courses
                        ]
                    except Exception as e:
                        print(f"Error fetching courses for category {review.category.id}: {e}")
                        pass
                except:
                    pass

            reviews_data.append(review_data)

        return JsonResponse({
            "success": True,
            "reviews": reviews_data,
            "total": len(reviews_data)
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def approve_review(request, review_id):
    """
    Admin API: Approve a review.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(review_id):
            return JsonResponse({"success": False, "message": "Invalid review ID"}, status=400)

        # Use pk or _id to query by primary key
        review = Review.objects.get(pk=ObjectId(review_id))
        review.is_approved = True
        review.is_active = True
        review.updated_at = datetime.utcnow()
        review.save()

        # Create notification for review approval
        try:
            from notifications.views import create_notification
            create_notification(
                user=review.user,
                notification_type='review_approved',
                title='Your Review Was Approved! ✅',
                message='Thank you! Your review has been approved and is now visible to others.',
                link='/dashboard',
                metadata={'review_id': str(review.id)}
            )
        except Exception as e:
            print(f"Error creating notification: {e}")

        return JsonResponse({
            "success": True,
            "message": "Review approved successfully"
        }, status=200)

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return JsonResponse({"success": False, "message": "Review not found"}, status=404)
        import traceback
        print(f"Error in approve_review: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": f"Error: {error_msg}"}, status=500)


@csrf_exempt
@authenticate
def reject_review(request, review_id):
    """
    Admin API: Reject/deactivate a review.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(review_id):
            return JsonResponse({"success": False, "message": "Invalid review ID"}, status=400)

        # Use pk or _id to query by primary key
        review = Review.objects.get(pk=ObjectId(review_id))
        review.is_active = False
        review.updated_at = datetime.utcnow()
        review.save()

        return JsonResponse({
            "success": True,
            "message": "Review rejected successfully"
        }, status=200)

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return JsonResponse({"success": False, "message": "Review not found"}, status=404)
        import traceback
        print(f"Error in reject_review: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": f"Error: {error_msg}"}, status=500)


@csrf_exempt
@authenticate
def toggle_testimonial(request, review_id):
    """
    Admin API: Toggle testimonial status of a review.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(review_id):
            return JsonResponse({"success": False, "message": "Invalid review ID"}, status=400)

        # Use pk or _id to query by primary key
        review = Review.objects.get(pk=ObjectId(review_id))
        # Only allow testimonial if review is approved
        if not review.is_approved:
            return JsonResponse({
                "success": False,
                "message": "Review must be approved before marking as testimonial"
            }, status=400)
        
        # Toggle testimonial status
        review.is_testimonial = not getattr(review, 'is_testimonial', False)
        review.updated_at = datetime.utcnow()
        review.save()

        return JsonResponse({
            "success": True,
            "message": f"Review {'marked as' if review.is_testimonial else 'removed from'} testimonial successfully",
            "is_testimonial": review.is_testimonial
        }, status=200)

    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            return JsonResponse({"success": False, "message": "Review not found"}, status=404)
        import traceback
        print(f"Error in toggle_testimonial: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": f"Error: {error_msg}"}, status=500)


# ==================== ADMIN COUPON MANAGEMENT ====================

@csrf_exempt
@authenticate
@restrict(['admin'])
def create_coupon(request):
    """
    Admin API: Create a common coupon code.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        
        code = data.get("code", "").strip().upper()
        discount_value = data.get("discount_value")
        discount_type = data.get("discount_type", "percentage")
        valid_days = data.get("valid_days", 30)
        min_purchase = data.get("min_purchase", 0)
        max_discount = data.get("max_discount")
        is_active = data.get("is_active", True)

        # Validate required fields
        if not code:
            return JsonResponse({"success": False, "message": "Coupon code is required"}, status=400)
        
        if discount_value is None:
            return JsonResponse({"success": False, "message": "Discount value is required"}, status=400)

        # Check if code already exists
        if Coupon.objects(code=code).first():
            return JsonResponse({"success": False, "message": "Coupon code already exists"}, status=400)

        # Validate discount value
        if discount_type == "percentage" and (discount_value < 0 or discount_value > 100):
            return JsonResponse({"success": False, "message": "Percentage discount must be between 0 and 100"}, status=400)
        elif discount_type == "fixed" and discount_value < 0:
            return JsonResponse({"success": False, "message": "Fixed discount must be positive"}, status=400)

        # Create coupon
        valid_until = datetime.utcnow() + timedelta(days=valid_days)
        coupon = Coupon(
            code=code,
            discount_type=discount_type,
            discount_value=float(discount_value),
            min_purchase=float(min_purchase) if min_purchase else 0,
            max_discount=float(max_discount) if max_discount else None,
            valid_from=datetime.utcnow(),
            valid_until=valid_until,
            is_active=is_active,
            is_common=True,
            created_by_admin=True
        )
        coupon.save()

        return JsonResponse({
            "success": True,
            "message": "Coupon created successfully",
            "coupon": {
                "id": str(coupon.id),
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "valid_until": str(coupon.valid_until),
                "is_active": coupon.is_active
            }
        }, status=201)

    except Exception as e:
        import traceback
        print(f"Error in create_coupon: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_all_coupons(request):
    """
    Admin API: Get all coupons with usage statistics.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        coupons = Coupon.objects().order_by('-created_at')
        
        coupons_data = []
        for coupon in coupons:
            coupons_data.append({
                "id": str(coupon.id),
                "code": coupon.code,
                "discount_type": coupon.discount_type,
                "discount_value": coupon.discount_value,
                "min_purchase": coupon.min_purchase,
                "max_discount": coupon.max_discount,
                "valid_from": str(coupon.valid_from),
                "valid_until": str(coupon.valid_until),
                "is_active": coupon.is_active,
                "is_common": coupon.is_common,
                "created_by_admin": coupon.created_by_admin,
                "used_count": len(coupon.used_by),
                "created_at": str(coupon.created_at),
                "user": str(coupon.user.id) if coupon.user else None,
                "review": str(coupon.review.id) if coupon.review else None,
                "lead": str(coupon.lead.id) if coupon.lead else None
            })

        return JsonResponse({
            "success": True,
            "coupons": coupons_data,
            "total": len(coupons_data)
        }, status=200)

    except Exception as e:
        import traceback
        print(f"Error in get_all_coupons: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_coupon(request, coupon_id):
    """
    Admin API: Update coupon details.
    """
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(coupon_id):
            return JsonResponse({"success": False, "message": "Invalid coupon ID"}, status=400)

        data = json.loads(request.body)
        coupon = Coupon.objects.get(pk=ObjectId(coupon_id))

        # Update fields if provided
        if "discount_value" in data:
            coupon.discount_value = float(data["discount_value"])
        if "discount_type" in data:
            coupon.discount_type = data["discount_type"]
        if "min_purchase" in data:
            coupon.min_purchase = float(data["min_purchase"])
        if "max_discount" in data:
            coupon.max_discount = float(data["max_discount"]) if data["max_discount"] else None
        if "is_active" in data:
            coupon.is_active = data["is_active"]
        if "valid_days" in data:
            coupon.valid_until = datetime.utcnow() + timedelta(days=int(data["valid_days"]))

        coupon.save()

        return JsonResponse({
            "success": True,
            "message": "Coupon updated successfully"
        }, status=200)

    except Coupon.DoesNotExist:
        return JsonResponse({"success": False, "message": "Coupon not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in update_coupon: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def delete_coupon(request, coupon_id):
    """
    Admin API: Delete a coupon.
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(coupon_id):
            return JsonResponse({"success": False, "message": "Invalid coupon ID"}, status=400)

        coupon = Coupon.objects.get(pk=ObjectId(coupon_id))
        coupon.delete()

        return JsonResponse({
            "success": True,
            "message": "Coupon deleted successfully"
        }, status=200)

    except Coupon.DoesNotExist:
        return JsonResponse({"success": False, "message": "Coupon not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in delete_coupon: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def assign_coupon_to_lead(request, lead_id):
    """
    Admin API: Assign a coupon to a lead (for non-enrolled users).
    The coupon will be given to the user when they enroll.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(lead_id):
            return JsonResponse({"success": False, "message": "Invalid lead ID"}, status=400)

        from leads.models import Lead
        
        data = json.loads(request.body)
        coupon_code = data.get("coupon_code", "").strip().upper()
        
        if not coupon_code:
            return JsonResponse({"success": False, "message": "Coupon code is required"}, status=400)

        lead = Lead.objects.get(pk=ObjectId(lead_id))
        source_coupon = Coupon.objects(code=coupon_code).first()

        if not source_coupon:
            return JsonResponse({"success": False, "message": "Coupon not found"}, status=404)

        # Create a coupon instance linked to the lead (will be assigned when they enroll)
        try:
            lead_coupon = Coupon(
                code=source_coupon.code,
                lead=lead,
                discount_type=source_coupon.discount_type,
                discount_value=source_coupon.discount_value,
                min_purchase=source_coupon.min_purchase,
                max_discount=source_coupon.max_discount,
                valid_from=source_coupon.valid_from,
                valid_until=source_coupon.valid_until,
                is_active=source_coupon.is_active,
                is_common=False,
                created_by_admin=True
            )
            lead_coupon.save()
        except Exception as save_error:
            # Handle duplicate key error (MongoDB index still exists)
            error_str = str(save_error)
            if "duplicate key" in error_str.lower() or "E11000" in error_str:
                # Check if coupon already exists for this lead
                existing = Coupon.objects(code=source_coupon.code, lead=lead).first()
                if existing:
                    return JsonResponse({
                        "success": True,
                        "message": "Lead already has this coupon",
                        "coupon": {
                            "code": existing.code,
                            "discount_value": existing.discount_value,
                            "discount_type": existing.discount_type,
                            "valid_until": str(existing.valid_until)
                        }
                    }, status=200)
                else:
                    # Try to generate a unique code by appending random suffix
                    unique_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    lead_coupon = Coupon(
                        code=f"{source_coupon.code}-{unique_suffix}",
                        lead=lead,
                        discount_type=source_coupon.discount_type,
                        discount_value=source_coupon.discount_value,
                        min_purchase=source_coupon.min_purchase,
                        max_discount=source_coupon.max_discount,
                        valid_from=source_coupon.valid_from,
                        valid_until=source_coupon.valid_until,
                        is_active=source_coupon.is_active,
                        is_common=False,
                        created_by_admin=True
                    )
                    lead_coupon.save()
            else:
                # Re-raise if it's a different error
                raise

        return JsonResponse({
            "success": True,
            "message": "Coupon assigned to lead successfully. They will receive it when they enroll.",
            "coupon": {
                "code": lead_coupon.code,
                "discount_value": lead_coupon.discount_value,
                "discount_type": lead_coupon.discount_type,
                "valid_until": str(lead_coupon.valid_until)
            }
        }, status=200)

    except Lead.DoesNotExist:
        return JsonResponse({"success": False, "message": "Lead not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in assign_coupon_to_lead: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def assign_coupon_to_user(request, user_id):
    """
    Admin API: Assign/send a coupon to a specific logged-in user.
    Creates a user-specific coupon instance.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(user_id):
            return JsonResponse({"success": False, "message": "Invalid user ID"}, status=400)

        data = json.loads(request.body)
        coupon_code = data.get("coupon_code", "").strip().upper()
        
        if not coupon_code:
            return JsonResponse({"success": False, "message": "Coupon code is required"}, status=400)

        user = User.objects.get(pk=ObjectId(user_id))
        source_coupon = Coupon.objects(code=coupon_code).first()

        if not source_coupon:
            return JsonResponse({"success": False, "message": "Coupon not found"}, status=404)

        # Check if user already has this coupon
        user_object_id = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
        
        # Check if user already has a coupon with this code
        existing_user_coupon = Coupon.objects(code=source_coupon.code, user=user).first()
        if existing_user_coupon:
            return JsonResponse({
                "success": True,
                "message": "User already has this coupon",
                "coupon": {
                    "code": existing_user_coupon.code,
                    "discount_value": existing_user_coupon.discount_value,
                    "discount_type": existing_user_coupon.discount_type,
                    "valid_until": str(existing_user_coupon.valid_until)
                }
            }, status=200)

        # Check if user has already used this coupon (for common coupons)
        if source_coupon.is_common and user_object_id in source_coupon.used_by:
            return JsonResponse({"success": False, "message": "User has already used this coupon"}, status=400)

        # Create a user-specific coupon instance (don't modify the source coupon)
        # Multiple users can have the same coupon code (unique constraint removed)
        try:
            user_coupon = Coupon(
                code=source_coupon.code,  # Same code - multiple users can have same code
                user=user,
                discount_type=source_coupon.discount_type,
                discount_value=source_coupon.discount_value,
                min_purchase=source_coupon.min_purchase,
                max_discount=source_coupon.max_discount,
                valid_from=source_coupon.valid_from,
                valid_until=source_coupon.valid_until,
                is_active=source_coupon.is_active,
                is_common=False,  # This is a user-specific instance
                created_by_admin=True
            )
            user_coupon.save()
        except Exception as save_error:
            # Handle duplicate key error (MongoDB index still exists)
            error_str = str(save_error)
            if "duplicate key" in error_str.lower() or "E11000" in error_str:
                # Check if coupon already exists for this user
                existing = Coupon.objects(code=source_coupon.code, user=user).first()
                if existing:
                    # User already has this coupon, return success
                    return JsonResponse({
                        "success": True,
                        "message": "User already has this coupon",
                        "coupon": {
                            "code": existing.code,
                            "discount_value": existing.discount_value,
                            "discount_type": existing.discount_type,
                            "valid_until": str(existing.valid_until)
                        }
                    }, status=200)
                else:
                    # Try to generate a unique code by appending user ID suffix
                    import random
                    import string
                    unique_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                    user_coupon = Coupon(
                        code=f"{source_coupon.code}-{unique_suffix}",
                        user=user,
                        discount_type=source_coupon.discount_type,
                        discount_value=source_coupon.discount_value,
                        min_purchase=source_coupon.min_purchase,
                        max_discount=source_coupon.max_discount,
                        valid_from=source_coupon.valid_from,
                        valid_until=source_coupon.valid_until,
                        is_active=source_coupon.is_active,
                        is_common=False,
                        created_by_admin=True
                    )
                    user_coupon.save()
            else:
                # Re-raise if it's a different error
                raise

        # Create notification for user
        try:
            from notifications.views import create_notification
            create_notification(
                user=user,
                notification_type='coupon',
                title='New Coupon Received! 🎉',
                message=f'You received a coupon code: {user_coupon.code}. Get {user_coupon.discount_value}{"%" if user_coupon.discount_type == "percentage" else "₹"} off on your next purchase!',
                link='/dashboard',
                metadata={'coupon_id': str(user_coupon.id), 'coupon_code': user_coupon.code}
            )
        except Exception as e:
            print(f"Error creating notification: {e}")

        return JsonResponse({
            "success": True,
            "message": "Coupon sent to user successfully",
            "coupon": {
                "code": user_coupon.code,
                "discount_value": user_coupon.discount_value,
                "discount_type": user_coupon.discount_type,
                "valid_until": str(user_coupon.valid_until)
            }
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in assign_coupon_to_user: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def send_coupon_to_all(request):
    """
    Admin API: Send a coupon to all students.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        coupon_code = data.get("coupon_code", "").strip().upper()
        
        if not coupon_code:
            return JsonResponse({"success": False, "message": "Coupon code is required"}, status=400)

        source_coupon = Coupon.objects(code=coupon_code).first()

        if not source_coupon:
            return JsonResponse({"success": False, "message": "Coupon not found"}, status=404)

        # Get all students
        all_users = User.objects(role='student')
        total_users = all_users.count()
        success_count = 0
        error_count = 0
        skipped_count = 0

        # Create notification helper
        from notifications.views import create_notification

        # Send coupon to each user
        for user in all_users:
            try:
                user_object_id = ObjectId(str(user.id)) if ObjectId.is_valid(str(user.id)) else str(user.id)
                
                # Check if user already has this coupon
                existing_coupon = Coupon.objects(code=source_coupon.code, user=user).first()
                if existing_coupon:
                    skipped_count += 1
                    continue  # Skip users who already have this coupon
                
                # Check if user already used this coupon (for common coupons)
                if source_coupon.is_common and user_object_id in source_coupon.used_by:
                    skipped_count += 1
                    continue  # Skip users who already used it

                # Create a user-specific coupon instance
                try:
                    user_coupon = Coupon(
                        code=source_coupon.code,  # Same code for all users
                        user=user,
                        discount_type=source_coupon.discount_type,
                        discount_value=source_coupon.discount_value,
                        min_purchase=source_coupon.min_purchase,
                        max_discount=source_coupon.max_discount,
                        valid_from=source_coupon.valid_from,
                        valid_until=source_coupon.valid_until,
                        is_active=source_coupon.is_active,
                        is_common=False,
                        created_by_admin=True
                    )
                    user_coupon.save()
                except Exception as save_error:
                    # Handle duplicate key error (MongoDB index still exists)
                    error_str = str(save_error)
                    if "duplicate key" in error_str.lower() or "E11000" in error_str:
                        # Check if coupon already exists for this user
                        existing = Coupon.objects(code=source_coupon.code, user=user).first()
                        if existing:
                            # User already has this coupon, skip
                            skipped_count += 1
                            continue
                        else:
                            # Try to generate a unique code by appending user ID suffix
                            import random
                            import string
                            unique_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                            user_coupon = Coupon(
                                code=f"{source_coupon.code}-{unique_suffix}",
                                user=user,
                                discount_type=source_coupon.discount_type,
                                discount_value=source_coupon.discount_value,
                                min_purchase=source_coupon.min_purchase,
                                max_discount=source_coupon.max_discount,
                                valid_from=source_coupon.valid_from,
                                valid_until=source_coupon.valid_until,
                                is_active=source_coupon.is_active,
                                is_common=False,
                                created_by_admin=True
                            )
                            user_coupon.save()
                    else:
                        # Re-raise if it's a different error
                        raise

                # Create notification
                try:
                    create_notification(
                        user=user,
                        notification_type='coupon',
                        title='Special Coupon for You! 🎉',
                        message=f'You received a coupon code: {user_coupon.code}. Get {user_coupon.discount_value}{"%" if user_coupon.discount_type == "percentage" else "₹"} off!',
                        link='/dashboard',
                        metadata={'coupon_id': str(user_coupon.id), 'coupon_code': user_coupon.code}
                    )
                except Exception as e:
                    print(f"Error creating notification for user {user.id}: {e}")

                success_count += 1
            except Exception as e:
                print(f"Error sending coupon to user {user.id}: {e}")
                error_count += 1

        return JsonResponse({
            "success": True,
            "message": f"Coupon sent to {success_count} users successfully",
            "total_users": total_users,
            "success_count": success_count,
            "error_count": error_count,
            "skipped_count": skipped_count
        }, status=200)

    except Exception as e:
        import traceback
        print(f"Error in send_coupon_to_all: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)

