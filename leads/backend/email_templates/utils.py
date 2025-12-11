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
        # Try exact match first
        template = EmailTemplate.objects(name=template_name, is_active=True).first()
        
        # If not found, try case-insensitive search
        if not template:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                if t.name.lower() == template_name.lower():
                    template = t
                    break
        
        if not template:
            print(f"⚠️ Email template '{template_name}' not found or not active. Using default template.")
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
        return (subject, body, plain_body)
    except Exception as e:
        print(f"✗ Error getting email template {template_name}: {e}")
        import traceback
        print(traceback.format_exc())
        return None

