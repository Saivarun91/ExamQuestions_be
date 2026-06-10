from bson import ObjectId
import logging
import threading

from mongoengine.errors import NotUniqueError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Language, Translation
from .serializers import LanguageSerializer, TranslationSerializer
from .locale_templates import LOCALE_TEMPLATES
from .master_keys import MASTER_TRANSLATION_KEYS
from .site_ui_keys import SITE_UI_KEYS
from .cms_keys import get_cms_translation_keys
from .auto_fill import auto_fill_language_translations, auto_translate_runtime_text

logger = logging.getLogger(__name__)


def normalize_language_code(code):
    return (code or "").strip().lower()


def find_language_by_code(code, *, exclude_id=None):
    normalized = normalize_language_code(code)
    if not normalized:
        return None

    queryset = Language.objects(code__iexact=normalized)
    if exclude_id:
        try:
            queryset = queryset.filter(id__ne=ObjectId(str(exclude_id)))
        except Exception:
            pass

    return queryset.first()


def resolve_language_by_code(code):
    """Match stored admin language codes (zh-cn, chinese, zn, etc.)."""
    from .auto_translate import normalize_language_code as translate_code

    raw = (code or "").strip()
    if not raw:
        return None

    collapsed = raw.lower().replace("_", "-")
    language = Language.objects(code__iexact=collapsed, is_active=True).first()
    if language:
        return language

    target = translate_code(collapsed)
    for candidate in Language.objects(is_active=True):
        candidate_code = (candidate.code or "").lower().replace("_", "-")
        if not candidate_code:
            continue
        if candidate_code == collapsed:
            return candidate
        if translate_code(candidate_code) == target:
            return candidate
        if candidate_code.startswith(f"{collapsed}-") or collapsed.startswith(
            f"{candidate_code}-"
        ):
            return candidate

    return None


def duplicate_language_code_response(code):
    normalized = normalize_language_code(code)
    return Response(
        {
            "success": False,
            "message": f'A language with code "{normalized}" already exists.',
            "errors": {
                "code": ["This language code is already in use."],
            },
        },
        status=status.HTTP_409_CONFLICT,
    )


TRANSLATION_GROUP_LABELS = {
    "nav": "Navigation",
    "footer": "Footer",
    "home": "Home Page",
    "common": "Common UI",
    "auth": "Authentication",
    "cms": "CMS Content",
    "categories": "Categories",
    "providers": "Providers",
    "blog": "Blog",
    "testimonials": "Testimonials",
    "contact": "Contact",
    "legal": "Legal Pages",
    "profile": "Profile",
    "dashboard": "Dashboard",
    "exams": "Exams",
    "search": "Search",
    "breadcrumb": "Breadcrumbs",
    "pagination": "Pagination",
}


def get_all_translation_keys():
    cms_keys = get_cms_translation_keys()
    return {**MASTER_TRANSLATION_KEYS, **SITE_UI_KEYS, **cms_keys}


def get_translation_group(key):
    prefix = (key or "").split(".")[0]
    return prefix if prefix else "other"


def build_site_translation_editor(language):
    seed_language_translations(language)
    all_keys = get_all_translation_keys()
    auto_fill_language_translations(language, all_keys, resolve_template_value)
    saved = {
        item.key: item.value
        for item in Translation.objects(language=language)
    }

    grouped = {}
    for key in sorted(all_keys.keys()):
        english = all_keys.get(key) or ""
        group_id = get_translation_group(key)
        grouped.setdefault(group_id, []).append({
            "key": key,
            "english": english,
            "value": saved.get(key, english if language.code.lower() == "en" else ""),
        })

    groups = []
    for group_id in sorted(grouped.keys(), key=lambda g: (
        g not in TRANSLATION_GROUP_LABELS,
        TRANSLATION_GROUP_LABELS.get(g, g),
    )):
        groups.append({
            "id": group_id,
            "label": TRANSLATION_GROUP_LABELS.get(
                group_id,
                group_id.replace("_", " ").title(),
            ),
            "items": grouped[group_id],
        })

    return {
        "language": {
            "id": str(language.id),
            "name": language.name,
            "code": language.code,
        },
        "total_keys": len(all_keys),
        "groups": groups,
    }


