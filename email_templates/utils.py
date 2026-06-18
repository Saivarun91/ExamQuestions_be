"""
Utility functions for email templates
"""
from .models import EmailTemplate
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
import json
import mimetypes
import re

MAX_TEMPLATE_FILE_SIZE = 20 * 1024 * 1024  # 20MB
BLOCKED_TEMPLATE_EXTENSIONS = {
    ".exe", ".bat", ".cmd", ".com", ".msi", ".scr", ".vbs", ".ps1", ".jar", ".dll",
}
TEXT_TEMPLATE_EXTENSIONS = {".html", ".htm", ".txt", ".text", ".csv", ".xml", ".md"}
IMAGE_TEMPLATE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tif", ".tiff",
}
PDF_TEMPLATE_EXTENSIONS = {".pdf"}
TEMPLATE_IMAGE_PLACEHOLDER = "{{template_image}}"
DEFAULT_ATTACHMENT_BODY = "Please find the attached document."


def _is_truthy_value(value):
    """Whether a context value should show optional template sections."""
    if value is None:
        return False
    s = str(value).strip()
    if not s:
        return False
    if s.upper() == "N/A":
        return False
    if re.match(r"^[$₹€£]?\s*0+(\.0+)?$", s):
        return False
    return True


def _guess_content_type(filename):
    guessed, _ = mimetypes.guess_type(filename or "")
    return guessed or "application/octet-stream"


def classify_template_file(filename, content_type=None):
    """Classify uploaded template: text, image, pdf, or attachment."""
    name = (filename or "").lower().strip()
    ct = (content_type or "").lower().strip()

    for ext in BLOCKED_TEMPLATE_EXTENSIONS:
        if name.endswith(ext):
            return "blocked"

    if ct.startswith("text/") or ct in ("application/xhtml+xml",):
        return "text"
    if ct.startswith("image/"):
        return "image"
    if ct == "application/pdf":
        return "pdf"

    for ext in TEXT_TEMPLATE_EXTENSIONS:
        if name.endswith(ext):
            return "text"
    for ext in IMAGE_TEMPLATE_EXTENSIONS:
        if name.endswith(ext):
            return "image"
    for ext in PDF_TEMPLATE_EXTENSIONS:
        if name.endswith(ext):
            return "pdf"

    return "attachment"


def read_template_file(template):
    """Read uploaded template file bytes and metadata."""
    if not getattr(template, "template_file", None):
        return None, None, None, None
    try:
        template.template_file.seek(0)
        data = template.template_file.read()
        template.template_file.seek(0)
        if not data:
            return None, None, None, None
        tf = template.template_file
        filename = getattr(tf, "filename", None) or getattr(tf, "name", None) or "attachment"
        content_type = getattr(tf, "content_type", None) or _guess_content_type(filename)
        kind = classify_template_file(filename, content_type)
        return data, filename, content_type, kind
    except Exception as e:
        print(f"⚠️ Error reading template file for '{getattr(template, 'name', '')}': {e}")
        return None, None, None, None


def get_template_file_kind(template):
    """Return file kind for template upload: text, image, pdf, attachment, or None."""
    _, _, _, kind = read_template_file(template)
    return kind


def template_has_uploaded_file(template):
    """True when an uploaded template file exists and has content."""
    data, _, _, kind = read_template_file(template)
    return bool(data) and kind != "blocked"


def resolve_template_body(template):
    """
    Build email body and attachments from template.
    When a file is uploaded, ONLY the uploaded file is used — manual body is ignored
    so the email does not duplicate content (body text + template image).
    """
    manual_body = getattr(template, "body", "") or ""
    file_data, filename, content_type, kind = read_template_file(template)

    if not file_data or kind == "blocked":
        return manual_body, []

    # HTML / TXT upload — sole email content; {{variables}} are replaced at send time.
    if kind == "text":
        try:
            text = file_data.decode("utf-8", errors="replace")
            if text.strip():
                return text, []
        except Exception:
            pass
        return manual_body, []

    if kind == "image":
        img_tag = (
            f'<img src="cid:template_image" alt="{filename}" '
            'style="max-width:100%;height:auto;display:block;margin:0 auto;" />'
        )
        attachment = {
            "filename": filename,
            "content": file_data,
            "mimetype": content_type or "image/png",
            "inline": True,
            "cid": "template_image",
        }
        # Uploaded image only — do not prepend/append manual email body.
        return img_tag, [attachment]

    # PDF and other files — attach only; no duplicate manual body text.
    attachment = {
        "filename": filename,
        "content": file_data,
        "mimetype": content_type or _guess_content_type(filename),
        "inline": False,
    }
    return "", [attachment]


