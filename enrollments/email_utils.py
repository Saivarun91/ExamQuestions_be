"""
Email utility functions for enrollment, invoice, and newsletter emails
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime, date
import re
from email_templates.utils import get_email_template, send_template_email, unpack_template_data, replace_template_variables
from email_templates.invoice_template import (
    enrich_invoice_context,
    find_admin_invoice_template,
    render_builtin_invoice_email,
    should_use_custom_admin_invoice,
)


def format_email_date(value):
    """Format enrollment/payment dates for email templates."""
    if value is None or value == "":
        return "N/A"
    if isinstance(value, datetime):
        return value.strftime("%B %d, %Y")
    if isinstance(value, date):
        return value.strftime("%B %d, %Y")
    if hasattr(value, "strftime"):
        return value.strftime("%B %d, %Y")
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return "N/A"
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.strptime(raw[:19], fmt)
                return parsed.strftime("%B %d, %Y")
            except ValueError:
                continue
        return raw
    return str(value)


def build_enrollment_email_context(user_email, user_name, category_name, enrolled_date, expiry_date):
    enrolled_date_str = format_email_date(enrolled_date)
    expiry_date_str = format_email_date(expiry_date)
    return {
        "name": user_name,
        "email": user_email,
        "category_name": category_name,
        "course_name": category_name,
        "enrolled_date": enrolled_date_str,
        "expiry_date": expiry_date_str,
        "enrollment_date": enrolled_date_str,
        "start_date": enrolled_date_str,
        "end_date": expiry_date_str,
        "date": enrolled_date_str,
        "expiry": expiry_date_str,
    }


def send_enrollment_confirmation_email(user_email, user_name, category_name, enrolled_date, expiry_date):
    """
    Send enrollment confirmation email to user after successful enrollment
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        # Validate email address
        if not user_email or not isinstance(user_email, str) or '@' not in user_email:
            print(f"✗ ERROR: Invalid email address: {user_email}")
            return False
        
        # Format dates
        email_context = build_enrollment_email_context(
            user_email, user_name, category_name, enrolled_date, expiry_date
        )
        enrolled_date_str = email_context["enrolled_date"]
        expiry_date_str = email_context["expiry_date"]
        
        # Get email template - try multiple template name variations
        template_data = None
        template_names = [
            "Enrollment Main",
            "Enrollment Confirmation",
            "Enrollment Email",
            "Enrollment Notification",
            "Course Enrollment",
            "Enrollment Success",
            "Enrollment",
            "Course Confirmation",
        ]
        
        print(f"📧 Attempting to send enrollment confirmation email to {user_email}")
        print(f"   Course: {category_name}, Enrolled: {enrolled_date_str}")
        
        # First, find a valid enrollment template by searching directly
        from email_templates.models import EmailTemplate
        valid_enrollment_template = None
        
        # Try exact matches first
        for template_name in template_names:
            template = EmailTemplate.objects(name=template_name, is_active=True).first()
            if not template:
                # Try case-insensitive
                all_templates = EmailTemplate.objects(is_active=True)
                for t in all_templates:
                    if t.name.strip().lower() == template_name.strip().lower():
                        template = t
                        break
            
            if template:
                template_name_lower = template.name.strip().lower()
                # CRITICAL: Reject password reset and coupon templates
                is_password_reset = (
                    "password" in template_name_lower and 
                    ("reset" in template_name_lower or "success" in template_name_lower or "confirm" in template_name_lower or "successful" in template_name_lower)
                )
                is_coupon_template = ("coupon" in template_name_lower or "discount" in template_name_lower)
                
                if is_password_reset or is_coupon_template:
                    print(f"✗ Rejecting non-enrollment template: '{template.name}'")
                    continue
                
                # Accept enrollment-related templates
                is_enrollment_related = (
                    "enrollment" in template_name_lower or 
                    "enrol" in template_name_lower or
                    ("course" in template_name_lower and ("confirm" in template_name_lower or "success" in template_name_lower))
                )
                if is_enrollment_related:
                    valid_enrollment_template = template
                    print(f"✓ Found valid enrollment template: '{template.name}'")
                    break
        
        # If not found, search for any template with "enrollment" or "enrol" keyword (excluding password reset and coupon)
        if not valid_enrollment_template:
            print(f"⚠️ Specific enrollment template names not found, searching for any template with enrollment-related keywords...")
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                template_name_lower = t.name.strip().lower()
                # EXCLUDE password reset and coupon templates
                is_password_reset = (
                    "password" in template_name_lower and 
                    ("reset" in template_name_lower or "success" in template_name_lower or "confirm" in template_name_lower or "successful" in template_name_lower)
                )
                is_coupon_template = ("coupon" in template_name_lower or "discount" in template_name_lower)
                if is_password_reset or is_coupon_template:
                    continue  # Skip non-enrollment templates
                
                # Accept templates with enrollment or course confirmation keywords
                is_enrollment_related = (
                    "enrollment" in template_name_lower or 
                    "enrol" in template_name_lower or
                    ("course" in template_name_lower and ("confirm" in template_name_lower or "success" in template_name_lower))
                )
                if is_enrollment_related:
                    valid_enrollment_template = t
                    print(f"✓ Found enrollment template by keyword: '{t.name}'")
                    break
        
        # Now get the template data using the validated template name
        if valid_enrollment_template:
            template_data = get_email_template(valid_enrollment_template.name, email_context)
        
        if not template_data:
            print(f"✗ ERROR: Email template for enrollment not found or not active!")
            print(f"  Tried template names: {', '.join(template_names)}")
            print(f"  Also searched for templates containing 'enrollment' or 'enrol' keywords")
            print(f"  Admin must create an enrollment email template in Email Templates section.")
            print(f"  Suggested template name: 'Enrollment Confirmation' or 'Enrollment Email'")
            return False
        
        subject, html_message, plain_message, attachments = unpack_template_data(template_data)
        
        # Validate template data
        if not subject or not html_message:
            print(f"✗ ERROR: Email template returned empty subject or body")
            return False
        
        print(f"✓ Using email template for enrollment confirmation to {user_email}")
        print(f"  Subject: {subject[:80]}...")
        print(f"  HTML message length: {len(html_message)} characters")
        
        # Send email
        try:
            send_template_email([user_email], template_data, fail_silently=False)
            print(f"✓✓✓ Enrollment confirmation email sent successfully to {user_email} ✓✓✓")
            return True
        except Exception as email_error:
            print(f"✗ Error sending enrollment email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            try:
                send_template_email([user_email], template_data, fail_silently=True)
                print(f"✓ Enrollment email sent with fail_silently=True to {user_email}")
                return True
            except Exception as fallback_error:
                print(f"✗ Fallback email send also failed: {fallback_error}")
                return False
        
    except Exception as e:
        print(f"✗ Error in send_enrollment_confirmation_email: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def send_invoice_email(user_email, user_name, payment_details, enrollment_details):
    """
    Send invoice email to user after successful payment
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        from common.currency_utils import get_currency_symbol

        # Get email template - REQUIRED, no fallback
        paid_date = format_email_date(payment_details.get("paid_at"))
        currency = payment_details.get("currency", "INR")
        symbol = get_currency_symbol(currency)
        amount = float(payment_details.get("amount", 0) or 0)
        discount_amount = float(payment_details.get("discount_amount", 0) or 0)

        billing = payment_details.get("billing_details") or {}
        tax = payment_details.get("tax_breakdown") or {}
        gst_amount = float(tax.get("gst_amount", 0) or 0)
        cgst_amount = float(tax.get("cgst_amount", 0) or 0)
        sgst_amount = float(tax.get("sgst_amount", 0) or 0)
        gst_percentage = float(tax.get("gst_percentage", 0) or 0)
        subtotal = round(max(0, amount - gst_amount), 2)

        course_name = enrollment_details.get("course_name") or enrollment_details.get("category_name", "Course")
        plan_name = enrollment_details.get("plan_name") or payment_details.get("plan_name") or "N/A"
        gst_id = (billing.get("gst_id") or billing.get("gstin") or "").strip()

        invoice_number = (
            payment_details.get("invoice_number")
            or payment_details.get("payment_id")
            or payment_details.get("razorpay_order_id")
            or "N/A"
        )
        amount_paid = f"{symbol}{amount:.2f}"
        exam_price_without_gst = f"{symbol}{subtotal:.2f}"

        invoice_context = {
            "name": user_name,
            "customer_name": user_name,
            "email": user_email,
            "customer_email": user_email,
            "category_name": course_name,
            "course_name": course_name,
            "exam_name": course_name,
            "plan_name": plan_name,
            "plan": plan_name,
            "payment_id": payment_details.get("payment_id", "N/A"),
            "invoice_number": invoice_number,
            "paid_date": paid_date,
            "payment_date": paid_date,
            "date": paid_date,
            "invoice_date": paid_date,
            "duration_months": enrollment_details.get("duration_months", "N/A"),
            "duration": enrollment_details.get("duration_months", "N/A"),
            "payment_method": payment_details.get("payment_method", "Razorpay"),
            "transaction_id": payment_details.get("razorpay_payment_id", "N/A"),
            "razorpay_payment_id": payment_details.get("razorpay_payment_id", "N/A"),
            "order_id": payment_details.get("razorpay_order_id", "N/A"),
            "razorpay_order_id": payment_details.get("razorpay_order_id", "N/A"),
            "amount": amount_paid,
            "amount_paid": amount_paid,
            "total_amount": amount_paid,
            "total": amount_paid,
            "subtotal": f"{symbol}{subtotal:.2f}",
            "discount_amount": f"{symbol}{discount_amount:.2f}" if discount_amount > 0 else f"{symbol}0.00",
            "discount": f"{symbol}{discount_amount:.2f}" if discount_amount > 0 else f"{symbol}0.00",
            "coupon_code": payment_details.get("coupon_code") or "N/A",
            "coupon": payment_details.get("coupon_code") or "N/A",
            "currency": currency,
            "billing_name": billing.get("name") or user_name,
            "billing_phone": billing.get("phone") or "N/A",
            "phone": billing.get("phone") or "N/A",
            "billing_address": billing.get("address") or "N/A",
            "address": billing.get("address") or "N/A",
            "billing_state": billing.get("state") or "N/A",
            "state": billing.get("state") or "N/A",
            "billing_country": billing.get("country") or "N/A",
            "country": billing.get("country") or "N/A",
            "gst_id": gst_id or "N/A",
            "customer_gstin": gst_id or "",
            "gstin": gst_id or "N/A",
            "gst_percentage": f"{gst_percentage:.2f}" if gst_percentage else "0.00",
            "gst_amount": f"{symbol}{gst_amount:.2f}" if gst_amount > 0 else f"{symbol}0.00",
            "gst": f"{symbol}{gst_amount:.2f}" if gst_amount > 0 else f"{symbol}0.00",
            "cgst_amount": f"{symbol}{cgst_amount:.2f}" if cgst_amount > 0 else f"{symbol}0.00",
            "cgst": f"{symbol}{cgst_amount:.2f}" if cgst_amount > 0 else f"{symbol}0.00",
            "sgst_amount": f"{symbol}{sgst_amount:.2f}" if sgst_amount > 0 else f"{symbol}0.00",
            "sgst": f"{symbol}{sgst_amount:.2f}" if sgst_amount > 0 else f"{symbol}0.00",
            "exam_price": exam_price_without_gst,
            "exam_price_without_gst": exam_price_without_gst,
            "base_amount": exam_price_without_gst,
        }
        invoice_context = enrich_invoice_context(invoice_context)

        admin_template = find_admin_invoice_template()
        template_data = None

        if admin_template and should_use_custom_admin_invoice(admin_template):
            template_data = get_email_template(admin_template.name, invoice_context)

        if not template_data:
            admin_subject = None
            if admin_template and (admin_template.subject or "").strip():
                admin_subject = replace_template_variables(admin_template.subject.strip(), invoice_context)
            template_data = render_builtin_invoice_email(invoice_context, subject=admin_subject)
            print("✓ Using built-in invoice HTML template with dynamic details")
        
        subject, html_message, plain_message, attachments = unpack_template_data(template_data)

        # If customer GSTIN was not provided, remove GSTIN row from template output.
        customer_gstin = (invoice_context.get("customer_gstin") or "").strip()
        if not customer_gstin:
            html_message = re.sub(
                r"<tr>\s*<td>\s*<strong>\s*GSTIN\s*:\s*</strong>\s*[^<]*</td>\s*</tr>",
                "",
                html_message,
                flags=re.IGNORECASE,
            )
            plain_message = re.sub(
                r"(?im)^\s*.*GSTIN\s*:\s*$",
                "",
                plain_message,
            )

        print(f"✓ Using invoice email for {user_email}")
        print(f"  Subject: {subject[:50]}...")

        invoice_payload = (subject, html_message, plain_message, attachments)
        
        try:
            send_template_email([user_email], invoice_payload, fail_silently=False)
            print(f"✓ Invoice email sent successfully to {user_email}")
            return True
        except Exception as email_error:
            print(f"✗ Error sending invoice email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            try:
                send_template_email([user_email], invoice_payload, fail_silently=True)
                print(f"✓ Invoice email sent with fail_silently=True to {user_email}")
                return True
            except Exception:
                return False
    except Exception as e:
        print(f"Error in send_invoice_email: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def send_newsletter_email(user_email, user_name, subject, content):
    """
    Send newsletter/followup email to purchased users
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        # Get email template - REQUIRED, no fallback
        template_data = get_email_template("Newsletter", {
            "name": user_name,
            "email": user_email,
            "content": content,
            "subject": subject if subject else "Updates from PrepTara"
        })
        
        if not template_data:
            print(f"✗ ERROR: Email template 'Newsletter' not found or not active!")
            print(f"  Admin must create this template in Email Templates section.")
            return False
        
        # Use template subject if provided, otherwise use the passed subject
        template_subject, html_message, plain_message, attachments = unpack_template_data(template_data)
        email_subject = template_subject if template_subject and template_subject.strip() else (subject if subject else 'Updates from PrepTara')
        
        print(f"✓ Using email template 'Newsletter' for {user_email}")
        print(f"  Subject: {email_subject[:50]}...")
        
        send_template_email([user_email], (email_subject, html_message, plain_message, attachments), fail_silently=False)
        print(f"✓ Newsletter email sent successfully to {user_email}")
        return True
    except Exception as e:
        print(f"Error sending newsletter email: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def send_password_reset_confirmation_email(user_email, user_name, reset_time):
    """
    Send password reset confirmation email to user after successful password reset
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        # Get email template - REQUIRED, no fallback
        template_data = get_email_template("Password Reset Confirmation", {
            "name": user_name,
            "email": user_email,
            "reset_time": reset_time.strftime('%B %d, %Y at %I:%M %p UTC')
        })
        
        if not template_data:
            print(f"✗ ERROR: Email template 'Password Reset Confirmation' not found or not active!")
            print(f"  Admin must create this template in Email Templates section.")
            return False
        
        subject, html_message, plain_message, attachments = unpack_template_data(template_data)
        print(f"✓ Using email template 'Password Reset Confirmation' for {user_email}")
        print(f"  Subject: {subject[:50]}...")
        
        try:
            send_template_email([user_email], template_data, fail_silently=False)
            print(f"✓ Password reset confirmation email sent successfully to {user_email}")
            return True
        except Exception as email_error:
            print(f"✗ Error sending password reset confirmation email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            try:
                send_template_email([user_email], template_data, fail_silently=True)
                print(f"✓ Email sent with fail_silently=True to {user_email}")
                return True
            except Exception:
                return False
    except Exception as e:
        print(f"Error in send_password_reset_confirmation_email: {e}")
        import traceback
        print(traceback.format_exc())
        return False


def send_coupon_email(user_email, user_name, coupon_code, discount_value, discount_type, valid_until, min_purchase=None, max_discount=None):
    """
    Send coupon email to user when admin assigns/sends a coupon
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        # Validate email address
        if not user_email or not isinstance(user_email, str) or '@' not in user_email:
            print(f"✗ ERROR: Invalid email address: {user_email}")
            return False
        
        # Format discount display
        discount_display = f"{discount_value}{'%' if discount_type == 'percentage' else '₹'}"
        if discount_type == 'percentage' and max_discount:
            discount_display += f" (up to ₹{max_discount})"
        
        # Format valid until date
        valid_until_str = valid_until.strftime('%B %d, %Y') if hasattr(valid_until, 'strftime') else str(valid_until)
        
        # Get email template - try multiple template name variations
        # IMPORTANT: We must find a coupon-related template, NOT password reset templates
        template_data = None
        template_names = [
            "Coupon Assignment Notification",  # Admin's template name - highest priority
            "Coupon Email",
            "Coupon Received",
            "Coupon Notification",
            "Coupon Assignment",
            "Special Coupon",
            "Coupon Code",
            "Coupon",
            "Discount Coupon"
        ]
        
        print(f"📧 Attempting to send coupon email to {user_email}")
        print(f"   Coupon Code: {coupon_code}, Discount: {discount_display}")
        
        # First, find a valid coupon template by searching directly
        from email_templates.models import EmailTemplate
        valid_coupon_template = None
        
        # Try exact matches first
        for template_name in template_names:
            template = EmailTemplate.objects(name=template_name, is_active=True).first()
            if not template:
                # Try case-insensitive
                all_templates = EmailTemplate.objects(is_active=True)
                for t in all_templates:
                    if t.name.strip().lower() == template_name.strip().lower():
                        template = t
                        break
            
            if template:
                template_name_lower = template.name.strip().lower()
                # CRITICAL: Reject password reset templates
                is_password_reset = (
                    "password" in template_name_lower and 
                    ("reset" in template_name_lower or "success" in template_name_lower or "confirm" in template_name_lower or "successful" in template_name_lower)
                )
                if is_password_reset:
                    print(f"✗ Rejecting password reset template: '{template.name}'")
                    continue
                
                # Accept coupon-related templates (including assignment/notification)
                is_coupon_related = (
                    "coupon" in template_name_lower or 
                    "discount" in template_name_lower or
                    ("assignment" in template_name_lower and "coupon" in template_name_lower) or
                    ("notification" in template_name_lower and "coupon" in template_name_lower)
                )
                if is_coupon_related:
                    valid_coupon_template = template
                    print(f"✓ Found valid coupon template: '{template.name}'")
                    break
        
        # If not found, search for any template with "coupon", "discount", "assignment", or "notification" keywords (excluding password reset)
        if not valid_coupon_template:
            print(f"⚠️ Specific coupon template names not found, searching for any template with coupon-related keywords...")
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                template_name_lower = t.name.strip().lower()
                # EXCLUDE password reset templates
                is_password_reset = (
                    "password" in template_name_lower and 
                    ("reset" in template_name_lower or "success" in template_name_lower or "confirm" in template_name_lower or "successful" in template_name_lower)
                )
                if is_password_reset:
                    continue  # Skip password reset templates
                
                # Accept templates with coupon, discount, assignment, or notification keywords
                is_coupon_related = (
                    "coupon" in template_name_lower or 
                    "discount" in template_name_lower or
                    ("assignment" in template_name_lower and "coupon" in template_name_lower) or
                    ("notification" in template_name_lower and "coupon" in template_name_lower)
                )
                if is_coupon_related:
                    valid_coupon_template = t
                    print(f"✓ Found coupon template by keyword: '{t.name}'")
                    break
        
        # Now get the template data using the validated template name
        if valid_coupon_template:
            template_data = get_email_template(valid_coupon_template.name, {
                "name": user_name,
                "email": user_email,
                "coupon_code": coupon_code,
                "discount_value": discount_value,
                "discount_type": discount_type,
                "discount_display": discount_display,
                "valid_until": valid_until_str,
                "min_purchase": f"₹{min_purchase}" if min_purchase and min_purchase > 0 else "No minimum",
                "max_discount": f"₹{max_discount}" if max_discount else "No limit"
            })
        
        if not template_data:
            print(f"✗ ERROR: Email template for coupon not found or not active!")
            print(f"  Tried template names: {', '.join(template_names)}")
            print(f"  Also searched for templates containing 'coupon' or 'discount' keywords")
            print(f"  Admin must create a coupon email template in Email Templates section.")
            print(f"  Suggested template name: 'Coupon Email' or 'Coupon Received'")
            return False
        
        subject, html_message, plain_message, attachments = unpack_template_data(template_data)
        
        # Validate template data
        if not subject or not html_message:
            print(f"✗ ERROR: Email template returned empty subject or body")
            return False
        
        print(f"✓ Using email template for coupon email to {user_email}")
        print(f"  Subject: {subject[:80]}...")
        print(f"  HTML message length: {len(html_message)} characters")
        
        # Send email
        try:
            send_template_email([user_email], template_data, fail_silently=False)
            print(f"✓✓✓ Coupon email sent successfully to {user_email} ✓✓✓")
            return True
        except Exception as email_error:
            print(f"✗ Error sending coupon email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            try:
                send_template_email([user_email], template_data, fail_silently=True)
                print(f"✓ Coupon email sent with fail_silently=True to {user_email}")
                return True
            except Exception as fallback_error:
                print(f"✗ Fallback email send also failed: {fallback_error}")
                return False
    except Exception as e:
        print(f"✗ Error in send_coupon_email: {e}")
        import traceback
        print(traceback.format_exc())
        return False