def get_translation_group(key):
    prefix = (key or "").split(".")[0]
    return prefix if prefix else "other"


def is_cms_content_key(key):
    return (key or "").startswith("cms.")


def cleanup_stale_cms_translations(language, all_keys, existing):
    """Drop non-English CMS rows that only duplicate admin source English."""
    if language.code.lower() == "en":
        return

    for key, english_value in all_keys.items():
        if not is_cms_content_key(key):
            continue

        record = existing.get(key)
        if not record:
            continue

        if (record.value or "").strip() == (english_value or "").strip():
            record.delete()


def cleanup_stale_english_translations(language, all_keys, existing):
    """Drop non-English rows that still duplicate the English source text."""
    if language.code.lower() == "en":
        return

    for key, english_value in all_keys.items():
        record = existing.get(key)
        if not record:
            continue

        if (record.value or "").strip() == (english_value or "").strip():
            record.delete()


def seed_language_translations(language):
    code = language.code.lower()
    template = LOCALE_TEMPLATES.get(code, {})
    all_keys = get_all_translation_keys()

    existing = {
        item.key: item
        for item in Translation.objects(language=language)
    }

    cleanup_stale_cms_translations(language, all_keys, existing)

    existing = {
        item.key: item
        for item in Translation.objects(language=language)
    }

    cleanup_stale_english_translations(language, all_keys, existing)

    existing = {
        item.key: item
        for item in Translation.objects(language=language)
    }

    for key, english_value in all_keys.items():
        template_value = resolve_template_value(template, key)
        is_cms = is_cms_content_key(key)

        if key in existing:
            if template_value and code != "en" and not is_cms:
                record = existing[key]
                current = (record.value or "").strip()
                if not current or current == (english_value or "").strip():
                    record.value = template_value
                    record.save()
            continue

        if code != "en":
            if is_cms or not template_value:
                continue
            value = template_value
        else:
            value = template_value or english_value

        if not (value or "").strip():
            continue

        Translation(
            language=language,
            key=key,
            value=value,
        ).save()


CMS_KEY_ALIASES = {
    "cms.hero.title": "home.hero.title",
    "cms.hero.subtitle": "home.hero.subtitle",
    "cms.seo.heading": "home.seo.heading",
    "cms.categories.heading": "home.categories.heading",
    "cms.categories.subtitle": "home.categories.subtitle",
    "cms.featured.heading": "home.featured.heading",
    "cms.featured.subtitle": "home.featured.subtitle",
    "cms.value.heading": "home.value.heading",
    "cms.value.subtitle": "home.value.subtitle",
    "cms.blog.heading": "home.blog.heading",
    "cms.blog.subtitle": "home.blog.subtitle",
    "cms.testimonials.heading": "home.testimonials.heading",
    "cms.testimonials.subtitle": "home.testimonials.subtitle",
    "cms.faq.heading": "home.faq.heading",
    "cms.faq.subtitle": "home.faq.subtitle",
    "cms.faq.section.heading": "home.faq.section.heading",
    "cms.recent.heading": "home.recent.heading",
    "cms.recent.subtitle": "home.recent.subtitle",
    "cms.providers.heading": "home.providers.heading",
    "cms.providers.subtitle": "home.providers.subtitle",
    "cms.subscribe.title": "home.subscribe.title",
    "cms.subscribe.subtitle": "home.subscribe.subtitle",
    "cms.categories_page.hero_title": "categories.page.hero_title",
    "cms.categories_page.hero_subtitle": "categories.page.hero_subtitle",
    "cms.exams_page.hero_title": "exams.page.hero_title",
    "cms.exams_page.hero_subtitle": "exams.page.hero_subtitle",
    "cms.exams_page.page_heading": "common.all_popular_exams",
    "cms.providers_page.hero_title": "providers.page.hero_title",
    "cms.providers_page.hero_subtitle": "providers.page.hero_subtitle",
}