def get_template_body_content(template):
    """Return preview body for admin UI (text from file or manual body)."""
    manual_body = getattr(template, "body", "") or ""
    file_data, filename, content_type, kind = read_template_file(template)
    if not file_data or kind == "blocked":
        return manual_body
    if kind == "text":
        try:
            text = file_data.decode("utf-8", errors="replace")
            if text.strip():
                return text
        except Exception:
            pass
        return manual_body
    if kind == "image":
        return f"[Image template: {filename}]"
    if kind in ("pdf", "attachment"):
        return f"[File attachment: {filename}]"
    return manual_body or f"[File attachment: {filename}]"


def validate_template_upload_file(uploaded_file):
    """Validate uploaded template file size and blocked extensions."""
    if not uploaded_file:
        return None
    size = getattr(uploaded_file, "size", None)
    if size is not None and size > MAX_TEMPLATE_FILE_SIZE:
        max_mb = MAX_TEMPLATE_FILE_SIZE // (1024 * 1024)
        return f"File too large. Maximum upload size is {max_mb}MB."
    filename = getattr(uploaded_file, "name", "") or ""
    kind = classify_template_file(filename, getattr(uploaded_file, "content_type", None))
    if kind == "blocked":
        return "This file type is not allowed for security reasons."
    return None


def parse_extra_fields(extra_fields_raw):
    """
    Parse admin extra_fields into a dict merged into email context.
    Supports JSON object or comma-separated key=value pairs.
    """
    if not extra_fields_raw:
        return {}
    raw = str(extra_fields_raw).strip()
    if not raw:
        return {}

    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            pass

    result = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" in part:
            key, val = part.split("=", 1)
            result[key.strip()] = val.strip()
        else:
            result[part] = ""
    return result


def process_conditional_blocks(text, context):
    """Process {{#if variable}}...{{/if}} blocks based on context values."""
    if not text or not context:
        return text

    context_map = {}
    for key, value in context.items():
        context_map[key] = value
        context_map[key.lower()] = value

    def _replacer(match):
        key = match.group(1).strip()
        inner = match.group(2)
        val = context_map.get(key) or context_map.get(key.lower())
        if _is_truthy_value(val):
            return inner
        return ""

    pattern = r"\{\{#if\s+([^}]+?)\s*\}\}(.*?)\{\{/if\}\}"
    return re.sub(pattern, _replacer, text, flags=re.DOTALL | re.IGNORECASE)


def remove_empty_detail_lines(text, context):
    """Remove lines that only contain empty/N/A placeholders after replacement."""
    if not text:
        return text

    context_map = {}
    for key, value in context.items():
        context_map[key.lower()] = str(value if value is not None else "").strip()

    lines = text.split("\n")
    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue

        placeholders = re.findall(r"\{\{\s*([^}]+?)\s*\}\}", stripped, flags=re.IGNORECASE)
        if not placeholders:
            kept.append(line)
            continue

        all_empty = True
        for ph in placeholders:
            ph_key = ph.strip().lower()
            if ph_key.startswith("#if ") or ph_key == "/if":
                all_empty = False
                break
            val = context_map.get(ph_key, "")
            if _is_truthy_value(val):
                all_empty = False
                break
        if not all_empty:
            kept.append(line)

    return "\n".join(kept)


def replace_template_variables(text, context):
    """Replace template placeholders with context values."""
    if not text:
        return text
    if not context:
        return text

    context_map = {}
    for key, value in context.items():
        val = str(value if value is not None else "")
        context_map[key] = val
        context_map[key.lower()] = val

    result = process_conditional_blocks(text, context)

    for key, value in context.items():
        val = str(value if value is not None else "")
        patterns = [
            f"{{{{{key}}}}}",
            f"{{{key}}}",
            f"[[{key}]]",
            f"%{key}%",
            f"${{{key}}}",
        ]
        for pattern in patterns:
            result = result.replace(pattern, val)
        result = re.sub(
            r"\{\{\s*" + re.escape(key) + r"\s*\}\}",
            val,
            result,
            flags=re.IGNORECASE,
        )
        result = re.sub(
            r"\[\[\s*" + re.escape(key) + r"\s*\]\]",
            val,
            result,
            flags=re.IGNORECASE,
        )

    def _replace_unknown(match):
        key = match.group(1).strip().lower()
        if key.startswith("#if ") or key == "/if":
            return match.group(0)
        return context_map.get(key, "")

    result = re.sub(r"\{\{\s*([^}]+?)\s*\}\}", _replace_unknown, result)
    result = re.sub(r"\[\[\s*([^\]]+?)\s*\]\]", _replace_unknown, result)
    result = remove_empty_detail_lines(result, context)
    return result


def build_template_context(base_context, template):
    """Merge admin custom extra_fields into the send context."""
    merged = dict(base_context or {})
    if template:
        extra = parse_extra_fields(getattr(template, "extra_fields", "") or "")
        for key, value in extra.items():
            if key not in merged or merged.get(key) in (None, "", "N/A"):
                merged[key] = value
    return merged


