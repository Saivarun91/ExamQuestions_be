import re

DESCRIPTION_WORD_LIMIT = 50


def count_words(text):
    return len(re.findall(r"\S+", str(text or "").strip()))


def clamp_to_word_limit(text, limit=DESCRIPTION_WORD_LIMIT):
    parts = str(text or "").split()
    if len(parts) <= limit:
        return str(text or "")
    return " ".join(parts[:limit])
