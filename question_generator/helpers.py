"""Helpers for OpenAI generation."""
import json
import os


def get_openai_key(settings_obj):
    """Get OpenAI API key from settings then env."""
    key = getattr(settings_obj, 'openai_api_key', None)
    if key and str(key).strip():
        return str(key).strip()
    key = os.environ.get('OPENAI_API_KEY', '').strip()
    if key:
        return key
    try:
        from django.conf import settings as django_settings
        if getattr(django_settings, 'OPENAI_API_KEY', None):
            return django_settings.OPENAI_API_KEY.strip()
    except Exception:
        pass
    return None


def _extract_options_from_item(item):
    """Extract options list from item; each option = {text, explanation}. Handles multiple LLM formats."""
    opts = (
        item.get('options') or item.get('choices') or item.get('option_list') or
        item.get('answer_choices') or item.get('options_list') or []
    )
    if isinstance(opts, list) and opts:
        out = []
        for o in opts:
            if isinstance(o, dict):
                text = (o.get('text') or o.get('value') or o.get('option') or o.get('label') or o.get('content') or '').strip()
                expl = (o.get('explanation') or o.get('reason') or o.get('desc') or '').strip()
                out.append({"text": text, "explanation": expl})
            else:
                out.append({"text": str(o).strip(), "explanation": ""})
        if any((o.get("text") or "").strip() or (o.get("explanation") or "").strip() for o in out):
            return out
    # Build from option_1, option_2, ... or option_A, option_B, ... and _explanation variants
    out = []
    for i in range(1, 11):
        letter = chr(64 + i)  # A, B, C, ...
        text = (
            (item.get(f'option_{i}') or '') or
            (item.get(f'option_{letter}') or '') or
            (item.get(f'choice_{i}') or '') or
            (item.get(f'choice_{letter}') or '')
        )
        text = str(text).strip() if text else ''
        expl = (
            (item.get(f'option_{i}_explanation') or '') or
            (item.get(f'option_{letter}_explanation') or '') or
            (item.get(f'explanation_{i}') or '') or
            (item.get(f'explanation_{letter}') or '')
        )
        expl = str(expl).strip() if expl else ''
        if text or expl or i <= 4:
            out.append({"text": text, "explanation": expl})
    return out


def _explanation_indicates_correct(explanation):
    """True if the option explanation marks this option as the correct answer."""
    if not explanation or not isinstance(explanation, str):
        return False
    e = explanation.strip().lower()
    if not e:
        return False
    # Clearly incorrect
    if "incorrect" in e and e.index("incorrect") < (e.find("correct") if "correct" in e else 999):
        return False
    if e.startswith("correct") or e.startswith("correct.") or e.startswith("correct,"):
        return True
    if " correct." in e or " correct," in e or " correct " in e:
        return True
    return False


def _infer_correct_from_explanations(options_list):
    """When correct_answers is missing, infer from options whose explanation says 'Correct.'."""
    if not options_list:
        return []
    inferred = []
    for o in options_list:
        expl = (o.get("explanation") or o.get("reason") or o.get("desc") or "").strip()
        if _explanation_indicates_correct(expl):
            text = (o.get("text") or o.get("value") or "").strip()
            if text:
                inferred.append(text)
    return inferred


def _extract_correct_answers_from_item(item, options_list):
    """Extract correct_answers (list of strings). Handles text, indices, or letters."""
    correct = item.get('correct_answers') or item.get('correct_answer') or item.get('answer') or item.get('answers')
    if correct is None:
        correct = item.get('correct_option') or item.get('correct_option_index')
        if correct is not None:
            idx = int(correct) if isinstance(correct, (int, float)) else (ord(str(correct).strip().upper()) - 64)
            if 1 <= idx <= len(options_list):
                correct = [options_list[idx - 1].get('text', '')]
            else:
                correct = []
    if isinstance(correct, str):
        correct = [correct]
    if isinstance(correct, (int, float)):
        correct = [correct]
    if not isinstance(correct, list):
        correct = []
    return [str(c).strip() for c in correct if c is not None and str(c).strip()]


def parse_generated_response(text):
    """Parse OpenAI response into list of { question_text, options, correct_answers, explanation }.
    Handles multiple JSON shapes (options array, option_1/option_2, etc.).
    """
    if not text or not text.strip():
        return []
    raw = text.strip()
    if raw.startswith('```json'):
        raw = raw[7:]
    if raw.startswith('```'):
        raw = raw[3:]
    if raw.endswith('```'):
        raw = raw[:-3]
    raw = raw.strip()
    start = raw.find('[')
    if start == -1:
        start = raw.find('{')
        if start != -1:
            raw = '[' + raw[start:] + ']'
            start = 0
    if start == -1:
        return []
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] in '[{':
            depth += 1
        elif raw[i] in ']}':
            depth -= 1
            if depth == 0:
                end = i
                break
    if end == -1:
        return []
    try:
        data = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        data = [data] if isinstance(data, dict) else []
    out = []
    for item in data:
        if not isinstance(item, dict):
            continue
        # Never skip: include every question from the response
        qtext = (item.get('question_text') or item.get('question') or item.get('text') or item.get('q') or '').strip()
        opts_clean = _extract_options_from_item(item)
        correct = _extract_correct_answers_from_item(item, opts_clean)
        # If AI didn't send correct_answers/correct_option, infer from option explanations (e.g. "Correct." / "Incorrect.")
        if not correct and opts_clean:
            correct = _infer_correct_from_explanations(opts_clean)
        # Keep numeric/letter indices as-is (e.g. ["1"], ["2"], ["3"]) so the view can use them directly.
        # Only resolve to option text when the value is not already a valid 1-based index.
        if correct and opts_clean:
            n_opts = len(opts_clean)
            all_valid_indices = True
            for c in correct:
                cstr = str(c).strip()
                if cstr.isdigit():
                    if not (1 <= int(cstr) <= n_opts):
                        all_valid_indices = False
                        break
                elif len(cstr) == 1 and cstr.isalpha():
                    idx = ord(cstr.upper()) - 64
                    if not (1 <= idx <= n_opts):
                        all_valid_indices = False
                        break
                else:
                    all_valid_indices = False
                    break
            if not all_valid_indices:
                # Resolve indices/letters to option text for non-index values
                resolved = []
                for c in correct:
                    cstr = str(c).strip()
                    if cstr.isdigit():
                        idx = int(cstr)
                        if 1 <= idx <= n_opts:
                            resolved.append(opts_clean[idx - 1].get('text', ''))
                        else:
                            resolved.append(cstr)
                    elif len(cstr) == 1 and cstr.isalpha():
                        idx = ord(cstr.upper()) - 64
                        if 1 <= idx <= n_opts:
                            resolved.append(opts_clean[idx - 1].get('text', ''))
                        else:
                            resolved.append(cstr)
                    else:
                        resolved.append(cstr)
                correct = resolved
        expl = (
            (item.get('explanation') or '') or
            (item.get('overall_explanation') or '') or
            (item.get('explanation_text') or '') or
            (item.get('summary') or '') or
            (item.get('reason') or '') or
            (item.get('rationale') or '') or
            (item.get('answer_explanation') or '') or
            (item.get('overall_explanation_text') or '')
        )
        expl = str(expl).strip() if expl else ''
        # Always append: do not skip any question; use safe defaults for missing fields
        out.append({
            "question_text": qtext or "Untitled question",
            "options": opts_clean if opts_clean else [],
            "correct_answers": correct if correct else [],
            "explanation": expl or "",
        })
    return out