def _find_template_by_names(names):
    """Find first active template matching any of the given names (case-insensitive)."""
    for name in names:
        template = EmailTemplate.objects(name=name, is_active=True).first()
        if template:
            return template
        normalized = name.strip().lower()
        for t in EmailTemplate.objects(is_active=True):
            if (t.name or "").strip().lower() == normalized:
                return t
    return None


def get_email_template(template_name, context=None):
    """
    Get email template by name and replace variables with context values.

    Uses uploaded template file when present; otherwise uses manual body field.
    """
    try:
        normalized_search_name = template_name.strip().lower()

        template = EmailTemplate.objects(name=template_name, is_active=True).first()

        if not template:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                if normalized_template_name == normalized_search_name:
                    template = t
                    print(f"✓ Found template with case-insensitive match: '{t.name}'")
                    break

        if not template:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""

                is_password_reset_template = (
                    "password" in normalized_template_name
                    and (
                        "reset" in normalized_template_name
                        or "success" in normalized_template_name
                        or "confirm" in normalized_template_name
                    )
                )
                is_coupon_search = (
                    "coupon" in normalized_search_name or "discount" in normalized_search_name
                )

                if is_coupon_search and is_password_reset_template:
                    continue

                if len(normalized_search_name) >= 3:
                    if (
                        normalized_search_name in normalized_template_name
                        or normalized_template_name in normalized_search_name
                    ):
                        template = t
                        print(f"✓ Found template with partial match: '{t.name}' (searched for '{template_name}')")
                        break

        if not template and (
            "invoice" in normalized_search_name
            or normalized_search_name in ("payment invoice", "payment receipt", "order invoice")
        ):
            template = _find_template_by_names([
                "Payment Invoice",
                "Invoice",
                "Payment Receipt",
                "Order Invoice",
                "Invoice Email",
            ])
            if template:
                print(f"✓ Found invoice template: '{template.name}' (searched for '{template_name}')")

        if not template and "password" in normalized_search_name:
            variations = [
                "Password Reset Confirmation",
                "Password Reset Successful",
                "Password Reset",
                "Reset Password Confirmation",
                "Reset Password Successful",
                "Password Reset Email",
                "Reset Confirmation",
                "Password Reset Success",
            ]
            template = _find_template_by_names(variations)
            if template:
                print(f"✓ Found template with variation match: '{template.name}' (searched for '{template_name}')")

        if not template and "password reset" in normalized_search_name:
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""
                if "password reset" in normalized_template_name and (
                    "success" in normalized_template_name
                    or "confirm" in normalized_template_name
                    or "successful" in normalized_template_name
                ):
                    template = t
                    print(f"✓ Found template with keyword match: '{t.name}' (searched for '{template_name}')")
                    break

        if not template and (
            "coupon" in normalized_search_name
            or "discount" in normalized_search_name
            or "assignment" in normalized_search_name
            or "notification" in normalized_search_name
        ):
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""

                is_password_reset_template = (
                    "password" in normalized_template_name
                    and (
                        "reset" in normalized_template_name
                        or "success" in normalized_template_name
                        or "confirm" in normalized_template_name
                        or "successful" in normalized_template_name
                    )
                )
                if is_password_reset_template:
                    continue

                is_coupon_related = (
                    "coupon" in normalized_template_name
                    or "discount" in normalized_template_name
                    or ("assignment" in normalized_template_name and "coupon" in normalized_template_name)
                    or ("notification" in normalized_template_name and "coupon" in normalized_template_name)
                )
                if is_coupon_related:
                    template = t
                    print(f"✓ Found template with coupon keyword match: '{t.name}' (searched for '{template_name}')")
                    break

        if not template and (
            "enrollment" in normalized_search_name
            or "enrol" in normalized_search_name
            or (
                "course" in normalized_search_name
                and ("confirm" in normalized_search_name or "success" in normalized_search_name)
            )
        ):
            all_templates = EmailTemplate.objects(is_active=True)
            for t in all_templates:
                normalized_template_name = t.name.strip().lower() if t.name else ""

                is_password_reset_template = (
                    "password" in normalized_template_name
                    and (
                        "reset" in normalized_template_name
                        or "success" in normalized_template_name
                        or "confirm" in normalized_template_name
                        or "successful" in normalized_template_name
                    )
                )
                is_coupon_template = (
                    "coupon" in normalized_template_name or "discount" in normalized_template_name
                )
                if is_password_reset_template or is_coupon_template:
                    continue

                is_enrollment_related = (
                    "enrollment" in normalized_template_name
                    or "enrol" in normalized_template_name
                    or (
                        "course" in normalized_template_name
                        and ("confirm" in normalized_template_name or "success" in normalized_template_name)
                    )
                )
                if is_enrollment_related:
                    template = t
                    print(f"✓ Found template with enrollment keyword match: '{t.name}' (searched for '{template_name}')")
                    break

        if not template:
            all_active = EmailTemplate.objects(is_active=True)
            template_names = [t.name for t in all_active] if all_active else []
            print(f"⚠️ Email template '{template_name}' not found or not active.")
            print(f"   Available active templates: {template_names}")
            print(f"   Searched for (normalized): '{normalized_search_name}'")
            return None

        print(f"✓ Found email template: '{template.name}'")

        subject = template.subject
        body, file_attachments = resolve_template_body(template)
        if not body.strip() and not file_attachments:
            print(f"⚠️ Template '{template.name}' has no body content (no file and empty body).")
            return None

        using_file = template_has_uploaded_file(template)
        file_kind = get_template_file_kind(template) if using_file else None
        if using_file:
            print(f"✓ Using uploaded template file for '{template.name}' (type: {file_kind})")
        else:
            print(f"✓ Using manual body field for '{template.name}'")

        send_context = build_template_context(context, template)

        if send_context:
            subject = replace_template_variables(subject, send_context)
            body = replace_template_variables(body, send_context)
            print(f"✓ Replaced variables in template: {list(send_context.keys())}")

        html_body = body.strip()
        attachment_only = not html_body and bool(file_attachments)

        if attachment_only:
            html_body = "<html><body></body></html>"

        html_lower = html_body.lower()
        has_complete_html = (
            ("<!doctype" in html_lower or "<html" in html_lower)
            and "</html>" in html_lower
            and "<head" in html_lower
            and "<body" in html_lower
        )

        if not has_complete_html:
            has_html_tags = bool(re.search(r"<[^>]+>", html_body))

            if has_html_tags:
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
                html_body = html_body.replace("\n", "<br>")
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

        plain_body = body
        if attachment_only:
            plain_body = " "
        else:
            plain_body = plain_body.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
            plain_body = plain_body.replace("</p>", "\n\n").replace("<p>", "")
            plain_body = plain_body.replace("</div>", "\n").replace("<div>", "")
            plain_body = re.sub(r"<[^>]+>", "", plain_body)
            plain_body = re.sub(r"\n\s*\n\s*\n", "\n\n", plain_body)
            plain_body = plain_body.strip()

        print("✓ Email template processed successfully")
        return (subject, html_body, plain_body, file_attachments)
    except Exception as e:
        print(f"✗ Error getting email template {template_name}: {e}")
        import traceback
        print(traceback.format_exc())
        return None


