"""
Utility functions for email templates
"""
from .models import EmailTemplate
from django.conf import settings
import re

def get_email_template(template_name, context=None):
    """
    Get email template by name and replace variables with context values.
    
    Args:
        template_name: Name of the template (e.g., "Enrollment Confirmation", "Password Reset Confirmation")
        context: Dictionary of variables to replace in template (e.g., {"name": "John", "email": "john@example.com"})
    
    Returns:
        tuple: (subject, html_body, plain_body) or None if template not found
    
    Available variables for different templates:
    - Enrollment Confirmation: name, email, category_name, enrolled_date, expiry_date
    - Password Reset Confirmation: name, email, reset_time
    """
    try:
        # Normalize template name (trim whitespace, lowercase for comparison)
        normalized_search_name = template_name.strip().lower()
        
        # Try exact match first (case-sensitive)
        template = EmailTemplate.objects(name=template_name, is_active=True).first()
        
        # If not found, try case-insensitive search with trimmed names
        if not template:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                if normalized_template_name == normalized_search_name:
                    template = t
                    print(f"✓ Found template with case-insensitive match: '{t.name}'")
                    break
        
        # If still not found, try partial match (contains the search name)
        # BUT: Exclude password reset templates when searching for coupon-related templates
        if not template:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                
                # Skip password reset templates when searching for coupon-related templates
                is_password_reset_template = (
                    "password" in normalized_template_name and 
                    ("reset" in normalized_template_name or "success" in normalized_template_name or "confirm" in normalized_template_name)
                )
                is_coupon_search = ("coupon" in normalized_search_name or "discount" in normalized_search_name)
                
                if is_coupon_search and is_password_reset_template:
                    continue  # Skip password reset templates when searching for coupons
                
                # Check if template name contains the search name or vice versa
                # Only match if search term is at least 3 characters (to avoid false matches)
                if len(normalized_search_name) >= 3:
                    if normalized_search_name in normalized_template_name or normalized_template_name in normalized_search_name:
                        template = t
                        print(f"✓ Found template with partial match: '{t.name}' (searched for '{template_name}')")
                        break
        
        # If still not found, try common variations
        if not template:
            # Common variations for "Password Reset Confirmation"
            variations = [
                "Password Reset Confirmation",
                "Password Reset Successful",  # Common alternative name
                "Password Reset",
                "Reset Password Confirmation",
                "Reset Password Successful",
                "Password Reset Email",
                "Reset Confirmation",
                "Password Reset Success"
            ]
            all_templates = EmailTemplate.objects(is_active=True)
            for variation in variations:
                for t in all_templates:
                    normalized_template_name = t.name.strip().lower() if t.name else ""
                    if normalized_template_name == variation.lower():
                        template = t
                        print(f"✓ Found template with variation match: '{t.name}' (searched for '{template_name}')")
                        break
                if template:
                    break
        
        # If still not found and searching for "Password Reset Confirmation", try matching any template with "password reset" and "success" or "confirm"
        if not template and "password reset" in normalized_search_name:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                # Match templates that contain both "password reset" and either "success" or "confirm" or "successful"
                if "password reset" in normalized_template_name and ("success" in normalized_template_name or "confirm" in normalized_template_name or "successful" in normalized_template_name):
                    template = t
                    print(f"✓ Found template with keyword match: '{t.name}' (searched for '{template_name}')")
                    break
        
        # If still not found and searching for coupon-related templates, try matching any template with "coupon" keyword
        # IMPORTANT: Explicitly exclude password reset templates
        if not template and ("coupon" in normalized_search_name or "discount" in normalized_search_name or "assignment" in normalized_search_name or "notification" in normalized_search_name):
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                
                # EXCLUDE password reset templates - never match them for coupon searches
                is_password_reset_template = (
                    "password" in normalized_template_name and 
                    ("reset" in normalized_template_name or "success" in normalized_template_name or "confirm" in normalized_template_name or "successful" in normalized_template_name)
                )
                if is_password_reset_template:
                    continue  # Skip password reset templates
                
                # Match templates that contain "coupon", "discount", or combination of "assignment"/"notification" with "coupon"
                is_coupon_related = (
                    "coupon" in normalized_template_name or 
                    "discount" in normalized_template_name or
                    ("assignment" in normalized_template_name and "coupon" in normalized_template_name) or
                    ("notification" in normalized_template_name and "coupon" in normalized_template_name)
                )
                if is_coupon_related:
                    template = t
                    print(f"✓ Found template with coupon keyword match: '{t.name}' (searched for '{template_name}')")
                    break
        
        # If still not found and searching for enrollment-related templates, try matching any template with "enrollment" keyword
        # IMPORTANT: Explicitly exclude password reset and coupon templates
        if not template and ("enrollment" in normalized_search_name or "enrol" in normalized_search_name or ("course" in normalized_search_name and ("confirm" in normalized_search_name or "success" in normalized_search_name))):
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                
                # EXCLUDE password reset and coupon templates - never match them for enrollment searches
                is_password_reset_template = (
                    "password" in normalized_template_name and 
                    ("reset" in normalized_template_name or "success" in normalized_template_name or "confirm" in normalized_template_name or "successful" in normalized_template_name)
                )
                is_coupon_template = ("coupon" in normalized_template_name or "discount" in normalized_template_name)
                if is_password_reset_template or is_coupon_template:
                    continue  # Skip non-enrollment templates
                
                # Match templates that contain "enrollment", "enrol", or "course" with "confirm"/"success"
                is_enrollment_related = (
                    "enrollment" in normalized_template_name or 
                    "enrol" in normalized_template_name or
                    ("course" in normalized_template_name and ("confirm" in normalized_template_name or "success" in normalized_template_name))
                )
                if is_enrollment_related:
                    template = t
                    print(f"✓ Found template with enrollment keyword match: '{t.name}' (searched for '{template_name}')")
                    break
        
        if not template:
            # Debug: List all active templates to help troubleshoot
            all_active = EmailTemplate.objects(is_active=True)
            template_names = [t.name for t in all_active] if all_active else []
            print(f"⚠️ Email template '{template_name}' not found or not active.")
            print(f"   Available active templates: {template_names}")
            print(f"   Searched for (normalized): '{normalized_search_name}'")
            return None
        
        print(f"✓ Found email template: '{template.name}'")
        
        subject = template.subject
        body = template.body
        
        # Replace variables in subject and body if context provided
        if context:
            for key, value in context.items():
                # Support both {{key}} and {{{key}}} formats
                patterns = [
                    f"{{{{{key}}}}}",  # {{key}}
                    f"{{{key}}}",      # {key}
                    f"[[{key}]]",      # [[key]]
                ]
                for pattern in patterns:
                    subject = subject.replace(pattern, str(value))
                    body = body.replace(pattern, str(value))
            
            print(f"✓ Replaced variables in template: {list(context.keys())}")
        
        # Ensure HTML body has proper structure for email clients
        html_body = body.strip()
        
        # Check if body already has complete HTML document structure
        html_lower = html_body.lower()
        has_complete_html = (
            ('<!doctype' in html_lower or '<html' in html_lower) and 
            '</html>' in html_lower and
            '<head' in html_lower and
            '<body' in html_lower
        )
        
        # If body doesn't have complete HTML structure, wrap it properly
        if not has_complete_html:
            # Check if body contains HTML tags (fragment)
            has_html_tags = bool(re.search(r'<[^>]+>', html_body))
            
            if has_html_tags:
                # HTML fragment - wrap in proper email structure while preserving admin's formatting
                html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px;">
        {html_body}
    </div>
</body>
</html>"""
            else:
                # Plain text content, convert to HTML with proper formatting
                html_body = html_body.replace('\n', '<br>')
                html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 20px;">
        {html_body}
    </div>
</body>
</html>"""
        
        # Create plain text version (better HTML stripping)
        plain_body = body
        # Replace common HTML line breaks
        plain_body = plain_body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
        plain_body = plain_body.replace("</p>", "\n\n").replace("<p>", "")
        plain_body = plain_body.replace("</div>", "\n").replace("<div>", "")
        # Remove other HTML tags
        plain_body = re.sub(r'<[^>]+>', '', plain_body)
        # Clean up extra whitespace
        plain_body = re.sub(r'\n\s*\n\s*\n', '\n\n', plain_body)
        plain_body = plain_body.strip()
        
        print(f"✓ Email template processed successfully")
        return (subject, html_body, plain_body)
    except Exception as e:
        print(f"✗ Error getting email template {template_name}: {e}")
        import traceback
        print(traceback.format_exc())
        return None

