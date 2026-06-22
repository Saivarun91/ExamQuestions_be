import mimetypes
import os
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile


def _webp_filename(original_name):
    base = os.path.splitext(os.path.basename(original_name or "image"))[0] or "image"
    return f"{base}.webp"


def convert_uploaded_image_to_webp(uploaded_file, quality=85):
    """
    Convert uploaded raster images to WebP before storage.
    Returns the original file for SVG/WebP or when conversion is unavailable.
    """
    if not uploaded_file:
        return uploaded_file

    content_type = getattr(uploaded_file, "content_type", None) or mimetypes.guess_type(
        getattr(uploaded_file, "name", "") or ""
    )[0] or ""

    if content_type in ("image/webp", "image/svg+xml"):
        return uploaded_file

    try:
        from PIL import Image
    except ImportError:
        return uploaded_file

    try:
        uploaded_file.seek(0)
        image = Image.open(uploaded_file)

        if getattr(image, "is_animated", False):
            uploaded_file.seek(0)
            return uploaded_file

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

        buffer = BytesIO()
        save_kwargs = {"format": "WEBP", "quality": quality, "method": 6}
        if image.mode == "RGBA":
            save_kwargs["lossless"] = False
        image.save(buffer, **save_kwargs)
        buffer.seek(0)

        webp_name = _webp_filename(getattr(uploaded_file, "name", "image"))
        return InMemoryUploadedFile(
            buffer,
            getattr(uploaded_file, "field_name", None),
            webp_name,
            "image/webp",
            buffer.getbuffer().nbytes,
            getattr(uploaded_file, "charset", None),
        )
    except Exception:
        uploaded_file.seek(0)
        return uploaded_file
