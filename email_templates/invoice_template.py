"""
Built-in payment invoice HTML email template.
Used when admin has not uploaded a custom HTML/text invoice template.
"""
import os
import re
import base64
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path
from .utils import replace_template_variables

DEFAULT_ISSUED_BY = "TutorKhoj Private Limited"
DEFAULT_COMPANY_ADDRESS = os.getenv(
    "INVOICE_COMPANY_ADDRESS",
    "202, Serinity Diamond Apt, Gopanpally, Hyderabad, Telangana, India 500046",
).strip()
DEFAULT_ISSUER_GSTIN = os.getenv("INVOICE_GSTIN", "").strip()
DEFAULT_BANK_NAME = os.getenv("INVOICE_BANK_NAME", "Wardiere")
DEFAULT_ACCOUNT_NO = os.getenv("INVOICE_ACCOUNT_NO", "0123 4567 8901")
DEFAULT_ACCOUNT_NAME = os.getenv("INVOICE_ACCOUNT_NAME", "Claudia Alves")
DEFAULT_BRAND_NAME = os.getenv("INVOICE_BRAND_NAME", "All Exam Questions")
INVOICE_BLUE = "#4a8fd4"
INVOICE_BLUE_DARK = "#3b78b8"
LOGO_CID = "invoice_logo"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