for stat_index in range(1, 7):
    CMS_KEY_ALIASES[f"cms.hero.stat{stat_index}.label"] = (
        f"home.hero.stat{stat_index}.label"
    )


def resolve_template_value(template, key):
    if key in template:
        return template[key]

    static_key = CMS_KEY_ALIASES.get(key)
    if static_key and static_key in template:
        return template[static_key]

    for cms_key, mapped_key in CMS_KEY_ALIASES.items():
        if mapped_key == key and cms_key in template:
            return template[cms_key]

    return None


def mirror_alias_keys(response_data):
    for cms_key, static_key in CMS_KEY_ALIASES.items():
        cms_value = response_data.get(cms_key)
        static_value = response_data.get(static_key)

        if cms_value and not static_value:
            response_data[static_key] = cms_value
        elif static_value and not cms_value:
            response_data[cms_key] = static_value


def sanitize_non_english_translations(response_data, all_keys, code):
    if code == "en":
        return response_data

    sanitized = {}
    for key, value in response_data.items():
        english = (all_keys.get(key) or "").strip()
        current = (value or "").strip()
        if english and current == english:
            continue
        sanitized[key] = value
    return sanitized


def get_cached_language_translations(language, *, lightweight=False):
    response_data = {
        item.key: item.value
        for item in Translation.objects(language=language)
    }

    mirror_alias_keys(response_data)

    code = language.code.lower()

    if code == "en":
        if lightweight:
            english_keys = {**MASTER_TRANSLATION_KEYS, **SITE_UI_KEYS}
        else:
            english_keys = get_all_translation_keys()
        for key, value in english_keys.items():
            response_data.setdefault(key, value)
    else:
        response_data = sanitize_non_english_translations(
            response_data, get_all_translation_keys(), code
        )

    return response_data


def _background_auto_fill(language_id):
    try:
        language = Language.objects.get(id=language_id)
        seed_language_translations(language)
        updated = auto_fill_language_translations(
            language,
            get_all_translation_keys(),
            resolve_template_value,
            max_updates=None,
        )
        logger.info(
            "Background translation fill completed for %s (%s keys)",
            language.code,
            updated,
        )
    except Exception as error:
        logger.warning("Background translation fill failed: %s", error)


def build_language_translations(language, fast=False):
    if fast:
        cached = get_cached_language_translations(language, lightweight=True)
        threading.Thread(
            target=_background_auto_fill,
            args=(language.id,),
            daemon=True,
        ).start()
        return cached

    seed_language_translations(language)
    all_keys = get_all_translation_keys()

    response_data = {
        item.key: item.value
        for item in Translation.objects(language=language)
    }

    mirror_alias_keys(response_data)

    code = language.code.lower()

    if code == "en":
        for key, value in all_keys.items():
            response_data.setdefault(key, value)
    else:
        response_data = sanitize_non_english_translations(
            response_data, all_keys, code
        )

    if code != "en":
        threading.Thread(
            target=_background_auto_fill,
            args=(language.id,),
            daemon=True,
        ).start()

    return response_data


# GET ALL
@api_view(["GET"])
def get_languages(request):
    languages = Language.objects()

    active_only = request.GET.get("active", "").lower() in ("1", "true", "yes")
    if active_only:
        languages = languages.filter(is_active=True)

    serializer = LanguageSerializer(
        languages,
        many=True
    )

    return Response({
        "success": True,
        "data": serializer.data
    })


# GET SINGLE
@api_view(["GET"])
def get_language(request, language_id):
    try:
        language = Language.objects.get(id=language_id)

        serializer = LanguageSerializer(language)

        return Response({
            "success": True,
            "data": serializer.data
        })

    except Language.DoesNotExist:
        return Response({
            "success": False,
            "message": "Language not found"
        }, status=status.HTTP_404_NOT_FOUND)


