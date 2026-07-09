"""Helpers for course exam codes (admin may leave code empty; slug is stored internally)."""


def display_course_code(code=None, slug=None):
    """Return user-facing exam code, or empty when only the slug fallback was stored."""
    code_value = str(code or "").strip()
    slug_value = str(slug or "").strip()
    if not code_value:
        return ""
    if slug_value and code_value.lower() == slug_value.lower():
        return ""
    return code_value


def internal_course_code(code=None, slug=None):
    """Normalize code for DB storage when admin leaves the exam code field empty."""
    trimmed = str(code or "").strip()
    if trimmed:
        return trimmed
    return str(slug or "").strip() or "exam"
