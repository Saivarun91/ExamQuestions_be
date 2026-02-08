"""Helpers for Gemini parsing: config, prompt building, response extraction."""
import json
import os


def get_gemini_key(settings_obj):
    """Get Gemini API key from settings then env then Django settings."""
    key = getattr(settings_obj, 'gemini_api_key', None)
    if key and str(key).strip():
        return str(key).strip()
    key = os.environ.get('GEMINI_API_KEY', '').strip()
    if key:
        return key
    try:
        from django.conf import settings as django_settings
        if getattr(django_settings, 'GEMINI_API_KEY', None):
            return django_settings.GEMINI_API_KEY.strip()
    except Exception:
        pass
    return None


def get_valid_gemini_model(selector, genai):
    """Resolve selected model name to a valid Gemini model name."""
    if not genai:
        return 'gemini-1.5-flash-latest'
    preferred = [
        'gemini-2.5-flash', 'gemini-2.5-pro',
        'gemini-1.5-flash-latest', 'gemini-1.5-pro-latest',
        'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro',
    ]
    name = (selector or 'gemini-1.5-flash-latest').strip()
    if name in preferred:
        return name
    for p in preferred:
        if p in (name or ''):
            return p
    return name or 'gemini-1.5-flash-latest'


def build_parse_prompt(user_prompt, doc_content, extra_instructions=""):
    """Build full prompt from user's dynamic prompt + document content. No hardcoded format; user prompt defines output."""
    parts = [(user_prompt or "").strip()]
    if extra_instructions:
        parts.append(f"\n\nAdditional instructions: {extra_instructions}")
    parts.append("\n\nDocument content:\n")
    parts.append(doc_content or "")
    return "".join(parts)


def _normalize_options(opts):
    """Convert options to list of strings."""
    if not isinstance(opts, list):
        return []
    return [o.get("text", str(o)) if isinstance(o, dict) else str(o) for o in opts]


def extract_questions_from_response(response_text):
    """Extract list of {question_text, options (strings), parsing_flag} from Gemini response text."""
    if not response_text or not response_text.strip():
        return []
    text = response_text.strip()
    if text.startswith('```json'):
        text = text[7:]
    if text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    text = text.strip()

    start = text.find('[')
    if start == -1:
        return []
    depth = 0
    end = -1
    for i in range(start, len(text)):
        if text[i] == '[':
            depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return []
    try:
        data = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        qt = item.get('question_text') or item.get('question', '')
        opts = _normalize_options(item.get('options', []))
        flag = (item.get('parsing_flag') or 'VALID').strip().upper()
        if flag not in ('VALID', 'INVALID'):
            flag = 'VALID'
        out.append({"question_text": qt, "options": opts, "parsing_flag": flag})
    return out


def get_response_text(response):
    """Safely get text from Gemini response."""
    if not response:
        return None
    try:
        return response.text
    except Exception:
        pass
    if hasattr(response, 'candidates') and response.candidates:
        c = response.candidates[0]
        if hasattr(c, 'content') and hasattr(c.content, 'parts'):
            return "".join(
                getattr(p, 'text', '') or ''
                for p in c.content.parts
            )
    return None