# CREATE
@api_view(["POST"])
def create_language(request):

    serializer = LanguageSerializer(
        data=request.data
    )

    if serializer.is_valid():
        code = normalize_language_code(serializer.validated_data["code"])

        if find_language_by_code(code):
            return duplicate_language_code_response(code)

        language = Language(
            name=serializer.validated_data["name"],
            code=code,
            is_active=serializer.validated_data.get(
                "is_active",
                True
            ),
            font_family=serializer.validated_data.get("font_family", ""),
        )

        try:
            language.save()
        except NotUniqueError:
            return duplicate_language_code_response(code)

        seed_language_translations(language)
        threading.Thread(
            target=_background_auto_fill,
            args=(language.id,),
            daemon=True,
        ).start()

        return Response({
            "success": True,
            "message": "Language created successfully",
            "id": str(language.id)
        }, status=status.HTTP_201_CREATED)

    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# UPDATE
@api_view(["PUT"])
def update_language(request, language_id):

    try:
        language = Language.objects.get(
            id=language_id
        )

    except Language.DoesNotExist:
        return Response({
            "success": False,
            "message": "Language not found"
        }, status=status.HTTP_404_NOT_FOUND)

    serializer = LanguageSerializer(
        data=request.data
    )

    if serializer.is_valid():
        code = normalize_language_code(serializer.validated_data["code"])

        if find_language_by_code(code, exclude_id=language_id):
            return duplicate_language_code_response(code)

        language.name = serializer.validated_data["name"]
        language.code = code
        language.is_active = serializer.validated_data.get(
            "is_active",
            language.is_active
        )
        if "font_family" in serializer.validated_data:
            language.font_family = serializer.validated_data.get(
                "font_family", ""
            )

        try:
            language.save()
        except NotUniqueError:
            return duplicate_language_code_response(code)

        seed_language_translations(language)
        threading.Thread(
            target=_background_auto_fill,
            args=(language.id,),
            daemon=True,
        ).start()

        return Response({
            "success": True,
            "message": "Language updated successfully"
        })

    return Response({
        "success": False,
        "errors": serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


# DELETE
@api_view(["DELETE"])
def delete_language(request, language_id):

    try:
        language = Language.objects.get(
            id=language_id
        )

        language.delete()

        return Response({
            "success": True,
            "message": "Language deleted successfully"
        })

    except Language.DoesNotExist:
        return Response({
            "success": False,
            "message": "Language not found"
        }, status=status.HTTP_404_NOT_FOUND)





# GET ALL TRANSLATIONS
@api_view(["GET"])
def get_translations(request):
    translations = Translation.objects()

    data = []

    for item in translations:
        data.append({
            "id": str(item.id),
            "language_id": str(item.language.id),
            "language_name": item.language.name,
            "language_code": item.language.code,
            "key": item.key,
            "value": item.value
        })

    return Response({
        "success": True,
        "data": data
    })


# GET SINGLE TRANSLATION
@api_view(["GET"])
def get_translation(request, translation_id):
    try:
        translation = Translation.objects.get(
            id=translation_id
        )

        return Response({
            "success": True,
            "data": {
                "id": str(translation.id),
                "language_id": str(translation.language.id),
                "key": translation.key,
                "value": translation.value
            }
        })

    except Translation.DoesNotExist:
        return Response({
            "success": False,
            "message": "Translation not found"
        }, status=status.HTTP_404_NOT_FOUND)


# CREATE TRANSLATION
@api_view(["POST"])
def create_translation(request):
    try:
        language = Language.objects.get(
            id=request.data.get("language")
        )

        translation = Translation(
            language=language,
            key=request.data.get("key"),
            value=request.data.get("value")
        )

        translation.save()

        return Response({
            "success": True,
            "message": "Translation created successfully",
            "id": str(translation.id)
        })

    except Language.DoesNotExist:
        return Response({
            "success": False,
            "message": "Language not found"
        }, status=status.HTTP_400_BAD_REQUEST)


# UPDATE TRANSLATION
@api_view(["PUT"])
def update_translation(request, translation_id):
    try:
        translation = Translation.objects.get(
            id=translation_id
        )

        language = Language.objects.get(
            id=request.data.get("language")
        )

        translation.language = language
        translation.key = request.data.get("key")
        translation.value = request.data.get("value")

        translation.save()

        return Response({
            "success": True,
            "message": "Translation updated successfully"
        })

    except Translation.DoesNotExist:
        return Response({
            "success": False,
            "message": "Translation not found"
        }, status=status.HTTP_404_NOT_FOUND)

    except Language.DoesNotExist:
        return Response({
            "success": False,
            "message": "Language not found"
        }, status=status.HTTP_400_BAD_REQUEST)


# DELETE TRANSLATION
@api_view(["DELETE"])
def delete_translation(request, translation_id):
    try:
        translation = Translation.objects.get(
            id=translation_id
        )

        translation.delete()

        return Response({
            "success": True,
            "message": "Translation deleted successfully"
        })

    except Translation.DoesNotExist:
        return Response({
            "success": False,
            "message": "Translation not found"
        }, status=status.HTTP_404_NOT_FOUND)


# RUNTIME AUTO-TRANSLATE (public site fallback)
@api_view(["POST"])
def translate_runtime_texts(request):
    target_lang = (request.data.get("target_lang") or "").lower().strip()
    source_lang = (request.data.get("source_lang") or "en").lower().strip()
    texts = request.data.get("texts")

    if not isinstance(texts, list):
        return Response(
            {"success": False, "message": "texts array is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not target_lang or target_lang == source_lang:
        return Response({"success": True, "translations": texts})

    from .auto_translate import translate_batch

    translations = translate_batch(texts, target_lang, source_lang)

    return Response({"success": True, "translations": translations})


# GET TRANSLATIONS BY LANGUAGE CODE
@api_view(["GET"])
def get_language_translations(request, code):
    if not (code or "").strip():
        return Response({})

    language = resolve_language_by_code(code)
    if not language:
        return Response({})

    fast = str(request.query_params.get("fast", "")).lower() in (
        "1",
        "true",
        "yes",
    )

    return Response(build_language_translations(language, fast=fast))


# WHOLE-SITE TRANSLATION EDITOR (admin)
@api_view(["GET"])
def get_site_translation_editor(request, language_id):
    try:
        language = Language.objects.get(id=language_id)
        payload = build_site_translation_editor(language)
        return Response({"success": True, **payload})
    except Language.DoesNotExist:
        return Response(
            {"success": False, "message": "Language not found"},
            status=status.HTTP_404_NOT_FOUND,
        )


@api_view(["POST"])
def bulk_save_site_translations(request, language_id):
    try:
        language = Language.objects.get(id=language_id)
    except Language.DoesNotExist:
        return Response(
            {"success": False, "message": "Language not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    incoming = request.data.get("translations")
    if not isinstance(incoming, dict):
        return Response(
            {"success": False, "message": "translations object is required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    all_keys = get_all_translation_keys()
    existing = {
        item.key: item
        for item in Translation.objects(language=language)
    }

    saved_count = 0
    removed_count = 0

    for key in all_keys.keys():
        if key not in incoming:
            continue

        value = (incoming.get(key) or "").strip()

        if key in existing:
            record = existing[key]
            if not value:
                record.delete()
                removed_count += 1
            elif record.value != value:
                record.value = value
                record.source_text = (all_keys.get(key) or "").strip()
                record.is_manual = True
                record.save()
                saved_count += 1
        elif value:
            english_source = (all_keys.get(key) or "").strip()
            Translation(
                language=language,
                key=key,
                value=value,
                source_text=english_source,
                is_manual=True,
            ).save()
            saved_count += 1

    return Response({
        "success": True,
        "message": "Site translations saved successfully",
        "saved_count": saved_count,
        "removed_count": removed_count,
    })