"""Configuration views: get and save (AdminSettings)."""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from common.middleware import authenticate, restrict


def _mask_key(key):
    if not key or len(key) < 8:
        return ''
    return f"{key[:4]}...{key[-4:]}"


@api_view(['GET'])
@authenticate
@restrict(['admin'])
def get_config(request):
    """Return parsing config from AdminSettings (prompts, determinism, model)."""
    try:
        from settings_app.models import AdminSettings
        obj = AdminSettings.objects.first()
        if not obj:
            obj = AdminSettings()
        prompts = getattr(obj, 'prompts', {}) or {}
        prompt1 = prompts.get('prompt1', {})
        prompt2 = prompts.get('prompt2', {})
        prompt3 = prompts.get('prompt3', {})
        parsing_prompt = (prompt1.get('prompt', '') if prompt1 else '') or ''
        generate_prompt = (prompt2.get('prompt', '') if prompt2 else '') or ''
        validation_prompt = (prompt3.get('prompt', '') if prompt3 else '') or ''
        gemini_key = getattr(obj, 'gemini_api_key', '') or ''
        config = {
            "parsing_instructions": getattr(obj, 'parsing_instructions', '') or '',
            "max_retry_count": getattr(obj, 'max_retry_count', 3),
            "temperature": float(getattr(obj, 'temperature', 0)),
            "top_p": float(getattr(obj, 'top_p', 1.0)),
            "frequency_penalty": float(getattr(obj, 'frequency_penalty', 0)),
            "presence_penalty": float(getattr(obj, 'presence_penalty', 0)),
            "gemini_model_selector": getattr(obj, 'gemini_model_selector', 'gemini-1.5-flash-latest') or 'gemini-1.5-flash-latest',
            "model_selector": getattr(obj, 'model_selector', 'gpt-4') or 'gpt-4',
            "prompts": prompts,
            "parsing_prompt": parsing_prompt,
            "generate_prompt": generate_prompt,
            "validation_prompt": validation_prompt,
            "gemini_api_key": _mask_key(gemini_key),
            "gemini_api_key_set": bool(gemini_key),
        }
        return Response({"success": True, "config": config})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def save_config(request):
    """Save parsing config to AdminSettings."""
    try:
        from settings_app.models import AdminSettings
        import json
        data = request.data
        obj = AdminSettings.objects.first()
        if not obj:
            obj = AdminSettings()

        if 'parsing_instructions' in data:
            obj.parsing_instructions = (data.get('parsing_instructions') or '') or ''
        if 'max_retry_count' in data:
            try:
                v = data.get('max_retry_count')
                if v is not None: obj.max_retry_count = max(0, min(10, int(v)))
            except (ValueError, TypeError): pass
        if 'temperature' in data:
            try:
                v = data.get('temperature')
                if v is not None: obj.temperature = max(0.0, min(2.0, float(v)))
            except (ValueError, TypeError): pass
        if 'top_p' in data:
            try:
                v = data.get('top_p')
                if v is not None: obj.top_p = max(0.0, min(1.0, float(v)))
            except (ValueError, TypeError): pass
        if 'frequency_penalty' in data:
            try:
                v = data.get('frequency_penalty')
                if v is not None: obj.frequency_penalty = max(-2.0, min(2.0, float(v)))
            except (ValueError, TypeError): pass
        if 'presence_penalty' in data:
            try:
                v = data.get('presence_penalty')
                if v is not None: obj.presence_penalty = max(-2.0, min(2.0, float(v)))
            except (ValueError, TypeError): pass
        if 'gemini_model_selector' in data:
            v = data.get('gemini_model_selector')
            if v is not None: obj.gemini_model_selector = v or 'gemini-1.5-flash-latest'
        if 'model_selector' in data:
            v = data.get('model_selector')
            if v is not None: obj.model_selector = v or 'gpt-4'
        if 'gemini_api_key' in data:
            obj.gemini_api_key = (data.get('gemini_api_key') or '') or ''
        if 'parsing_prompt' in data:
            obj.prompts = getattr(obj, 'prompts', None) or {}
            if 'prompt1' not in obj.prompts:
                obj.prompts['prompt1'] = {}
            obj.prompts['prompt1']['prompt'] = (data.get('parsing_prompt') or '') or ''
        if 'generate_prompt' in data:
            obj.prompts = getattr(obj, 'prompts', None) or {}
            if 'prompt2' not in obj.prompts:
                obj.prompts['prompt2'] = {}
            obj.prompts['prompt2']['prompt'] = (data.get('generate_prompt') or '') or ''
        if 'validation_prompt' in data:
            obj.prompts = getattr(obj, 'prompts', None) or {}
            if 'prompt3' not in obj.prompts:
                obj.prompts['prompt3'] = {}
            obj.prompts['prompt3']['prompt'] = (data.get('validation_prompt') or '') or ''
        if 'prompts' in data:
            p = data.get('prompts', {})
            if isinstance(p, str):
                try: p = json.loads(p)
                except Exception: p = {}
            if isinstance(p, dict):
                obj.prompts = p

        obj.save()
        return Response({"success": True})
    except Exception as e:
        return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
