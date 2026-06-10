from .auto_translate import translate_batch, translate_text
from .cms_keys import get_cms_translation_keys
from .locale_templates import LOCALE_TEMPLATES
from .models import Translation


def is_cms_content_key(key):
    return (key or "").startswith("cms.")


def upsert_auto_translation(language, key, value, source_text):
    if not (value or "").strip():
        return

    record = Translation.objects(language=language, key=key).first()
    if record and getattr(record, "is_manual", False):
        return

    if record:
        record.value = value
        record.source_text = source_text or ""
        record.is_manual = False
        record.save()
        return

    Translation(
        language=language,
        key=key,
        value=value,
        source_text=source_text or "",
        is_manual=False,
    ).save()


def translation_needs_refresh(record, english):
    english = (english or "").strip()
    if not english:
        return False
    if not record:
        return True
    if getattr(record, "is_manual", False):
        return False

    current = (record.value or "").strip()
    if not current:
        return True
    if current == english:
        return True

    stored_source = (getattr(record, "source_text", None) or "").strip()
    if stored_source and stored_source != english:
        return True
    if not stored_source and is_cms_content_key(record.key):
        return True

    return False


def auto_fill_language_translations(
    language, all_keys, resolve_template_value, max_updates=None
):
    code = (language.code or "en").lower()
    if code == "en":
        return 0

    template = LOCALE_TEMPLATES.get(code, {})
    existing = {
        item.key: item
        for item in Translation.objects(language=language)
    }

    template_updates = []
    machine_queue = []

    for key, english_value in all_keys.items():
        english = (english_value or "").strip()
        if not english:
            continue

        record = existing.get(key)
        if record and not translation_needs_refresh(record, english):
            continue

        template_value = resolve_template_value(template, key)
        if template_value and not is_cms_content_key(key):
            template_updates.append((key, template_value, english))
            continue

        machine_queue.append((key, english))

    updated_count = 0

    for key, value, source_text in template_updates:
        if max_updates is not None and updated_count >= max_updates:
            break
        upsert_auto_translation(language, key, value, source_text)
        updated_count += 1

    for chunk_start in range(0, len(machine_queue), 30):
        if max_updates is not None and updated_count >= max_updates:
            break

        chunk = machine_queue[chunk_start : chunk_start + 30]
        translated_values = translate_batch(
            [english for _, english in chunk],
            target_lang=code,
            source_lang="en",
        )

        for (key, english), translated in zip(chunk, translated_values):
            if max_updates is not None and updated_count >= max_updates:
                break

            final_value = (translated or "").strip()
            if not final_value or final_value == english:
                continue

            upsert_auto_translation(language, key, final_value, english)
            updated_count += 1

    return updated_count


def auto_translate_runtime_text(text, target_lang, source_lang="en"):
    return translate_text(text, target_lang, source_lang)
