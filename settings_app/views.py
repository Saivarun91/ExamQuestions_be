import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from common.middleware import authenticate, restrict
from .models import AdminSettings, PrivacyPolicy, TermsOfService, RefundCancellationPolicy, Disclaimer, ContactUs, Sitemap, SitemapURL

@csrf_exempt
def get_public_settings(request):
    """Get public site settings (site name only, no authentication required)."""
    try:
        settings_obj = AdminSettings.objects.first()
        if not settings_obj:
            settings_obj = AdminSettings()
            settings_obj.save()

        # Get contact details from ContactUs model (preferred) or fallback to AdminSettings
        contact_obj = ContactUs.objects.first()
        contact_email = ""
        contact_phone = ""
        contact_address = ""
        contact_website = ""
        
        if contact_obj:
            contact_email = getattr(contact_obj, 'contact_email', '') or ''
            contact_phone = getattr(contact_obj, 'contact_phone', '') or ''
            contact_address = getattr(contact_obj, 'contact_address', '') or ''
            contact_website = getattr(contact_obj, 'contact_website', '') or ''
        else:
            # Fallback to AdminSettings for backward compatibility
            contact_email = getattr(settings_obj, 'contact_email', '') or ''
            contact_phone = getattr(settings_obj, 'contact_phone', '') or ''
            contact_address = getattr(settings_obj, 'contact_address', '') or ''
            contact_website = getattr(settings_obj, 'contact_website', '') or ''

        return JsonResponse({
            "success": True, 
            "site_name": getattr(settings_obj, 'site_name', '') or '',
            "logo_url": getattr(settings_obj, 'logo_url', '') or '',
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "contact_address": contact_address,
            "contact_website": contact_website,
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
            "logo_url": getattr(settings_obj, 'logo_url', '') or '',
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
        if "logo_url" in body:
            settings_obj.logo_url = body.get("logo_url", "")
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
            "meta_title": getattr(policy, 'meta_title', '') or '',
            "meta_keywords": getattr(policy, 'meta_keywords', '') or '',
            "meta_description": getattr(policy, 'meta_description', '') or '',
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
        policy.meta_title = body.get("meta_title", policy.meta_title or "")
        policy.meta_keywords = body.get("meta_keywords", policy.meta_keywords or "")
        policy.meta_description = body.get("meta_description", policy.meta_description or "")
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
        terms.meta_title = body.get("meta_title", terms.meta_title or "")
        terms.meta_keywords = body.get("meta_keywords", terms.meta_keywords or "")
        terms.meta_description = body.get("meta_description", terms.meta_description or "")
        terms.updated_at = datetime.utcnow()
        terms.save()
        
        return JsonResponse({"success": True, "message": "Terms of service updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= REFUND & CANCELLATION POLICY =================
@csrf_exempt
def get_refund_cancellation_policy(request):
    """Get refund & cancellation policy content (public endpoint)."""
    try:
        policy = RefundCancellationPolicy.objects.first()
        if not policy:
            policy = RefundCancellationPolicy(content="Refund & cancellation policy content will be updated by admin.")
            policy.save()
        
        return JsonResponse({
            "success": True,
            "content": policy.content,
            "meta_title": getattr(policy, 'meta_title', '') or '',
            "meta_keywords": getattr(policy, 'meta_keywords', '') or '',
            "meta_description": getattr(policy, 'meta_description', '') or '',
            "updated_at": policy.updated_at.isoformat() if policy.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_refund_cancellation_policy(request):
    """Update refund & cancellation policy content (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        content = body.get("content", "")
        
        if not content:
            return JsonResponse({"success": False, "error": "Content is required"}, status=400)
        
        policy = RefundCancellationPolicy.objects.first()
        if not policy:
            policy = RefundCancellationPolicy()
        
        policy.content = content
        policy.meta_title = body.get("meta_title", policy.meta_title or "")
        policy.meta_keywords = body.get("meta_keywords", policy.meta_keywords or "")
        policy.meta_description = body.get("meta_description", policy.meta_description or "")
        policy.updated_at = datetime.utcnow()
        policy.save()
        
        return JsonResponse({"success": True, "message": "Refund & cancellation policy updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= DISCLAIMER =================
@csrf_exempt
def get_disclaimer(request):
    """Get disclaimer content (public endpoint)."""
    try:
        disclaimer = Disclaimer.objects.first()
        if not disclaimer:
            disclaimer = Disclaimer(content="Disclaimer content will be updated by admin.")
            disclaimer.save()
        
        return JsonResponse({
            "success": True,
            "content": disclaimer.content,
            "updated_at": disclaimer.updated_at.isoformat() if disclaimer.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_disclaimer(request):
    """Update disclaimer content (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        content = body.get("content", "")
        
        if not content:
            return JsonResponse({"success": False, "error": "Content is required"}, status=400)
        
        disclaimer = Disclaimer.objects.first()
        if not disclaimer:
            disclaimer = Disclaimer()
        
        disclaimer.content = content
        disclaimer.meta_title = body.get("meta_title", disclaimer.meta_title or "")
        disclaimer.meta_keywords = body.get("meta_keywords", disclaimer.meta_keywords or "")
        disclaimer.meta_description = body.get("meta_description", disclaimer.meta_description or "")
        disclaimer.updated_at = datetime.utcnow()
        disclaimer.save()
        
        return JsonResponse({"success": True, "message": "Disclaimer updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= CONTACT US =================
@csrf_exempt
def get_contact_us(request):
    """Get contact us details (public endpoint)."""
    try:
        contact = ContactUs.objects.first()
        if not contact:
            contact = ContactUs()
            contact.save()
        
        return JsonResponse({
            "success": True,
            "contact_email": getattr(contact, 'contact_email', '') or '',
            "contact_phone": getattr(contact, 'contact_phone', '') or '',
            "contact_address": getattr(contact, 'contact_address', '') or '',
            "contact_website": getattr(contact, 'contact_website', '') or '',
            "meta_title": getattr(contact, 'meta_title', '') or '',
            "meta_keywords": getattr(contact, 'meta_keywords', '') or '',
            "meta_description": getattr(contact, 'meta_description', '') or '',
            "updated_at": contact.updated_at.isoformat() if contact.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_contact_us(request):
    """Update contact us details (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        
        contact = ContactUs.objects.first()
        if not contact:
            contact = ContactUs()
        
        contact.contact_email = body.get("contact_email", contact.contact_email or "")
        contact.contact_phone = body.get("contact_phone", contact.contact_phone or "")
        contact.contact_address = body.get("contact_address", contact.contact_address or "")
        contact.contact_website = body.get("contact_website", contact.contact_website or "")
        contact.meta_title = body.get("meta_title", contact.meta_title or "")
        contact.meta_keywords = body.get("meta_keywords", contact.meta_keywords or "")
        contact.meta_description = body.get("meta_description", contact.meta_description or "")
        contact.updated_at = datetime.utcnow()
        contact.save()
        
        return JsonResponse({"success": True, "message": "Contact us details updated successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ================= SITEMAP =================
@csrf_exempt
@authenticate
@restrict(['admin'])
def get_sitemap(request):
    """Get all sitemap URLs (admin only)."""
    try:
        sitemap = Sitemap.objects.first()
        if not sitemap:
            sitemap = Sitemap()
            sitemap.save()
        
        urls = []
        for url_obj in sitemap.urls:
            urls.append({
                "url": url_obj.url,
                "priority": url_obj.priority,
                "changefreq": url_obj.changefreq,
                "lastmod": url_obj.lastmod.isoformat() if url_obj.lastmod else None
            })
        
        return JsonResponse({
            "success": True,
            "urls": urls,
            "updated_at": sitemap.updated_at.isoformat() if sitemap.updated_at else None
        }, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def add_sitemap_url(request):
    """Add a new URL to sitemap (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        url = body.get("url", "").strip()
        priority = float(body.get("priority", 0.5))
        changefreq = body.get("changefreq", "monthly")
        
        if not url:
            return JsonResponse({"success": False, "error": "URL is required"}, status=400)
        
        # Validate URL format
        if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("/"):
            return JsonResponse({"success": False, "error": "Invalid URL format"}, status=400)
        
        # Validate priority
        priority = max(0.0, min(1.0, priority))
        
        # Validate changefreq
        valid_changefreqs = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
        if changefreq not in valid_changefreqs:
            changefreq = "monthly"
        
        sitemap = Sitemap.objects.first()
        if not sitemap:
            sitemap = Sitemap()
        
        # Check if URL already exists
        for existing_url in sitemap.urls:
            if existing_url.url == url:
                return JsonResponse({"success": False, "error": "URL already exists in sitemap"}, status=400)
        
        # Add new URL
        new_url = SitemapURL(
            url=url,
            priority=priority,
            changefreq=changefreq,
            lastmod=datetime.utcnow()
        )
        sitemap.urls.append(new_url)
        sitemap.updated_at = datetime.utcnow()
        sitemap.save()
        
        return JsonResponse({"success": True, "message": "URL added to sitemap successfully"}, status=200)
    except ValueError as e:
        return JsonResponse({"success": False, "error": f"Invalid value: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def update_sitemap_url(request):
    """Update an existing sitemap URL (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        old_url = body.get("old_url", "").strip()
        new_url = body.get("url", "").strip()
        priority = body.get("priority")
        changefreq = body.get("changefreq")
        
        if not old_url:
            return JsonResponse({"success": False, "error": "Old URL is required"}, status=400)
        
        if not new_url:
            return JsonResponse({"success": False, "error": "New URL is required"}, status=400)
        
        # Validate URL format
        if not new_url.startswith("http://") and not new_url.startswith("https://") and not new_url.startswith("/"):
            return JsonResponse({"success": False, "error": "Invalid URL format"}, status=400)
        
        sitemap = Sitemap.objects.first()
        if not sitemap:
            return JsonResponse({"success": False, "error": "Sitemap not found"}, status=404)
        
        # Find and update URL
        url_found = False
        for url_obj in sitemap.urls:
            if url_obj.url == old_url:
                url_obj.url = new_url
                if priority is not None:
                    url_obj.priority = max(0.0, min(1.0, float(priority)))
                if changefreq is not None:
                    valid_changefreqs = ["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"]
                    if changefreq in valid_changefreqs:
                        url_obj.changefreq = changefreq
                url_obj.lastmod = datetime.utcnow()
                url_found = True
                break
        
        if not url_found:
            return JsonResponse({"success": False, "error": "URL not found in sitemap"}, status=404)
        
        sitemap.updated_at = datetime.utcnow()
        sitemap.save()
        
        return JsonResponse({"success": True, "message": "URL updated successfully"}, status=200)
    except ValueError as e:
        return JsonResponse({"success": False, "error": f"Invalid value: {str(e)}"}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def delete_sitemap_url(request):
    """Delete a URL from sitemap (admin only)."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        body = json.loads(request.body.decode("utf-8"))
        url = body.get("url", "").strip()
        
        if not url:
            return JsonResponse({"success": False, "error": "URL is required"}, status=400)
        
        sitemap = Sitemap.objects.first()
        if not sitemap:
            return JsonResponse({"success": False, "error": "Sitemap not found"}, status=404)
        
        # Remove URL
        original_count = len(sitemap.urls)
        sitemap.urls = [url_obj for url_obj in sitemap.urls if url_obj.url != url]
        
        if len(sitemap.urls) == original_count:
            return JsonResponse({"success": False, "error": "URL not found in sitemap"}, status=404)
        
        sitemap.updated_at = datetime.utcnow()
        sitemap.save()
        
        return JsonResponse({"success": True, "message": "URL deleted from sitemap successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
