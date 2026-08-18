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
import traceback    
import jwt
from bson import ObjectId
from django.conf import settings
from users.authentication import authenticate  # custom decorator
from users.auth_helpers import authenticate_user_or_admin, normalize_login_email, normalize_login_password
from common.middleware import restrict
import urllib.request
import urllib.parse
import json
import requests

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


# ================= JWT HELPER =================
SECRET_KEY = settings.SECRET_KEY

# Distinguishes signup OTPs from password-reset OTPs in PasswordResetToken.token
# without changing models.py
SIGNUP_TOKEN_PREFIX = "signup:"


def generate_jwt(payload):
    """Generate a JWT token with a 7-day expiry."""
    payload["exp"] = datetime.utcnow() + timedelta(days=7)
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token


def _normalize_auth_email(email):
    return (email or "").strip().lower()


def _is_signup_otp_token(token_doc):
    token_value = getattr(token_doc, "token", None) or ""
    return str(token_value).startswith(SIGNUP_TOKEN_PREFIX)


def _find_otp_token(email, otp, used, signup_only):
    """Find an OTP token; signup_only=True for signup, False for password reset."""
    candidates = PasswordResetToken.objects(email=email, otp=otp, used=used)
    for token_doc in candidates:
        is_signup = _is_signup_otp_token(token_doc)
        if signup_only and is_signup:
            return token_doc
        if not signup_only and not is_signup:
            return token_doc
    return None


def _invalidate_unused_signup_otps(email):
    try:
        old_tokens = PasswordResetToken.objects(email=email, used=False)
        for token in old_tokens:
            if _is_signup_otp_token(token):
                token.used = True
                token.save()
    except Exception as e:
        print(f"Error invalidating old signup tokens: {e}")


