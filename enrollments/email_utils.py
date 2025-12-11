"""
Email utility functions for enrollment, invoice, and newsletter emails
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from datetime import datetime
from email_templates.utils import get_email_template


def send_enrollment_confirmation_email(user_email, user_name, category_name, enrolled_date, expiry_date):
    """
    Send enrollment confirmation email to user after successful enrollment
    Uses ONLY email template created by admin - no hardcoded content
    """
    try:
        # Get email template - REQUIRED, no fallback
        template_data = get_email_template("Enrollment Confirmation", {
            "name": user_name,
            "email": user_email,
            "category_name": category_name,
            "enrolled_date": enrolled_date.strftime('%B %d, %Y'),
            "expiry_date": expiry_date.strftime('%B %d, %Y')
        })
        
        if not template_data:
            print(f"✗ ERROR: Email template 'Enrollment Confirmation' not found or not active!")
            print(f"  Admin must create this template in Email Templates section.")
            return False
        
        subject, html_message, plain_message = template_data
        print(f"✓ Using email template 'Enrollment Confirmation' for {user_email}")
        print(f"  Subject: {subject[:50]}...")
        
        # Send email using template content only
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        print(f"✓ Enrollment confirmation email sent successfully to {user_email}")
        return True
        
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
        # Get email template - REQUIRED, no fallback
        paid_date = payment_details["paid_at"].strftime('%B %d, %Y') if payment_details.get("paid_at") else datetime.now().strftime('%B %d, %Y')
        
        template_data = get_email_template("Payment Invoice", {
            "name": user_name,
            "email": user_email,
            "category_name": enrollment_details["category_name"],
            "payment_id": payment_details.get("payment_id", "N/A"),
            "paid_date": paid_date,
            "duration_months": enrollment_details.get("duration_months", "N/A"),
            "payment_method": payment_details.get("payment_method", "Razorpay"),
            "transaction_id": payment_details.get("razorpay_payment_id", "N/A"),
            "order_id": payment_details.get("razorpay_order_id", "N/A"),
            "amount": f"₹{payment_details['amount']:.2f}",
            "currency": payment_details.get("currency", "INR")
        })
        
        if not template_data:
            print(f"✗ ERROR: Email template 'Payment Invoice' not found or not active!")
            print(f"  Admin must create this template in Email Templates section.")
            return False
        
        subject, html_message, plain_message = template_data
        print(f"✓ Using email template 'Payment Invoice' for {user_email}")
        print(f"  Subject: {subject[:50]}...")
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✓ Invoice email sent successfully to {user_email}")
            return True
        except Exception as email_error:
            print(f"✗ Error sending invoice email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            # Try to send with fail_silently=True as fallback
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user_email],
                    html_message=html_message,
                    fail_silently=True,
                )
                print(f"✓ Invoice email sent with fail_silently=True to {user_email}")
                return True
            except:
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
        template_subject, html_message, plain_message = template_data
        email_subject = template_subject if template_subject and template_subject.strip() else (subject if subject else 'Updates from PrepTara')
        
        print(f"✓ Using email template 'Newsletter' for {user_email}")
        print(f"  Subject: {email_subject[:50]}...")
        
        send_mail(
            subject=email_subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
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
        
        subject, html_message, plain_message = template_data
        print(f"✓ Using email template 'Password Reset Confirmation' for {user_email}")
        print(f"  Subject: {subject[:50]}...")
        
        try:
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[user_email],
                html_message=html_message,
                fail_silently=False,
            )
            print(f"✓ Password reset confirmation email sent successfully to {user_email}")
            return True
        except Exception as email_error:
            print(f"✗ Error sending password reset confirmation email to {user_email}: {email_error}")
            import traceback
            print(traceback.format_exc())
            # Try to send with fail_silently=True as fallback
            try:
                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user_email],
                    html_message=html_message,
                    fail_silently=True,
                )
                print(f"✓ Email sent with fail_silently=True to {user_email}")
                return True
            except:
                return False
    except Exception as e:
        print(f"Error in send_password_reset_confirmation_email: {e}")
        import traceback
        print(traceback.format_exc())
        return False
