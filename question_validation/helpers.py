"""Call Gemini with Prompt 3 + question + options only; parse answer(s) from response."""
import json


def gemini_text_answers_to_indices(gemini_texts, options_text_list):
    """
    Convert Gemini's answer(s) from option text to 1-based option indices.
    options_text_list: list of option strings in display order (e.g. ["Incident", "Problem", ...]).
    Returns list of index strings e.g. ["1"], ["2","3"] for multiple.
    """
    if not options_text_list or not gemini_texts:
        return []
    indices = []
    opts_lower = [str(o).strip().lower() for o in options_text_list]
    for text in gemini_texts:
        t = str(text).strip()
        if not t:
            continue
        t_lower = t.lower()
        for i, opt in enumerate(opts_lower):
            if opt == t_lower or (opt and t_lower in opt) or (t_lower and opt in t_lower):
                indices.append(str(i + 1))
                break
    return indices


def _normalize_answers(answers):
    """Normalize for comparison: trim, sort, case-insensitive match."""
    if not answers:
        return []
    out = [str(a).strip() for a in answers if a is not None and str(a).strip()]
    return sorted(set(out), key=lambda x: x.lower())


def answers_match(openai_answers, gemini_answers):
    """True if OpenAI and Gemini answer sets are equivalent (order-independent, case-insensitive)."""
    a = _normalize_answers(openai_answers)
    b = _normalize_answers(gemini_answers)
    if len(a) != len(b):
        return False
    a_set = {s.lower() for s in a}
    b_set = {s.lower() for s in b}
    return a_set == b_set


def parse_gemini_answer_response(text):
    """Parse Gemini response to get answer(s). Expects JSON with 'answer' or 'answers' or 'correct_answer'."""
    if not text or not text.strip():
        return []
    raw = text.strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    start = raw.find("{")
    if start == -1:
        start = raw.find("[")
    if start == -1:
        return []
    depth = 0
    end = -1
    for i in range(start, len(raw)):
        if raw[i] in "{[":
            depth += 1
        elif raw[i] in "}]":
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
     # ✅ Gemini Prompt 3 ALWAYS returns indices in "status"
    if isinstance(data, dict):
        status_vals = data.get("status")
        if isinstance(status_vals, list):
            return [str(v).strip() for v in status_vals if str(v).strip()]
        if isinstance(status_vals, str):
            return [status_vals.strip()]

    # if isinstance(data, dict):
    #     ans = data.get("answer") or data.get("correct_answer") or data.get("correct_answer_s")
    #     if ans is not None:
    #         return [ans] if isinstance(ans, str) else list(ans) if isinstance(ans, list) else []
    #     ans_list = data.get("answers") or data.get("correct_answers")
    #     if isinstance(ans_list, list):
    #         return [str(a) for a in ans_list if a is not None]
    #     if isinstance(ans_list, str):
    #         return [ans_list]
    # if isinstance(data, list) and data:
    #     return [str(data[0])] if not isinstance(data[0], list) else [str(x) for x in data[0]]
    return []
