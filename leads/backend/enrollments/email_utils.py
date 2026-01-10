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
    """
    try:
        subject = f'Payment Invoice - {enrollment_details["category_name"]} | PrepTara'
        
        # Create HTML email content
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #059669; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .invoice-box {{ background-color: white; padding: 20px; margin: 15px 0; border-radius: 4px; border: 1px solid #e5e7eb; }}
                .invoice-header {{ border-bottom: 2px solid #e5e7eb; padding-bottom: 15px; margin-bottom: 15px; }}
                .invoice-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #f3f4f6; }}
                .invoice-row.total {{ border-top: 2px solid #059669; border-bottom: none; font-weight: bold; font-size: 18px; margin-top: 10px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>💰 Payment Invoice</h1>
                </div>
                <div class="content">
                    <p>Dear {user_name},</p>
                    <p>Thank you for your payment! Your invoice for <strong>{enrollment_details["category_name"]}</strong> is attached below.</p>
                    
                    <div class="invoice-box">
                        <div class="invoice-header">
                            <h2>Invoice Details</h2>
                            <p><strong>Invoice #:</strong> {payment_details["payment_id"]}</p>
                            <p><strong>Date:</strong> {payment_details["paid_at"].strftime('%B %d, %Y') if payment_details.get("paid_at") else datetime.now().strftime('%B %d, %Y')}</p>
                        </div>
                        
                        <div class="invoice-row">
                            <span>Course:</span>
                            <span>{enrollment_details["category_name"]}</span>
                        </div>
                        <div class="invoice-row">
                            <span>Duration:</span>
                            <span>{enrollment_details["duration_months"]} months</span>
                        </div>
                        <div class="invoice-row">
                            <span>Payment Method:</span>
                            <span>{payment_details.get("payment_method", "Razorpay")}</span>
                        </div>
                        <div class="invoice-row">
                            <span>Transaction ID:</span>
                            <span>{payment_details.get("razorpay_payment_id", "N/A")}</span>
                        </div>
                        <div class="invoice-row">
                            <span>Order ID:</span>
                            <span>{payment_details.get("razorpay_order_id", "N/A")}</span>
                        </div>
                        <div class="invoice-row total">
                            <span>Total Amount:</span>
                            <span>₹{payment_details["amount"]:.2f} {payment_details.get("currency", "INR")}</span>
                        </div>
                    </div>
                    
                    <p>Your enrollment is now active. You can access all course materials and resources.</p>
                    
                    <p>If you have any questions about this invoice, please contact our support team.</p>
                    
                    <p>Best regards,<br>The PrepTara Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                    <p>&copy; {datetime.now().year} PrepTara. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        plain_message = f"""
        Dear {user_name},
        
        Thank you for your payment! Your invoice for {enrollment_details["category_name"]} is below.
        
        Invoice Details:
        Invoice #: {payment_details["payment_id"]}
        Date: {payment_details["paid_at"].strftime('%B %d, %Y') if payment_details.get("paid_at") else datetime.now().strftime('%B %d, %Y')}
        
        Course: {enrollment_details["category_name"]}
        Duration: {enrollment_details["duration_months"]} months
        Payment Method: {payment_details.get("payment_method", "Razorpay")}
        Transaction ID: {payment_details.get("razorpay_payment_id", "N/A")}
        Order ID: {payment_details.get("razorpay_order_id", "N/A")}
        
        Total Amount: ₹{payment_details["amount"]:.2f} {payment_details.get("currency", "INR")}
        
        Your enrollment is now active.
        
        Best regards,
        The PrepTara Team
        """
        
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
    """
    try:
        email_subject = subject if subject else 'Updates from PrepTara'
        
        # Create HTML email content
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #7c3aed; color: white; padding: 20px; text-align: center; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 30px; border-radius: 0 0 5px 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📬 PrepTara Newsletter</h1>
                </div>
                <div class="content">
                    <p>Dear {user_name},</p>
                    {content}
                    <p>Best regards,<br>The PrepTara Team</p>
                </div>
                <div class="footer">
                    <p>This is an automated email. Please do not reply to this message.</p>
                    <p>&copy; {datetime.now().year} PrepTara. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version (strip HTML tags)
        plain_message = strip_tags(content)
        plain_message = f"Dear {user_name},\n\n{plain_message}\n\nBest regards,\nThe PrepTara Team"
        
        send_mail(
            subject=email_subject,
            message=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending newsletter email: {e}")
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
