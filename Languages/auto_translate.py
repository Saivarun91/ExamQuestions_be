import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

logger = logging.getLogger(__name__)

GOOGLE_TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"

LANGUAGE_CODE_MAP = {
    "zn": "zh-CN",
    "zh": "zh-CN",
    "zh-cn": "zh-CN",
    "zh-tw": "zh-TW",
    "cn": "zh-CN",
    "chinese": "zh-CN",
    "mandarin": "zh-CN",
    "hindi": "hi",
    "hi": "hi",
    "tamil": "ta",
    "ta": "ta",
    "telugu": "te",
    "te": "te",
    "bengali": "bn",
    "bn": "bn",
    "marathi": "mr",
    "mr": "mr",
    "gujarati": "gu",
    "gu": "gu",
    "kannada": "kn",
    "kn": "kn",
    "malayalam": "ml",
    "ml": "ml",
    "punjabi": "pa",
    "pa": "pa",
    "urdu": "ur",
    "ur": "ur",
    "japanese": "ja",
    "ja": "ja",
    "korean": "ko",
    "ko": "ko",
    "arabic": "ar",
    "ar": "ar",
    "spanish": "es",
    "es": "es",
    "french": "fr",
    "fr": "fr",
    "german": "de",
    "de": "de",
    "portuguese": "pt",
    "pt": "pt",
    "pt-br": "pt",
    "italian": "it",
    "it": "it",
    "russian": "ru",
    "ru": "ru",
    "he": "iw",
    "jw": "jv",
    "indonesian": "id",
    "in": "id",
    "norwegian": "no",
    "nb": "no",
    "no": "no",
}


def normalize_language_code(code):
    normalized = (code or "en").lower().strip().replace("_", "-")
    if not normalized:
        return "en"
    return LANGUAGE_CODE_MAP.get(normalized, normalized.split("-")[0])


def translate_text(text, target_lang, source_lang="en"):
    source = normalize_language_code(source_lang)
    target = normalize_language_code(target_lang)
    value = (text or "").strip()

    if not value or source == target:
        return value

    params = {
        "client": "gtx",
        "sl": source,
        "tl": target,
        "dt": "t",
        "q": value,
    }

    try:
        response = requests.get(
            GOOGLE_TRANSLATE_URL,
            params=params,
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()

        if payload and payload[0]:
            parts = [
                chunk[0]
                for chunk in payload[0]
                if isinstance(chunk, (list, tuple)) and chunk and chunk[0]
            ]
            translated = "".join(parts).strip()
            if translated:
                return translated
    except Exception as error:
        logger.warning(
            "Translation failed (%s -> %s): %s",
            source,
            target,
            error,
        )

    return value


def translate_batch(texts, target_lang, source_lang="en", max_workers=4):
    items = list(texts or [])
    if not items:
        return []

    target = normalize_language_code(target_lang)
    source = normalize_language_code(source_lang)

    if source == target:
        return items

    if len(items) == 1:
        return [translate_text(items[0], target, source)]

    results = [None] * len(items)

    def _translate_index(index_text):
        index, text = index_text
        if index > 0:
            time.sleep(0.05)
        return index, translate_text(text, target, source)

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(_translate_index, (index, text))
                for index, text in enumerate(items)
            ]

            for future in as_completed(futures):
                try:
                    index, translated = future.result()
                    results[index] = translated
                except Exception as error:
                    logger.warning("Batch translation worker failed: %s", error)
    except RuntimeError as error:
        logger.warning("Parallel translation unavailable, falling back: %s", error)
        for index, text in enumerate(items):
            results[index] = translate_text(text, target, source)

    return [
        (result or "").strip()
        for index, result in enumerate(results)
    ]
