import os
import re
from urllib.parse import urlparse

from rest_framework import serializers
from .models import Category
from django.utils.text import slugify

_CATEGORY_IMAGE_PATH_RE = re.compile(
    r"^/api/categories/([a-fA-F0-9]{24})/image/?$", re.IGNORECASE
)


def _api_base():
    return (
        os.environ.get("PUBLIC_API_BASE_URL")
        or os.environ.get("API_BASE_URL")
        or ""
    ).rstrip("/")


def _category_image_serve_url(category_id, request=None):
    api_base = _api_base()
    if api_base:
        return f"{api_base}/api/categories/{category_id}/image/"
    if request:
        return (
            f"{request.scheme}://{request.get_host()}"
            f"/api/categories/{category_id}/image/"
        )
    return f"/api/categories/{category_id}/image/"


def _category_image_url(instance, request=None):
    """Return absolute image URL for API clients and Next.js."""
    category_id = str(instance.id)

    if hasattr(instance, "image") and instance.image:
        return _category_image_serve_url(category_id, request=request)

    image_url = getattr(instance, "image_url", None) or ""
    trimmed = str(image_url).strip()
    if not trimmed:
        return ""

    path = trimmed
    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        try:
            path = urlparse(trimmed).path or trimmed
        except Exception:
            path = trimmed

    if path.startswith("/"):
        match = _CATEGORY_IMAGE_PATH_RE.match(path)
        if match:
            return _category_image_serve_url(match.group(1), request=request)

    if trimmed.startswith("http://") or trimmed.startswith("https://"):
        return trimmed

    api_base = _api_base()
    if api_base and trimmed.startswith("/"):
        return f"{api_base}{trimmed}"
    if request:
        return f"{request.scheme}://{request.get_host()}{trimmed}"
    return trimmed


def _category_title_taken(title, exclude_id=None):
    normalized = (title or "").strip()
    if not normalized:
        return False
    existing = Category.objects(title__iexact=normalized).first()
    if not existing:
        return False
    if exclude_id and str(existing.id) == str(exclude_id):
        return False
    return True

def _to_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "y", "on"}
    return bool(value)


class CategorySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.CharField(required=True)
    main_category = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True, max_length=50)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    faqs = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    icon = serializers.CharField(required=True)
    image_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    slug = serializers.CharField(read_only=True)
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_top_certification = serializers.BooleanField(required=False, default=False)
    page_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hero_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hero_subtitle = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def get_id(self, obj):
        return str(obj.id)

    def to_representation(self, instance):
        """Properly serialize MongoEngine document"""
        request = self.context.get("request")
        image_url = _category_image_url(instance, request=request)

        return {
            'id': str(instance.id),
            'name': instance.title,  # Frontend expects 'name'
            'title': instance.title,
            'main_category': getattr(instance, 'main_category', '') or '',
            'description': instance.description or '',
            'content': instance.content or '',
            'faqs': getattr(instance, 'faqs', []) or [],
            'icon': instance.icon,
            'image_url': image_url,
            'slug': instance.slug,
            'is_active': getattr(instance, 'is_active', True),
            'meta_title': instance.meta_title or '',
            'meta_keywords': instance.meta_keywords or '',
            'meta_description': instance.meta_description or '',
            'is_top_certification': _to_bool(getattr(instance, 'is_top_certification', False)),
            'page_title': getattr(instance, 'page_title', '') or '',
            'hero_title': getattr(instance, 'hero_title', '') or '',
            'hero_subtitle': getattr(instance, 'hero_subtitle', '') or '',
        }

    def validate_title(self, value):
        title = (value or "").strip()
        if not title:
            raise serializers.ValidationError("Category title is required.")
        exclude_id = getattr(self.instance, "id", None) if self.instance else None
        if _category_title_taken(title, exclude_id=exclude_id):
            raise serializers.ValidationError("This category already exists.")
        return title

    def validate_description(self, value):
        return str(value or "")[:50]

    def create(self, validated_data):
        # Generate slug from title if not provided
        title = validated_data.get('title', '')
        if title and 'slug' not in validated_data:
            base_slug = slugify(title)
            slug = base_slug
            # Ensure slug is unique
            counter = 1
            while Category.objects(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data['slug'] = slug
        category = Category(**validated_data)
        category.save()
        return category

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def validate_faqs(self, value):
        if value in (None, ""):
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError("FAQs must be a list.")

        cleaned = []
        for item in value:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if question and answer:
                cleaned.append({"question": question, "answer": answer})
        return cleaned
