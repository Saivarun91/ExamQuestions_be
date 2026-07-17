"""Invoice context and HTML/PDF generation for payments."""
import base64
import tempfile
from io import BytesIO

from bson import ObjectId
from users.models import User
from .payment_models import Payment
from .models import Enrollment
from .email_utils import format_email_date
from common.currency_utils import get_currency_symbol


def _enrollment_display_name(course=None, category=None):
    if course:
        return getattr(course, "title", None) or getattr(course, "code", None) or "Course"
    if category:
        return getattr(category, "name", None) or "Course"
    return "Course"


def _resolve_user(user=None, payment=None):
    if user:
        return user
    if payment and payment.user_id:
        try:
            uid = payment.user_id
            if ObjectId.is_valid(str(uid)):
                return User.objects(id=ObjectId(uid)).first()
        except Exception:
            pass
    return None


def _resolve_enrollment(payment, enrollment=None):
    if enrollment:
        return enrollment
    if payment and getattr(payment, "enrollment_id", None):
        try:
            return payment.enrollment_id
        except Exception:
            pass
    try:
        return Enrollment.objects(payment=payment.id).first()
    except Exception:
        return None


def build_invoice_context(payment, enrollment=None, user=None):
    """Build template context dict for invoice HTML/email from a Payment record."""
    user = _resolve_user(user, payment)
    enrollment = _resolve_enrollment(payment, enrollment)

    course = None
    category = None
    if enrollment:
        try:
            course = getattr(enrollment, "course", None)
            if course:
                course = course
        except Exception:
            course = None
        try:
            category = getattr(enrollment, "category", None)
        except Exception:
            category = None

    course_name = _enrollment_display_name(course=course, category=category)
    billing = dict(getattr(payment, "billing_details", None) or {})
    tax = dict(getattr(payment, "tax_breakdown", None) or {})

    user_email = getattr(user, "email", "") if user else ""
    user_name = (
        billing.get("name")
        or (getattr(user, "fullname", None) if user else None)
        or "Student"
    )

    currency = getattr(payment, "currency", None) or "INR"
    symbol = get_currency_symbol(currency)
    amount = float(getattr(payment, "amount", 0) or 0)
    discount_amount = float(getattr(payment, "discount_amount", 0) or 0)
    gst_amount = float(tax.get("gst_amount", 0) or 0)
    gst_percentage = float(tax.get("gst_percentage", 0) or 0)
    subtotal = round(max(0, amount - gst_amount), 2)
    gst_id = (billing.get("gst_id") or billing.get("gstin") or "").strip()
    plan_name = getattr(payment, "plan_name", None) or "N/A"
    duration_months = getattr(enrollment, "duration_months", None) if enrollment else "N/A"

    paid_at = getattr(payment, "paid_at", None)
    paid_date = format_email_date(paid_at)
    invoice_number = (
        str(payment.id)
        if payment and payment.id
        else getattr(payment, "razorpay_order_id", None) or "N/A"
    )
    amount_paid = f"{symbol}{amount:.2f}"
    exam_price_without_gst = f"{symbol}{subtotal:.2f}"

    return {
        "name": user_name,
        "customer_name": user_name,
        "email": user_email,
        "customer_email": user_email,
        "category_name": course_name,
        "course_name": course_name,
        "exam_name": course_name,
        "plan_name": plan_name,
        "plan": plan_name,
        "payment_id": str(payment.id) if payment and payment.id else "N/A",
        "invoice_number": invoice_number,
        "paid_date": paid_date,
        "payment_date": paid_date,
        "date": paid_date,
        "invoice_date": paid_date,
        "duration_months": duration_months,
        "duration": duration_months,
        "payment_method": getattr(payment, "payment_method", None) or "Razorpay",
        "transaction_id": getattr(payment, "razorpay_payment_id", None) or "N/A",
        "razorpay_payment_id": getattr(payment, "razorpay_payment_id", None) or "N/A",
        "order_id": getattr(payment, "razorpay_order_id", None) or "N/A",
        "razorpay_order_id": getattr(payment, "razorpay_order_id", None) or "N/A",
        "amount": amount_paid,
        "amount_paid": amount_paid,
        "total_amount": amount_paid,
        "total": amount_paid,
        "subtotal": f"{symbol}{subtotal:.2f}",
        "discount_amount": f"{symbol}{discount_amount:.2f}" if discount_amount > 0 else f"{symbol}0.00",
        "discount": f"{symbol}{discount_amount:.2f}" if discount_amount > 0 else f"{symbol}0.00",
        "coupon_code": getattr(payment, "coupon_code", None) or "N/A",
        "coupon": getattr(payment, "coupon_code", None) or "N/A",
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
        "cgst_amount": f"{symbol}{float(tax.get('cgst_amount', 0) or 0):.2f}",
        "sgst_amount": f"{symbol}{float(tax.get('sgst_amount', 0) or 0):.2f}",
        "exam_price": exam_price_without_gst,
        "exam_price_without_gst": exam_price_without_gst,
        "base_amount": exam_price_without_gst,
    }