# ================= reCAPTCHA HELPER =================
def verify_recaptcha(token):
    """
    Verify reCAPTCHA token with Google's API.
    Returns (True, None) if valid, (False, error_message) otherwise.
    """
    
    if not token:
        return False, "reCAPTCHA token is missing"
    
    try:
        response = requests.post(
            settings.RECAPTCHA_VERIFY_URL,
            data={
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': token
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"reCAPTCHA API returned status {response.status_code}: {response.text}")
            return False, "reCAPTCHA verification service unavailable. Please try again."
        
        result = response.json()
        success = result.get('success', False)
        
        if not success:
            error_codes = result.get('error-codes', [])
            error_message = "reCAPTCHA verification failed. Please try again."
            
            # Provide more specific error messages
            if 'invalid-input-secret' in error_codes:
                error_message = "reCAPTCHA configuration error. Please contact support."
                print(f"reCAPTCHA error: Invalid secret key")
            elif 'invalid-input-response' in error_codes:
                error_message = "reCAPTCHA verification failed. Please complete the captcha again."
                print(f"reCAPTCHA error: Invalid token - {token[:20]}...")
            elif 'timeout-or-duplicate' in error_codes:
                error_message = "reCAPTCHA token expired. Please complete the captcha again."
                print(f"reCAPTCHA error: Token timeout or duplicate")
            elif 'bad-request' in error_codes:
                error_message = "reCAPTCHA verification failed. Please try again."
                print(f"reCAPTCHA error: Bad request - {error_codes}")
            else:
                print(f"reCAPTCHA error codes: {error_codes}")
            
            return False, error_message
        
        return True, None
        
    except requests.exceptions.Timeout:
        print("reCAPTCHA verification timeout")
        return False, "reCAPTCHA verification timed out. Please try again."
    except requests.exceptions.RequestException as e:
        print(f"reCAPTCHA verification network error: {e}")
        return False, "Network error during reCAPTCHA verification. Please check your connection and try again."
    except Exception as e:
        print(f"reCAPTCHA verification error: {e}")
        import traceback
        traceback.print_exc()
        return False, "reCAPTCHA verification error. Please try again."


# ================= SIGNUP EMAIL OTP =================
@api_view(["POST"])
@permission_classes([AllowAny])
def send_signup_otp(request):
    """Send OTP to verify email before signup. Does not create a user."""
    try:
        data = request.data
        email = _normalize_auth_email(data.get("email") if hasattr(data, "get") else None)
        fullname = (data.get("fullname") or "").strip() if hasattr(data, "get") else ""

        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects(email__iexact=email).first():
            return Response(
                {"error": "Email already exists. Please login or use a different email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        otp = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        _invalidate_unused_signup_otps(email)

        try:
            unique_token = f"{SIGNUP_TOKEN_PREFIX}{uuid.uuid4()}"
            signup_token = PasswordResetToken(
                email=email,
                otp=otp,
                token=unique_token,
                expires_at=expires_at,
            )
            signup_token.save()
        except Exception as e:
            print(f"Error creating signup OTP token: {e}")
            return Response(
                {"error": "Failed to create verification code. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            from email_templates.utils import get_email_template, send_template_email, unpack_template_data

            user_name = fullname if fullname else "Student"
            template_context = {"name": user_name, "email": email, "otp": otp}

            template_data = get_email_template("Signup Email OTP", template_context)
            if not template_data:
                template_data = get_email_template("Email Verification OTP", template_context)
            if not template_data:
                # Reuse existing active password-reset OTP template so signup works
                # without requiring a new CMS template immediately.
                template_data = get_email_template("Password Reset OTP", template_context)

            if not template_data:
                print("✗ ERROR: No email template found for signup OTP")
                return Response(
                    {"error": "Email template not configured. Please contact administrator."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            subject, html_message, plain_message, _attachments = unpack_template_data(template_data)
            print(f"✓ Sending signup OTP email to {email} (subject: {subject[:50]}...)")
            send_template_email([email], template_data, fail_silently=False)
            print(f"✓ Signup OTP email sent successfully to {email}")
        except Exception as e:
            print(f"✗ Error sending signup OTP email: {e}")
            import traceback
            print(traceback.format_exc())
            return Response(
                {"error": "Failed to send email. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"success": True, "message": "OTP has been sent to your email."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        import traceback
        print(f"Send signup OTP error: {e}")
        print(traceback.format_exc())
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_signup_otp(request):
    """Verify email OTP for signup (marks token used; register consumes it)."""
    try:
        data = request.data
        if not data or (not isinstance(data, dict) and not hasattr(data, "get")):
            try:
                data = json.loads(request.body.decode("utf-8"))
            except Exception as e:
                return Response(
                    {"error": f"Invalid JSON in request body: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        email = _normalize_auth_email(data.get("email") if hasattr(data, "get") else None)
        otp = str((data.get("otp") if hasattr(data, "get") else None) or "").strip()

        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not otp:
            return Response({"error": "OTP is required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects(email__iexact=email).first():
            return Response(
                {"error": "Email already exists. Please login."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signup_token = _find_otp_token(email, otp, used=False, signup_only=True)

        if not signup_token:
            used_token = _find_otp_token(email, otp, used=True, signup_only=True)
            if used_token:
                return Response(
                    {"error": "This OTP has already been used. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return Response(
                {"error": "Invalid OTP. Please check and try again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if datetime.utcnow() > signup_token.expires_at:
            signup_token.used = True
            signup_token.save()
            return Response(
                {"error": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signup_token.used = True
        signup_token.save()

        return Response(
            {"success": True, "message": "Email verified successfully"},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        import traceback
        print(f"Verify signup OTP error: {e}")
        print(traceback.format_exc())
        return Response(
            {"error": f"An error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ================= REGISTER =================
@api_view(["POST"])
def register_user(request):
    try:
        data = request.data
        email = _normalize_auth_email(data.get("email"))
        fullname = data.get("fullname", "").strip()
        password = data.get("password")
        phone_number = data.get("phone_number", "").strip()
        recaptcha_token = data.get("recaptcha_token")
        otp = str(data.get("otp") or "").strip()
        
        # Verify reCAPTCHA token
        recaptcha_valid, recaptcha_error = verify_recaptcha(recaptcha_token)
        if not recaptcha_valid:
            return Response(
                {'error': recaptcha_error or 'reCAPTCHA verification failed. Please try again.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            print("recaptcha error : ",recaptcha_error)
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not otp:
            return Response(
                {"error": "Email verification OTP is required. Please verify your email first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if User.objects(email__iexact=email).first():
            return Response(
                {"error": "Email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Require a valid signup OTP for this email (verified used=True, or still unused)
        signup_token = _find_otp_token(email, otp, used=True, signup_only=True)
        if not signup_token:
            signup_token = _find_otp_token(email, otp, used=False, signup_only=True)

        if not signup_token:
            return Response(
                {"error": "Invalid or unverified OTP. Please verify your email first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if datetime.utcnow() > signup_token.expires_at:
            signup_token.used = True
            signup_token.save()
            return Response(
                {"error": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark consumed before creating user (idempotent if already used from verify step)
        if not signup_token.used:
            signup_token.used = True
            signup_token.save()
        
        # ✅ Create user
        user = User(
            fullname=fullname if fullname else "Unknown User",
            email=email,
            phone_number=phone_number if phone_number else "N/A",
        )
        user.set_password(password)
        user.save()

        # Expire signup OTP so it cannot be reused after successful registration
        try:
            signup_token.expires_at = datetime.utcnow() - timedelta(seconds=1)
            signup_token.save()
        except Exception as e:
            print(f"Warning: failed to expire signup OTP after register: {e}")
        
        # ✅ Generate JWT token (use consistent key "id")
        # token = generate_jwt({"id": str(user.id), "email": user.email, "role": user.role})
        token = generate_jwt({"id": str(user.id), "role": user.role})

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
        print("error : ",e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= LOGIN =================
@api_view(["POST"])
def login_user(request):
    try:
        data = request.data
        email = normalize_login_email(data.get("email"))
        password = normalize_login_password(data.get("password"))
        
        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        auth_result = authenticate_user_or_admin(email, password)
        if not auth_result:
            return Response(
                {"error": "Invalid email or password"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if auth_result.get("inactive_admin"):
            return Response(
                {"error": "This admin account is inactive"},
                status=status.HTTP_403_FORBIDDEN,
            )

        account_type = auth_result["account_type"]
        account = auth_result["account"]

        if account_type == "admin":
            token = generate_jwt({
                "id": str(account.id),
                "role": "admin",
                "name": account.name or "Admin",
                "email": account.email or "",
            })
            return Response(
                {
                    "success": True,
                    "message": "Login successful",
                    "token": token,
                    "user": {
                        "id": str(account.id),
                        "fullname": account.name,
                        "email": account.email,
                        "role": "admin",
                        "phone_number": "",
                        "location": "",
                    },
                },
                status=status.HTTP_200_OK,
            )

        token = generate_jwt({"id": str(account.id), "role": account.role})
        return Response(
            {
                "success": True,
                "message": "Login successful",
                "token": token,
                "user": {
                    "id": str(account.id),
                    "fullname": account.fullname,
                    "email": account.email,
                    "role": account.role,
                    "phone_number": getattr(account, "phone_number", ""),
                    "location": getattr(account, "location", ""),
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
            print("invalid token payload: missing user ID or role")
            return Response(
                {"error": "Invalid token payload: missing user ID or role"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ============================
        # 🧩 STUDENT USER
        # ============================
        if role == "student":
            print("student role found")
            try:
                user = User.objects.get(id=ObjectId(user_id))
                print("user found")
            except User.DoesNotExist:
                print("user not found")
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
                if "profile_picture" in data:
                    # Store profile picture URL or base64
                    user.profile_picture = data["profile_picture"]
                # Note: email should not be changed via profile update
                user.save()
            
            # Build user data safely
            user_data = {
                "id": str(user.id),
                "fullname": user.fullname,
                "email": user.email,
                "phone_number": getattr(user, "phone_number", ""),
                "location": getattr(user, "location", ""),
                "profile_picture": getattr(user, "profile_picture", ""),
                "role": "student",
            }

            # Handle enrolled_courses safely
            if hasattr(user, "enrolled_courses") and user.enrolled_courses:
                try:
                    user_data["enrolled_courses"] = [
                        str(course.id) if hasattr(course, 'id') else str(course)
                        for course in user.enrolled_courses
                    ]
                    print("enrolled courses found")
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
            print("admin role found")
            try:
                admin = Admin.objects.get(_id=ObjectId(user_id))
                print("admin found")
            except Admin.DoesNotExist:
                print("admin not found")
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
            print("unknown role in token")
            return Response(
                {"error": f"Unknown role '{role}' in token"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    except User.DoesNotExist:
        print("student user not found")
        return Response({"error": "Student user not found"}, status=status.HTTP_404_NOT_FOUND)
    except Admin.DoesNotExist:
        print("admin not found")
        return Response({"error": "Admin not found"}, status=status.HTTP_404_NOT_FOUND)
    except jwt.ExpiredSignatureError:
        print("token has expired")
        return Response({"error": "Token has expired"}, status=status.HTTP_401_UNAUTHORIZED)
    except jwt.InvalidTokenError:
        print("invalid token")
        return Response({"error": "Invalid token"}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        print("error : ",e)
        print(traceback.format_exc())
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
    email = normalize_login_email(request.data.get("email"))
    password = normalize_login_password(request.data.get("password"))

    if not email or not password:
        return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    auth_result = authenticate_user_or_admin(email, password)
    if not auth_result:
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    if auth_result.get("inactive_admin"):
        return Response({"error": "This admin account is inactive"}, status=status.HTTP_403_FORBIDDEN)

    account_type = auth_result["account_type"]
    account = auth_result["account"]

    if account_type == "user" and getattr(account, "role", "") != "admin":
        return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

    if account_type == "admin":
        admin_id = str(account.id)
        admin_name = account.name or "Admin"
        admin_email = account.email or ""
        admin_role = account.role
    else:
        admin_id = str(account.id)
        admin_name = account.fullname or "Admin"
        admin_email = account.email or ""
        admin_role = "admin"

    token = generate_jwt({
        "id": admin_id,
        "role": "admin",
        "name": admin_name,
        "email": admin_email,
    })

    return Response({
        "message": "Admin login successful",
        "token": token,
        "admin": {
            "id": admin_id,
            "name": admin_name,
            "email": admin_email,
            "role": admin_role,
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


# ================= FORGOT PASSWORD =================
@api_view(["POST"])
@permission_classes([AllowAny])
def forgot_password(request):
    """Send OTP to user's email for password reset."""
    try:
        # Get data from request
        data = request.data
        
        # Handle both dict and QueryDict
        if hasattr(data, 'get'):
            email = data.get("email")
        else:
            email = data.get("email") if isinstance(data, dict) else None
        
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize email (lowercase)
        email = email.strip().lower()

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

        # Invalidate old password-reset tokens for this email (not signup OTPs)
        try:
            old_tokens = PasswordResetToken.objects(email=email, used=False)
            for token in old_tokens:
                if _is_signup_otp_token(token):
                    continue
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
            from email_templates.utils import get_email_template, send_template_email, unpack_template_data
            
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
            
            subject, html_message, plain_message, _attachments = unpack_template_data(template_data)
            print(f"✓ Using email template 'Password Reset OTP' for {email}")
            print(f"  Subject: {subject[:50]}...")
            
            send_template_email([email], template_data, fail_silently=False)
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
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP for password reset."""
    try:
        # Get data from request.data (DRF handles JSON parsing automatically)
        data = request.data
        
        # If request.data is empty or not a dict, try parsing body directly
        if not data or (not isinstance(data, dict) and not hasattr(data, 'get')):
            import json
            try:
                body = request.body
                if not body:
                    return Response(
                        {"error": "Request body is empty. Please provide email and OTP."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                data = json.loads(body.decode('utf-8'))
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as e:
                return Response(
                    {"error": f"Invalid JSON in request body: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle both dict and QueryDict
        if hasattr(data, 'get'):
            email = data.get("email")
            otp = data.get("otp")
        else:
            email = data.get("email") if isinstance(data, dict) else None
            otp = data.get("otp") if isinstance(data, dict) else None

        # Validate required fields
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not otp:
            return Response(
                {"error": "OTP is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize email (lowercase)
        email = email.strip().lower()
        
        # Normalize OTP (remove spaces if any)
        otp = str(otp).strip()

        # Debug logging
        print(f"[DEBUG verify_otp] Looking for token with email: {email}, otp: {otp}")
        
        reset_token = _find_otp_token(email, otp, used=False, signup_only=False)

        if not reset_token:
            # Check if OTP exists but is already used
            used_token = _find_otp_token(email, otp, used=True, signup_only=False)
            
            if used_token:
                return Response(
                    {"error": "This OTP has already been used. Please request a new one."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if email exists but OTP doesn't match
            email_tokens = None
            for t in PasswordResetToken.objects(email=email, used=False):
                if not _is_signup_otp_token(t):
                    email_tokens = t
                    break
            if email_tokens:
                return Response(
                    {"error": "Invalid OTP. Please check and try again."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {"error": "Invalid OTP or email. Please request a new OTP."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check expiration
        current_time = datetime.utcnow()
        if current_time > reset_token.expires_at:
            # Clean up expired token
            reset_token.used = True
            reset_token.save()
            return Response(
                {"error": "OTP has expired. Please request a new one."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark token as used
        reset_token.used = True
        reset_token.save()

        return Response(
            {
            "success": True,
            "message": "OTP verified successfully"
            },
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
@permission_classes([AllowAny])
def reset_password(request):
    """Reset password after OTP verification."""
    try:
        # Get data from request
        data = request.data
        
        # Handle both dict and QueryDict
        if hasattr(data, 'get'):
            email = data.get("email")
            otp = data.get("otp")
            new_password = data.get("new_password")
        else:
            email = data.get("email") if isinstance(data, dict) else None
            otp = data.get("otp") if isinstance(data, dict) else None
            new_password = data.get("new_password") if isinstance(data, dict) else None

        # Validate required fields with specific error messages
        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not otp:
            return Response(
                {"error": "OTP is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not new_password:
            return Response(
                {"error": "New password is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Normalize email (lowercase)
        email = email.strip().lower()
        
        # Normalize OTP (remove spaces if any)
        otp = str(otp).strip()
        
        # Validate password strength
        if len(new_password) < 8:
            return Response(
                {"error": "Password must be at least 8 characters long"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Debug logging
        print(f"[DEBUG reset_password] Looking for used token with email: {email}, otp: {otp}")
        
        # Verify OTP was used (from verify_otp step) — password-reset tokens only
        reset_token = _find_otp_token(email, otp, used=True, signup_only=False)

        if not reset_token:
            # Check if OTP exists but hasn't been verified yet
            unverified_token = _find_otp_token(email, otp, used=False, signup_only=False)
            
            if unverified_token:
                return Response(
                    {"error": "Please verify the OTP first before resetting your password."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(
                {"error": "Invalid or unverified OTP. Please verify the OTP first."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if token is still valid (within 15 minutes of creation)
        current_time = datetime.utcnow()
        if current_time > reset_token.expires_at:
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
        # user.set_password(new_password)
        # user.save()

        try:
            validate_password(new_password, user=user)
        except ValidationError as e:
            return Response(
                {"error": list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST
            )

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
            # Random unguessable password — Google users never log in with it,
            # but the MongoEngine User model requires a hashed password.
            user.set_password(
                "".join(random.choices(string.ascii_letters + string.digits, k=32))
            )
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

        # if user:
        #     # User exists, login
        #     token = generate_jwt({"id": str(user.id), "role": user.role})
        #     return Response(
        #         {
        #             "success": True,
        #             "message": "Login successful",
        #             "token": token,
        #             "user": {
        #                 "id": str(user.id),
        #                 "fullname": user.fullname,
        #                 "email": user.email,
        #                 "role": user.role,
        #             },
        #         },
        #         status=status.HTTP_200_OK,
        #     )
        # else:
        #     # New user, create account
        #     user = User(
        #         fullname=name if name else "Google User",
        #         email=email,
        #         phone_number="N/A",
        #         role="student"
        #     )
        #     # Set a random password (user won't need it for Google login)
        #     user.set_password("".join(random.choices(string.ascii_letters + string.digits, k=32)))
        #     user.save()

        #     token = generate_jwt({"id": str(user.id), "role": user.role})
        #     return Response(
        #         {
        #             "success": True,
        #             "message": "Account created and logged in successfully",
        #             "token": token,
        #             "user": {
        #                 "id": str(user.id),
        #                 "fullname": user.fullname,
        #                 "email": user.email,
        #                 "role": user.role,
        #             },
        #         },
        #         status=status.HTTP_201_CREATED,
        #     )
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

