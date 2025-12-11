
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import User, Admin, PasswordResetToken
from .serializers import UserSerializer, AdminSerializer
from django.contrib.auth.hashers import check_password 
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.tokens import AccessToken
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail
import random
import string
import uuid

import jwt
from bson import ObjectId
from django.conf import settings
from users.authentication import authenticate  # custom decorator
from common.middleware import restrict


# ================= JWT HELPER =================
SECRET_KEY = settings.SECRET_KEY

def generate_jwt(payload):
    """Generate a JWT token with a 7-day expiry."""
    payload["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ================= REGISTER =================
@api_view(["POST"])
def register_user(request):
    try:
        data = request.data
        email = data.get("email")
        fullname = data.get("fullname", "").strip()
        password = data.get("password")
        phone_number = data.get("phone_number", "").strip()

        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects(email=email).first():
            return Response(
                {"error": "Email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ✅ Create user
        user = User(
            fullname=fullname if fullname else "Unknown User",
            email=email,
            phone_number=phone_number if phone_number else "N/A",
        )
        user.set_password(password)
        user.save()

        # ✅ Generate JWT token (use consistent key "id")
        token = generate_jwt({"id": str(user.id), "email": user.email, "role": user.role})

        return Response(
            {
                "success": True,
                "message": "User registered successfully.",
                "token": token,
                "user": {
                    "id": str(user.id),
                    "fullname": user.fullname,
                    "email": user.email,
                    "role": user.role,
                    "phone_number": user.phone_number,
                    "location": getattr(user, "location", ""),
                },
            },
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= LOGIN =================
@api_view(["POST"])
def login_user(request):
    try:
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects(email=email).first()
        if not user:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password):
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ Generate consistent token
        token = generate_jwt({"id": str(user.id), "role": user.role})

        return Response(
            {
                "success": True,
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": str(user.id),
                    "fullname": user.fullname,
                    "email": user.email,
                    "role": user.role,
                    "phone_number": getattr(user, "phone_number", ""),
                    "location": getattr(user, "location", ""),
                },
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        import traceback
        print(f"Login error: {e}")
        print(traceback.format_exc())
        return Response(
            {"error": "An error occurred during login. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================= CURRENT USER =================
@api_view(["GET"])
@authenticate  # uses token
def current_user(request):
    """Get user info from decoded JWT"""
    try:
        user_id = request.user.get("id")
        user = User.objects.get(id=ObjectId(user_id))

        return Response(
            {
                "id": str(user.id),
                "fullname": user.fullname,
                "email": user.email,
                "phone_number": user.phone_number,
                "role": user.role,
                "location": getattr(user, "location", ""),
            },
            status=status.HTTP_200_OK,
        )
    except User.DoesNotExist:
        return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# ================= USER PROFILE =================
# @api_view(["GET"])
# @authenticate
# def user_profile(request):
#     """Get currently logged-in user's profile."""
#     try:
#         user_id = request.user.get("id")
#         if not user_id:
#             return Response(
#                 {"error": "User ID not found in token"},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )

#         user = User.objects.get(id=ObjectId(user_id))

#         return Response(
#             {
#                 "id": str(user.id),
#                 "fullname": user.fullname,
#                 "email": user.email,
#                 "phone_number": user.phone_number,
#                 "role": user.role,
#                 "location": user.location,
#             },
#             status=status.HTTP_200_OK,
#         )

#     except User.DoesNotExist:
#         return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
#     except jwt.ExpiredSignatureError:
#         return Response({"error": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
#     except jwt.InvalidTokenError:
#         return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
#     except Exception as e:
#         return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from bson import ObjectId
import jwt
from .models import User, Admin


@api_view(["GET", "PUT"])
@authenticate
def user_profile(request):
    """Return profile info for logged-in student or admin based on token role."""
    try:
        payload = request.user  # contains {'id': ..., 'role': ..., 'exp': ...}
        print("payload : ",payload)
        user_id = payload.get("id")
        role = payload.get("role")

        if not user_id or not role:
            return Response(
                {"error": "Invalid token payload: missing user ID or role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================
        # 🧩 STUDENT USER
        # ============================
        if role == "student":
            try:
                user = User.objects.get(id=ObjectId(user_id))
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Handle PUT request for updating profile
            if request.method == "PUT":
                data = request.data
                # Update allowed fields (exclude password, role, enrolled_courses)
                if "fullname" in data:
                    user.fullname = data["fullname"]
                if "phone_number" in data:
                    user.phone_number = data["phone_number"]
                if "location" in data:
                    user.location = data["location"]
                # Note: email should not be changed via profile update
                user.save()
            
            # Build user data safely
            user_data = {
                "id": str(user.id),
                "fullname": user.fullname,
                "email": user.email,
                "phone_number": getattr(user, "phone_number", ""),
                "location": getattr(user, "location", ""),
                "role": "student",
            }

            # Handle enrolled_courses safely
            if hasattr(user, "enrolled_courses") and user.enrolled_courses:
                try:
                    user_data["enrolled_courses"] = [
                        str(course.id) if hasattr(course, 'id') else str(course)
                        for course in user.enrolled_courses
                    ]
                except Exception as e:
                    print(f"Error processing enrolled_courses: {e}")
                    user_data["enrolled_courses"] = []
            else:
                user_data["enrolled_courses"] = []

            return Response(
                {"success": True, "role": "student", "profile": user_data},
                status=status.HTTP_200_OK,
            )

            

        # ============================
        # 🧩 ADMIN USER
        # ============================
        elif role == "admin":
            try:
                admin = Admin.objects.get(_id=ObjectId(user_id))
            except Admin.DoesNotExist:
                return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Handle PUT request for updating profile
            if request.method == "PUT":
                data = request.data
                # Update allowed fields (exclude password, role, email)
                if "name" in data:
                    admin.name = data["name"]
                # Note: email should not be changed via profile update
                admin.save()
            
            # Build admin data safely
            admin_data = {
                "id": str(admin._id),
                "name": admin.name,
                "email": admin.email,
                "role": "admin",
                "is_active": getattr(admin, "is_active", True),
            }

            return Response(
                {"success": True, "role": "admin", "profile": admin_data},
                status=status.HTTP_200_OK,
            )

        else:
            return Response(
                {"error": f"Unknown role '{role}' in token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except User.DoesNotExist:
        return Response({"error": "Student user not found"}, status=status.HTTP_404_NOT_FOUND)
    except Admin.DoesNotExist:
        return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
    except jwt.ExpiredSignatureError:
        return Response({"error": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print("error : ",e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from bson import ObjectId
from datetime import datetime, timedelta
import jwt
from users.authentication import authenticate  # your custom decorator
from .models import Admin

SECRET_KEY = settings.SECRET_KEY


# ------------------ JWT Helper ------------------
def generate_jwt(payload):
    """Generate JWT with 7 days expiry."""
    payload["exp"] = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ------------------ Admin Register ------------------
@api_view(["POST"])
def register_admin(request):
    name = request.data.get("name")
    email = request.data.get("email")
    password = request.data.get("password")
    confirm_password = request.data.get("confirm_password")

    # Validation
    if not all([name, email, password, confirm_password]):
        return Response({"error": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    if Admin.objects(email=email).first():
        return Response({"error": "Email already registered"}, status=status.HTTP_400_BAD_REQUEST)

    # Create admin
    admin = Admin(name=name, email=email)
    admin.set_password(password)
    admin.save()

    return Response({"message": "Admin registered successfully"}, status=status.HTTP_201_CREATED)


# ------------------ Admin Login ------------------
@api_view(["POST"])
def login_admin(request):
    email = request.data.get("email")
    password = request.data.get("password")

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    admin = Admin.objects(email=email).first()
    if not admin:
        return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)

    if not admin.check_password(password):
        return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

    # Generate JWT
    token = generate_jwt({"id": str(admin.id), "role": "admin"})

    return Response({
        "message": "Admin login successful",
        "token": token,
        "admin": {
            "id": str(admin.id),
            "name": admin.name,
            "email": admin.email,
            "role": admin.role
        }
    }, status=status.HTTP_200_OK)


# ------------------ Admin Profile ------------------
@api_view(["GET"])
@authenticate
def admin_profile(request):
    """Fetch logged-in admin profile from JWT"""
    try:
        user_id = request.user.get("id")
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Admin model uses _id as primary key
        admin = Admin.objects(_id=ObjectId(user_id)).first()
        
        if not admin:
            return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            "admin": {
                "id": str(admin._id),
                "name": admin.name,
                "email": admin.email,
                "role": admin.role
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        import traceback
        print(f"Admin profile error: {e}")
        print(traceback.format_exc())
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------ Update Admin Email/Password ------------------
@api_view(["PUT", "PATCH"])
@authenticate
def update_admin_credentials(request):
    """Update admin email and/or password"""
    try:
        user_id = request.user.get("id")
        if not user_id:
            return Response({"error": "User not authenticated"}, status=status.HTTP_401_UNAUTHORIZED)
        
        # Admin model uses _id as primary key
        admin = Admin.objects(_id=ObjectId(user_id)).first()
        if not admin:
            return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data
        
        # Update email if provided
        new_email = data.get("email")
        if new_email:
            # Check if email is already taken by another admin
            existing_admin = Admin.objects(email=new_email).first()
            if existing_admin and str(existing_admin._id) != str(admin._id):
                return Response({"error": "Email already in use"}, status=status.HTTP_400_BAD_REQUEST)
            admin.email = new_email
        
        # Update password if provided
        new_password = data.get("password")
        current_password = data.get("current_password")
        
        if new_password:
            # Require current password for security
            if not current_password:
                return Response({"error": "Current password is required to change password"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify current password
            if not admin.check_password(current_password):
                return Response({"error": "Current password is incorrect"}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Set new password
            admin.set_password(new_password)
        
        admin.save()
        
        return Response({
            "message": "Credentials updated successfully",
            "admin": {
                "id": str(admin._id),
                "name": admin.name,
                "email": admin.email,
                "role": admin.role
            }
        }, status=status.HTTP_200_OK)
        
    except Admin.DoesNotExist:
        return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    user_id = request.user.get("id")

    try:
        admin = Admin.objects(_id=ObjectId(user_id)).first()
    except Exception:
        return Response({"error": "Invalid user ID"}, status=status.HTTP_400_BAD_REQUEST)

    if not admin:
        return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "id": str(admin.id),
        "name": admin.name,
        "email": admin.email,
        "role": admin.role,
        "is_active": admin.is_active,
        "created_at": admin.created_at
    }, status=status.HTTP_200_OK)


# ================= FORGOT PASSWORD =================
@api_view(["POST"])
def forgot_password(request):
    """Send OTP to user's email for password reset."""
    try:
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects(email=email).first()
        if not user:
            # Don't reveal if email exists for security
            return Response(
                {"message": "If the email exists, a password reset OTP has been sent."},
                status=status.HTTP_200_OK
            )

        # Generate 6-digit OTP
        otp = ''.join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Invalidate old tokens for this email
        try:
            old_tokens = PasswordResetToken.objects(email=email, used=False)
            for token in old_tokens:
                token.used = True
                token.save()
        except Exception as e:
            print(f"Error invalidating old tokens: {e}")
            # Continue anyway

        # Create new token
        try:
            # Generate a unique token ID to satisfy MongoDB unique index
            unique_token = str(uuid.uuid4())
            
            reset_token = PasswordResetToken(
                email=email,
                otp=otp,
                token=unique_token,  # Set unique token to satisfy MongoDB index
                expires_at=expires_at
            )
            reset_token.save()
        except Exception as e:
            print(f"Error creating reset token: {e}")
            return Response(
                {"error": "Failed to create reset token. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Send email using ONLY template - no hardcoded content
        try:
            from email_templates.utils import get_email_template
            
            # Get user name for template
            user_name = user.fullname if user else "Student"
            
            # Get email template - REQUIRED, no fallback
            template_data = get_email_template("Password Reset OTP", {
                "name": user_name,
                "email": email,
                "otp": otp
            })
            
            if not template_data:
                print(f"✗ ERROR: Email template 'Password Reset OTP' not found or not active!")
                print(f"  Admin must create this template in Email Templates section.")
                return Response(
                    {"error": "Email template not configured. Please contact administrator."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            subject, html_message, plain_message = template_data
            print(f"✓ Using email template 'Password Reset OTP' for {email}")
            print(f"  Subject: {subject[:50]}...")
            
            # Send email using template content only
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✓ Password reset OTP email sent successfully to {email}")
            
        except Exception as e:
            print(f"✗ Error sending email: {e}")
            import traceback
            print(traceback.format_exc())
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {"message": "OTP has been sent to your email."},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        import traceback
        print(f"Forgot password error: {e}")
        print(traceback.format_exc())
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def verify_otp(request):
    """Verify OTP for password reset."""
    try:
        # Get data from request.data (DRF handles JSON parsing automatically)
        data = request.data
        
        # If request.data is empty or not a dict, try parsing body directly
        if not data or not isinstance(data, dict):
            import json
            try:
                body = request.body
                if not body:
                    return Response(
                        {"error": "Request body is empty"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                data = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as e:
                return Response(
                    {"error": f"Invalid JSON in request body: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        email = data.get("email")
        otp = data.get("otp")

        if not email or not otp:
            return Response(
                {"error": "Email and OTP are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        reset_token = PasswordResetToken.objects(
            email=email,
            otp=otp,
            used=False
        ).first()

        if not reset_token:
            return Response(
                {"error": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if datetime.utcnow() > reset_token.expires_at:
            return Response(
                {"error": "OTP has expired"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark token as used
        reset_token.used = True
        reset_token.save()

        return Response(
            {"message": "OTP verified successfully"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        import traceback
        print(f"Verify OTP error: {e}")
        print(traceback.format_exc())
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
def reset_password(request):
    """Reset password after OTP verification."""
    try:
        email = request.data.get("email")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")

        if not all([email, otp, new_password]):
            return Response(
                {"error": "Email, OTP, and new password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify OTP was used (from verify_otp step)
        reset_token = PasswordResetToken.objects(
            email=email,
            otp=otp,
            used=True
        ).first()

        if not reset_token:
            return Response(
                {"error": "Invalid or unverified OTP"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if token is still valid (within 15 minutes of creation)
        if datetime.utcnow() > reset_token.expires_at:
            return Response(
                {"error": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects(email=email).first()
        if not user:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update password
        user.set_password(new_password)
        user.save()

        # Send password reset confirmation email
        try:
            from enrollments.email_utils import send_password_reset_confirmation_email
            reset_time = datetime.utcnow()
            send_password_reset_confirmation_email(
                user_email=user.email,
                user_name=user.fullname,
                reset_time=reset_time
            )
        except Exception as email_error:
            # Log error but don't fail the password reset
            print(f"Error sending password reset confirmation email: {email_error}")
            import traceback
            print(traceback.format_exc())

        return Response(
            {"message": "Password reset successfully"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================= GOOGLE OAUTH =================
@api_view(["POST"])
def google_oauth(request):
    """Handle Google OAuth authentication."""
    try:
        data = request.data
        google_id = data.get("google_id")
        email = data.get("email")
        name = data.get("name", "")
        profile_picture = data.get("profile_picture", "")

        if not google_id or not email:
            return Response(
                {"error": "Google ID and email are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user exists
        user = User.objects(email=email).first()

        if user:
            # User exists, login
            token = generate_jwt({"id": str(user.id), "role": user.role})
            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": str(user.id),
                        "fullname": user.fullname,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                status=status.HTTP_200_OK,
            )
        else:
            # New user, create account
            user = User(
                fullname=name if name else "Google User",
                email=email,
                phone_number="N/A",
                role="student"
            )
            # Set a random password (user won't need it for Google login)
            user.set_password("".join(random.choices(string.ascii_letters + string.digits, k=32)))
            user.save()

            token = generate_jwt({"id": str(user.id), "role": user.role})
            return Response(
                {
                    "success": True,
                    "message": "Account created and logged in successfully",
                    "token": token,
                    "user": {
                        "id": str(user.id),
                        "fullname": user.fullname,
                        "email": user.email,
                        "role": user.role,
                    },
                },
                status=status.HTTP_201_CREATED,
            )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================= GET ALL USERS (ADMIN) =================
@api_view(["GET"])
@authenticate
@restrict(['admin'])
def get_all_users(request):
    """
    Admin API: Get all users (students) for admin to select and send coupons.
    """
    try:
        # Get all students (exclude admins)
        users = User.objects(role='student').order_by('-id')
        
        users_data = []
        for user in users:
            users_data.append({
                "id": str(user.id),
                "fullname": user.fullname,
                "email": user.email,
                "phone_number": user.phone_number,
            })
        
        return Response({
            "success": True,
            "users": users_data,
            "total": len(users_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print(f"Error in get_all_users: {traceback.format_exc()}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ================= SEARCH USERS BY EMAIL (ADMIN) =================
@api_view(["GET"])
@authenticate
@restrict(['admin'])
def search_users_by_email(request):
    """
    Admin API: Search users by email (for sending coupons).
    """
    try:
        email_query = request.GET.get("email", "").strip().lower()
        
        if not email_query:
            return Response({
                "success": True,
                "users": [],
                "total": 0
            }, status=status.HTTP_200_OK)
        
        # Search users by email (case-insensitive partial match)
        users = User.objects(role='student', email__icontains=email_query).limit(10)
        
        users_data = []
        for user in users:
            users_data.append({
                "id": str(user.id),
                "fullname": user.fullname,
                "email": user.email,
                "phone_number": user.phone_number,
            })
        
        return Response({
            "success": True,
            "users": users_data,
            "total": len(users_data)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        print(f"Error in search_users_by_email: {traceback.format_exc()}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