def get_invoice_html_for_payment(payment, enrollment=None, user=None):
    """Return rendered invoice HTML string for browser download."""
    from email_templates.invoice_template import render_builtin_invoice_download

    ctx = build_invoice_context(payment, enrollment=enrollment, user=user)
    return render_builtin_invoice_download(ctx)


def _prepare_invoice_html_for_pdf(html, *, for_xhtml2pdf=False):
    """Flatten invoice HTML for PDF so only the invoice card is printed cleanly."""
    # Portrait only — landscape @page previously swapped width/height and split
    # the invoice across multiple broken pages in Chromium/xhtml2pdf.
    if for_xhtml2pdf:
        page_css = """
      @page {
        size: A4 portrait;
        margin: 12mm;
      }
"""
    else:
        # Playwright uses explicit px page size; keep @page margin-only so CSS
        # cannot override orientation or force a second page.
        page_css = """
      @page {
        margin: 0;
      }
"""
    pdf_css = f"""
    <style>
      {page_css}
      html, body {{
        margin: 0 !important;
        padding: 0 !important;
        background: #ffffff !important;
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }}
      body > table,
      body > table > tbody > tr,
      body > table > tbody > tr > td {{
        margin: 0 !important;
        padding: 0 !important;
        height: auto !important;
        vertical-align: top !important;
      }}
      body table {{
        box-shadow: none !important;
      }}
      img {{
        max-width: 100% !important;
        height: auto !important;
      }}
    </style>
    """
    optimized = html
    optimized = optimized.replace("background-color:#eef2f7", "background-color:#ffffff")
    optimized = optimized.replace("padding:24px 12px", "padding:0")
    optimized = optimized.replace("box-shadow:0 4px 24px rgba(0,0,0,0.08)", "box-shadow:none")
    if "</head>" in optimized:
        optimized = optimized.replace("</head>", f"{pdf_css}</head>", 1)
    else:
        optimized = pdf_css + optimized
    return optimized


def _invoice_pdf_link_callback(uri, _rel):
    """Allow xhtml2pdf to load embedded data-URI images from invoice HTML."""
    if not isinstance(uri, str):
        return uri
    if uri.startswith("data:"):
        try:
            header, encoded = uri.split(",", 1)
            data = base64.b64decode(encoded)
            suffix = ".png"
            if "svg" in header:
                suffix = ".svg"
            elif "jpeg" in header or "jpg" in header:
                suffix = ".jpg"
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            tmp.write(data)
            tmp.close()
            return tmp.name
        except (ValueError, TypeError, OSError):
            return None
    if uri.startswith("file://"):
        return uri[7:]
    return uri


