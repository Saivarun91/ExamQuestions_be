from django.urls import path
from .views import (
    get_languages,
    get_language,
    create_language,
    update_language,
    delete_language,
    get_translations,
    get_translation,
    create_translation,
    update_translation,
    delete_translation,
    get_language_translations,
    get_site_translation_editor,
    bulk_save_site_translations,
    translate_runtime_texts,
)

urlpatterns = [

    path(
        "languages/",
        get_languages,
        name="get_languages"
    ),

    path(
        "languages/create/",
        create_language,
        name="create_language"
    ),

    path(
        "languages/update/<str:language_id>/",
        update_language,
        name="update_language"
    ),

    path(
        "languages/delete/<str:language_id>/",
        delete_language,
        name="delete_language"
    ),

    path(
        "languages/<str:language_id>/",
        get_language,
        name="get_language"
    ),

    path(
        "translations/",
        get_translations,
        name="get_translations"
    ),

    path(
        "translations/site-editor/<str:language_id>/",
        get_site_translation_editor,
        name="get_site_translation_editor"
    ),

    path(
        "translations/site-editor/<str:language_id>/save/",
        bulk_save_site_translations,
        name="bulk_save_site_translations"
    ),

    path(
        "translations/runtime/",
        translate_runtime_texts,
        name="translate_runtime_texts"
    ),

    path(
        "translations/language/<str:code>/",
        get_language_translations,
        name="get_language_translations"
    ),

    path(
        "translations/create/",
        create_translation,
        name="create_translation"
    ),

    path(
        "translations/update/<str:translation_id>/",
        update_translation,
        name="update_translation"
    ),

    path(
        "translations/delete/<str:translation_id>/",
        delete_translation,
        name="delete_translation"
    ),

    path(
        "translations/<str:translation_id>/",
        get_translation,
        name="get_translation"
    ),
]
