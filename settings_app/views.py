import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common.middleware import authenticate, restrict
from .models import AdminSettings, PrivacyPolicy, TermsOfService

@csrf_exempt
def get_public_settings(request):
    """Get public site settings (site name only, no authentication required)."""
    try:
        settings_obj = AdminSettings.objects.first()
        if not settings_obj:
            settings_obj = AdminSettings()
            settings_obj.save()

        return JsonResponse({
            "success": True, 
            "site_name": settings_obj.site_name or "AllExamQuestions",
            "contact_email": getattr(settings_obj, 'contact_email', '') or '',
            "contact_phone": getattr(settings_obj, 'contact_phone', '') or '',
            "contact_address": getattr(settings_obj, 'contact_address', '') or '',
            "contact_website": getattr(settings_obj, 'contact_website', '') or '',
            "providers_carousel_speed": getattr(settings_obj, 'providers_carousel_speed', 1500),
            "providers_logo_size": getattr(settings_obj, 'providers_logo_size', 80),
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_admin_settings(request):
    """Retrieve current admin settings."""
    try:
        settings_obj = AdminSettings.objects.first()
        if not settings_obj:
            settings_obj = AdminSettings().save()

        data = {
            "site_name": settings_obj.site_name,
            "admin_email": settings_obj.admin_email,
            "email_notifications": settings_obj.email_notifications,
            "maintenance_mode": settings_obj.maintenance_mode,
            "default_user_role": settings_obj.default_user_role,
            "session_timeout": settings_obj.session_timeout,
            "contact_email": getattr(settings_obj, 'contact_email', '') or '',
            "contact_phone": getattr(settings_obj, 'contact_phone', '') or '',
            "contact_address": getattr(settings_obj, 'contact_address', '') or '',
            "contact_website": getattr(settings_obj, 'contact_website', '') or '',
            "providers_carousel_speed": getattr(settings_obj, 'providers_carousel_speed', 1500),
            "providers_logo_size": getattr(settings_obj, 'providers_logo_size', 80),
        }

        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_admin_settings(request):
    """Update admin settings via POST request."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
        settings_obj = AdminSettings.objects.first()
        if not settings_obj:
            settings_obj = AdminSettings()

        # Update fields if provided
        settings_obj.site_name = body.get("site_name", settings_obj.site_name)
        settings_obj.admin_email = body.get("admin_email", settings_obj.admin_email)
        settings_obj.email_notifications = body.get("email_notifications", settings_obj.email_notifications)
        settings_obj.maintenance_mode = body.get("maintenance_mode", settings_obj.maintenance_mode)
        settings_obj.default_user_role = body.get("default_user_role", settings_obj.default_user_role)
        settings_obj.session_timeout = body.get("session_timeout", settings_obj.session_timeout)
        
        # Update contact details if provided
        if "contact_email" in body:
            settings_obj.contact_email = body.get("contact_email", "")
        if "contact_phone" in body:
            settings_obj.contact_phone = body.get("contact_phone", "")
        if "contact_address" in body:
            settings_obj.contact_address = body.get("contact_address", "")
        if "contact_website" in body:
            settings_obj.contact_website = body.get("contact_website", "")
        
        # Update Popular Providers carousel settings
        if "providers_carousel_speed" in body:
            speed = body.get("providers_carousel_speed", 1500)
            settings_obj.providers_carousel_speed = max(500, min(10000, int(speed)))  # Clamp between 500ms and 10s
        if "providers_logo_size" in body:
            size = body.get("providers_logo_size", 80)
            settings_obj.providers_logo_size = max(40, min(200, int(size)))  # Clamp between 40px and 200px
        
        settings_obj.save()

        return JsonResponse({"success": True, "message": "Settings updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= PRIVACY POLICY =================
@csrf_exempt
def get_privacy_policy(request):
    """Get privacy policy content (public endpoint)."""
    try:
        policy = PrivacyPolicy.objects.first()
        if not policy:
            policy = PrivacyPolicy(content="Privacy policy content will be updated by admin.")
            policy.save()
        
        return JsonResponse({
            "success": True,
            "content": policy.content,
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_privacy_policy(request):
    """Update privacy policy content (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        content = body.get("content", "")
        
        if not content:
            return JsonResponse({"success": False, "error": "Content is required"}, status=400)
        
        policy = PrivacyPolicy.objects.first()
        if not policy:
            policy = PrivacyPolicy()
        
        policy.content = content
        policy.updated_at = datetime.utcnow()
        policy.save()
        
        return JsonResponse({"success": True, "message": "Privacy policy updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= TERMS OF SERVICE =================
@csrf_exempt
def get_terms_of_service(request):
    """Get terms of service content (public endpoint)."""
    try:
        terms = TermsOfService.objects.first()
        if not terms:
            terms = TermsOfService(content="Terms of service content will be updated by admin.")
            terms.save()
        
        return JsonResponse({
            "success": True,
            "content": terms.content,
            "updated_at": terms.updated_at.isoformat() if terms.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_terms_of_service(request):
    """Update terms of service content (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        content = body.get("content", "")
        
        if not content:
            return JsonResponse({"success": False, "error": "Content is required"}, status=400)
        
        terms = TermsOfService.objects.first()
        if not terms:
            terms = TermsOfService()
        
        terms.content = content
        terms.updated_at = datetime.utcnow()
        terms.save()
        
        return JsonResponse({"success": True, "message": "Terms of service updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