def _generate_pdf_with_playwright(html):
    """
    Render invoice PDF with Chromium so output matches browser design.
    Returns bytes on success; returns None when Playwright isn't available.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 680, "height": 1000})
            page.set_content(html, wait_until="networkidle")
            metrics = page.evaluate(
                """() => {
                  const card = Array.from(document.querySelectorAll('table')).find((table) => {
                    const style = table.getAttribute('style') || '';
                    return style.includes('max-width:640px');
                  }) || document.body;
                  const rect = card.getBoundingClientRect();
                  return {
                    width: Math.ceil(Math.max(rect.width, 640)),
                    height: Math.ceil(Math.max(rect.height, document.body.scrollHeight, 800)),
                  };
                }"""
            )
            width = int(metrics.get("width") or 640)
            height = int(metrics.get("height") or 900) + 4
            page.set_viewport_size({"width": width, "height": height})
            # prefer_css_page_size=False prevents any leftover @page size from
            # forcing landscape / multi-page output.
            pdf_bytes = page.pdf(
                width=f"{width}px",
                height=f"{height}px",
                print_background=True,
                prefer_css_page_size=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
            browser.close()
            return pdf_bytes
    except Exception:
        return None


def _generate_pdf_with_xhtml2pdf(html):
    """Fallback PDF renderer for environments without Playwright/Chromium."""
    from xhtml2pdf import pisa

    buffer = BytesIO()
    pdf_status = pisa.CreatePDF(
        BytesIO(html.encode("utf-8")),
        dest=buffer,
        encoding="utf-8",
        link_callback=_invoice_pdf_link_callback,
    )
    if pdf_status.err:
        raise RuntimeError("Failed to generate invoice PDF")
    return buffer.getvalue()


def get_invoice_pdf_for_payment(payment, enrollment=None, user=None):
    """Return invoice bytes as a PDF generated from the invoice HTML template."""
    html = get_invoice_html_for_payment(payment, enrollment=enrollment, user=user)
    # Prefer Chromium print-to-PDF for near pixel-perfect HTML parity.
    playwright_html = _prepare_invoice_html_for_pdf(html, for_xhtml2pdf=False)
    pdf_bytes = _generate_pdf_with_playwright(playwright_html)
    if not pdf_bytes:
        xhtml_html = _prepare_invoice_html_for_pdf(html, for_xhtml2pdf=True)
        pdf_bytes = _generate_pdf_with_xhtml2pdf(xhtml_html)
    if not pdf_bytes:
        raise RuntimeError("Invoice PDF is empty")
    return pdf_bytes


def serialize_billing_record(payment, enrollment=None, user=None):
    """Serialize payment + enrollment for billing history API."""
    enrollment = _resolve_enrollment(payment, enrollment)
    ctx = build_invoice_context(payment, enrollment=enrollment, user=user)

    course = None
    category = None
    if enrollment:
        try:
            course = enrollment.course
        except Exception:
            course = None
        try:
            category = enrollment.category
        except Exception:
            category = None

    billing = dict(getattr(payment, "billing_details", None) or {})
    tax = dict(getattr(payment, "tax_breakdown", None) or {})

    return {
        "payment_id": str(payment.id),
        "enrollment_id": str(enrollment.id) if enrollment else None,
        "exam_name": ctx.get("exam_name"),
        "course_name": ctx.get("course_name"),
        "plan_name": ctx.get("plan_name"),
        "duration_months": getattr(enrollment, "duration_months", None) if enrollment else None,
        "enrolled_date": str(enrollment.enrolled_date) if enrollment and enrollment.enrolled_date else None,
        "expiry_date": str(enrollment.expiry_date) if enrollment and enrollment.expiry_date else None,
        "amount": float(payment.amount or 0),
        "currency": payment.currency or "INR",
        "amount_display": ctx.get("amount_paid"),
        "subtotal_display": ctx.get("subtotal"),
        "gst_amount_display": ctx.get("gst_amount"),
        "discount_amount_display": ctx.get("discount_amount"),
        "status": payment.status,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "invoice_date": ctx.get("invoice_date"),
        "invoice_number": ctx.get("invoice_number"),
        "transaction_id": payment.razorpay_payment_id,
        "order_id": payment.razorpay_order_id,
        "payment_method": payment.payment_method or "razorpay",
        "coupon_code": getattr(payment, "coupon_code", None) or "",
        "billing_details": billing,
        "tax_breakdown": tax,
    }