def unpack_template_data(template_data):
    """Unpack get_email_template() result — always returns (subject, html, plain, attachments)."""
    if not template_data:
        return None, None, None, []
    attachments = template_data[3] if len(template_data) > 3 else []
    return template_data[0], template_data[1], template_data[2], attachments


def send_template_email(recipient_list, template_data, fail_silently=False):
    """
    Send email from get_email_template() result.
    Supports HTML body plus optional file attachments (PDF, images, etc.).
    """
    if not template_data or len(template_data) < 3:
        return False

    subject = template_data[0]
    html_message = template_data[1]
    plain_message = template_data[2]
    attachments = template_data[3] if len(template_data) > 3 else []

    if not recipient_list:
        return False

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_list,
        )
        if html_message:
            msg.attach_alternative(html_message, "text/html")

        for att in attachments or []:
            content = att.get("content")
            if not content:
                continue
            filename = att.get("filename") or "attachment"
            mimetype = att.get("mimetype") or _guess_content_type(filename)

            if att.get("inline") and mimetype.startswith("image/"):
                from email.mime.image import MIMEImage
                from email.mime.base import MIMEBase
                from email import encoders

                subtype = mimetype.split("/", 1)[-1]
                if subtype == "jpg":
                    subtype = "jpeg"
                cid = att.get("cid") or "template_image"
                if subtype == "svg+xml":
                    part = MIMEBase("image", "svg+xml")
                    part.set_payload(content)
                    encoders.encode_base64(part)
                    part.add_header("Content-ID", f"<{cid}>")
                    part.add_header("Content-Disposition", "inline", filename=filename)
                    msg.attach(part)
                else:
                    img = MIMEImage(content, _subtype=subtype)
                    img.add_header("Content-ID", f"<{cid}>")
                    img.add_header("Content-Disposition", "inline", filename=filename)
                    msg.attach(img)
            else:
                msg.attach(filename, content, mimetype)

        msg.send(fail_silently=fail_silently)
        return True
    except Exception as e:
        print(f"✗ Error sending template email: {e}")
        import traceback
        print(traceback.format_exc())
        if not fail_silently:
            raise
        return False