DEFAULT_INVOICE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Invoice {{invoice_number}}</title>
</head>
<body style="margin:0;padding:0;background-color:#eef2f7;font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#eef2f7;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="640" cellspacing="0" cellpadding="0" style="max-width:640px;width:100%;background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
          <!-- Top blue accent -->
          <tr>
            <td style="padding:0;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td width="130" style="background:{{invoice_blue}};border-bottom-right-radius:90px;height:58px;vertical-align:top;line-height:0;font-size:0;">&nbsp;</td>
                  <td style="background:#ffffff;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Header -->
          <tr>
            <td style="padding:18px 36px 0 36px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td width="160" valign="top">
                    <img src="{{logo_src}}"
                        alt="{{brand_name}}"
                        width="140"
                        style="display:block;border:0;outline:none;height:auto;" />
                  </td>
                  <td valign="top" align="right">
                    <div style="font-size:30px;font-weight:700;color:{{invoice_blue}};font-family:Arial,Helvetica,sans-serif;line-height:1;">INVOICE</div>
                    <div style="margin-top:10px;font-size:13px;color:#333;line-height:1.7;text-align:right;">
                      {{company_address}}
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Invoice to / Billed to -->
          <!-- Invoice To -->
          <tr>
            <td style="padding:22px 36px 0 36px;">
              <div style="font-size:15px;font-weight:bold;color:#111111;margin-bottom:12px;">
                Invoice To :
              </div>

              <table role="presentation" cellspacing="0" cellpadding="0"
                    style="font-size:14px;color:#333333;line-height:1.8;">
                <tr><td><strong>Issued by :</strong> {{issued_by}}</td></tr>
                <tr><td><strong>Invoice no :</strong> {{invoice_number}}</td></tr>
                <tr><td><strong>Date :</strong> {{invoice_date}}</td></tr>
                {{#if invoice_gstin}}
                <tr><td><strong>GSTIN :</strong> {{invoice_gstin}}</td></tr>
                {{/if}}
                <tr><td><strong>Transaction ID :</strong> {{transaction_id}}</td></tr>
              </table>
            </td>
          </tr>

          <!-- Billed To -->
          <tr>
            <td style="padding:20px 36px 0 36px;">
              <div style="font-size:15px;font-weight:bold;color:#111111;margin-bottom:12px;">
                Billed To :
              </div>

              <table role="presentation" cellspacing="0" cellpadding="0"
                    style="font-size:14px;color:#333333;line-height:1.8;">
                <tr><td><strong>Name :</strong> {{billing_name}}</td></tr>
                <tr><td><strong>Phone :</strong> {{billing_phone}}</td></tr>
                <tr><td><strong>Email :</strong> {{customer_email}}</td></tr>
                <tr><td><strong>Address :</strong> {{billing_address}}</td></tr>
              </table>
            </td>
          </tr>
          <!-- Items table -->
          <tr>
            <td style="padding:28px 36px 0 36px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;font-size:14px;">
                <tr style="background:#f2f4f8;">
                  <th align="left" style="padding:12px 10px;font-weight:bold;color:#111;border-bottom:1px solid #e2e6ee;">NO</th>
                  <th align="left" style="padding:12px 10px;font-weight:bold;color:#111;border-bottom:1px solid #e2e6ee;">ITEM DESRIPTION</th>
                  <th align="left" style="padding:12px 10px;font-weight:bold;color:#111;border-bottom:1px solid #e2e6ee;">PRICE</th>
                  <th align="left" style="padding:12px 10px;font-weight:bold;color:#111;border-bottom:1px solid #e2e6ee;">PLAN</th>
                  <th align="left" style="padding:12px 10px;font-weight:bold;color:#111;border-bottom:1px solid #e2e6ee;">TOTAL</th>
                </tr>
                <tr>
                  <td style="padding:14px 10px;border-bottom:1px solid #e2e6ee;color:#333;">1</td>
                  <td style="padding:14px 10px;border-bottom:1px solid #e2e6ee;color:#333;">{{exam_name}}</td>
                  <td style="padding:14px 10px;border-bottom:1px solid #e2e6ee;color:#333;">{{exam_price}}</td>
                  <td style="padding:14px 10px;border-bottom:1px solid #e2e6ee;color:#333;">{{plan_name}}</td>
                  <td style="padding:14px 10px;border-bottom:1px solid #e2e6ee;color:#333;">{{exam_price}}</td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Totals -->
          <tr>
            <td style="padding:18px 36px 0 36px;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td width="50%">&nbsp;</td>
                  <td width="50%">
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="font-size:14px;color:#333;">
                      <tr>
                        <td style="padding:8px 0;border-bottom:1px solid #e2e6ee;"><strong>Total :</strong></td>
                        <td align="right" style="padding:8px 0;border-bottom:1px solid #e2e6ee;">{{subtotal}}</td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;border-bottom:1px solid #e2e6ee;"><strong>Tax :</strong></td>
                        <td align="right" style="padding:8px 0;border-bottom:1px solid #e2e6ee;">{{tax_display}}</td>
                      </tr>
                      <tr>
                        <td style="padding:8px 0;border-bottom:1px solid #e2e6ee;"><strong>Discount :</strong></td>
                        <td align="right" style="padding:8px 0;border-bottom:1px solid #e2e6ee;">{{discount_display}}</td>
                      </tr>
                      <tr>
                        <td style="padding:10px 0;font-weight:bold;font-size:15px;"><strong>Sub Total :</strong></td>
                        <td align="right" style="padding:10px 0;font-weight:bold;font-size:15px;">{{amount_paid}}</td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          <!-- Notes -->
          <tr>
            <td style="padding:20px 36px 20px 36px;">
              <div style="font-size:15px;font-weight:bold;color:#111111;margin-bottom:8px;">
                Notes:
              </div>
              <div style="font-size:13px;color:#555555;line-height:1.7;">
                This is a system generated invoice and does not require a physical signature.<br>
                This invoice is issued by TutorKhoj Private Limited operating as AllExamQuestions.<br>
                
              </div>
            </td>
          </tr>
          
          <!-- Bottom blue accent (mirrors top-left) -->
          <tr>
            <td style="padding:0;line-height:0;font-size:0;">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                  <td style="background:#ffffff;">&nbsp;</td>
                  <td width="130" align="right" style="background:{{invoice_blue}};border-top-left-radius:90px;height:58px;vertical-align:bottom;line-height:0;font-size:0;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _guess_image_mimetype(url, content_type, data):
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct.startswith("image/"):
        return ct
    guessed, _ = mimetypes.guess_type(url or "")
    if guessed and guessed.startswith("image/"):
        return guessed
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data.lstrip()[:5] == b"<?xml" or b"<svg" in data[:200]:
        return "image/svg+xml"
    return "image/png"


def _get_company_invoice_details():
    address = DEFAULT_COMPANY_ADDRESS
    gstin = DEFAULT_ISSUER_GSTIN
    try:
        from settings_app.models import AdminSettings, ContactUs

        settings_obj = AdminSettings.objects.first()
        if settings_obj:
            settings_address = (getattr(settings_obj, "contact_address", "") or "").strip()
            if settings_address:
                address = settings_address
            settings_gstin = (
                getattr(settings_obj, "gstin", None)
                or getattr(settings_obj, "gst_id", None)
                or getattr(settings_obj, "company_gstin", None)
                or ""
            )
            settings_gstin = str(settings_gstin).strip()
            if settings_gstin:
                gstin = settings_gstin
        if not address:
            contact = ContactUs.objects.first()
            if contact:
                address = (getattr(contact, "contact_address", "") or "").strip()
    except Exception as exc:
        print(f"Warning: Could not load company invoice details: {exc}")
    return address or DEFAULT_COMPANY_ADDRESS, gstin


def _format_address_html(address):
    if not address:
        return "N/A"
    return (
        str(address)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\r\n", "\n")
        .replace("\n", "<br>")
    )


def _get_site_branding():
    logo_url = (os.getenv("INVOICE_LOGO_URL") or "").strip()
    site_name = ""
    try:
        from settings_app.models import AdminSettings

        settings_obj = AdminSettings.objects.first()
        if settings_obj:
            logo_url = logo_url or (getattr(settings_obj, "logo_url", "") or "").strip()
            site_name = (getattr(settings_obj, "site_name", "") or "").strip()
    except Exception as exc:
        print(f"Warning: Could not load site branding for invoice: {exc}")
    return logo_url, site_name


def _fetch_url_bytes(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AllExamQuestions-Invoice/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read(), resp.headers.get("Content-Type", "")


def _fallback_logo_bytes():
    local_candidates = [
        ASSETS_DIR / "brand_logo.png",
        ASSETS_DIR / "brand_logo.jpg",
        ASSETS_DIR / "brand_logo.svg",
    ]
    for path in local_candidates:
        if path.is_file():
            data = path.read_bytes()
            return data, _guess_image_mimetype(str(path), "", data)

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="230" height="48" viewBox="0 0 230 48">
  <rect x="0" y="4" width="40" height="40" rx="6" fill="{INVOICE_BLUE}"/>
  <path d="M12 30 L18 14 L22 14 L16 30 Z M20 22 L28 22 L28 25 L20 25 Z" fill="#ffffff"/>
  <path d="M24 14 L30 28 L27 30 L21 16 Z" fill="#ffffff" opacity="0.9"/>
  <text x="50" y="31" font-family="Arial, Helvetica, sans-serif" font-size="17" font-weight="700" fill="{INVOICE_BLUE}">All Exam Questions</text>
</svg>"""
    return svg.encode("utf-8"), "image/svg+xml"


def build_invoice_logo_attachment():
    """Return inline CID attachment for the invoice logo image."""
    logo_url, _site_name = _get_site_branding()
    content = None
    mimetype = "image/png"
    filename = "invoice_logo.png"

    if logo_url:
        try:
            if logo_url.startswith("http://") or logo_url.startswith("https://"):
                content, raw_ct = _fetch_url_bytes(logo_url)
                mimetype = _guess_image_mimetype(logo_url, raw_ct, content)
            elif os.path.isfile(logo_url):
                content = Path(logo_url).read_bytes()
                mimetype = _guess_image_mimetype(logo_url, "", content)
        except (urllib.error.URLError, OSError, ValueError) as exc:
            print(f"Warning: Could not fetch invoice logo from URL: {exc}")

    if not content:
        content, mimetype = _fallback_logo_bytes()

    ext = mimetypes.guess_extension(mimetype) or ".png"
    if ext == ".jpe":
        ext = ".jpg"
    filename = f"invoice_logo{ext}"

    return {
        "filename": filename,
        "content": content,
        "mimetype": mimetype,
        "inline": True,
        "cid": LOGO_CID,
    }


def _is_zero_amount(value):
    if value is None:
        return True
    s = str(value).strip()
    if not s or s in ("-", "N/A"):
        return True
    nums = re.sub(r"[^0-9.]", "", s)
    try:
        return float(nums or 0) == 0
    except ValueError:
        return False


def enrich_invoice_context(context):
    """Add built-in invoice template fields to the send context."""
    ctx = dict(context or {})
    logo_url, site_name = _get_site_branding()
    company_address, issuer_gstin = _get_company_invoice_details()
    if site_name:
        ctx.setdefault("brand_name", site_name)
    ctx.setdefault("brand_name", DEFAULT_BRAND_NAME)
    ctx.setdefault("logo_url", logo_url or "")
    ctx.setdefault("logo_cid", LOGO_CID)
    ctx.setdefault("invoice_blue", INVOICE_BLUE)
    ctx.setdefault("invoice_blue_dark", INVOICE_BLUE_DARK)
    ctx.setdefault("issued_by", DEFAULT_ISSUED_BY)
    ctx.setdefault("company_address", _format_address_html(company_address))
    ctx.setdefault("issuer_gstin", issuer_gstin)
    ctx.setdefault("bank_name", DEFAULT_BANK_NAME)
    ctx.setdefault("account_no", DEFAULT_ACCOUNT_NO)
    ctx.setdefault("account_name", DEFAULT_ACCOUNT_NAME)

    discount_raw = ctx.get("discount_amount", "")
    gst_raw = ctx.get("gst_amount", "")
    ctx.setdefault("discount_display", "-" if _is_zero_amount(discount_raw) else discount_raw)
    ctx.setdefault("tax_display", "-" if _is_zero_amount(gst_raw) else gst_raw)

    # Invoice To GSTIN = issuer GSTIN (matches screenshot); fall back to customer.
    issuer = str(ctx.get("issuer_gstin") or "").strip()
    customer = str(ctx.get("customer_gstin") or ctx.get("gst_id") or "").strip()
    if customer in ("N/A", "-", "None"):
        customer = ""
    if issuer in ("N/A", "-", "None"):
        issuer = ""
    ctx["invoice_gstin"] = issuer or customer
    return ctx


def _html_to_plain(html):
    text = html.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("</tr>", "\n").replace("</td>", " ").replace("</div>", "\n")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def should_use_custom_admin_invoice(template):
    """Use admin template only when a custom HTML/text file was uploaded."""
    if not template:
        return False
    from .utils import template_has_uploaded_file, get_template_file_kind

    if not template_has_uploaded_file(template):
        return False
    return get_template_file_kind(template) == "text"


def find_admin_invoice_template():
    from .models import EmailTemplate

    names = [
        "Payment Invoice",
        "Invoice Main",
        "Invoice",
        "Payment Receipt",
        "Order Invoice",
        "Invoice Email",
    ]
    for name in names:
        t = EmailTemplate.objects(name=name, is_active=True).first()
        if t:
            return t
    for t in EmailTemplate.objects(is_active=True):
        n = (t.name or "").lower()
        if "invoice" in n or ("payment" in n and "receipt" in n):
            return t
    return None


def render_builtin_invoice_email(context, subject=None):
    """
    Render the built-in invoice HTML with dynamic values.
    Returns (subject, html_body, plain_body, attachments).
    """
    ctx = enrich_invoice_context(context)
    ctx["logo_src"] = f"cid:{LOGO_CID}"
    html_body = replace_template_variables(DEFAULT_INVOICE_HTML, ctx)
    plain_body = _html_to_plain(html_body)

    exam_name = ctx.get("exam_name") or ctx.get("course_name") or "Course"
    default_subject = f"Payment Invoice - {exam_name}"
    final_subject = subject or default_subject
    final_subject = replace_template_variables(final_subject, ctx)

    attachments = [build_invoice_logo_attachment()]
    return (final_subject, html_body, plain_body, attachments)


def render_builtin_invoice_download(context):
    """Render invoice HTML for browser download (logo embedded as base64)."""
    ctx = enrich_invoice_context(context)
    logo_att = build_invoice_logo_attachment()
    b64 = base64.b64encode(logo_att["content"]).decode("ascii")
    ctx["logo_src"] = f"data:{logo_att['mimetype']};base64,{b64}"
    return replace_template_variables(DEFAULT_INVOICE_HTML, ctx)
