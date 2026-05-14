from rest_framework import serializers
from .models import Category
from django.utils.text import slugify

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
    description = serializers.CharField(required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    faqs = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    icon = serializers.CharField(required=True)
    slug = serializers.CharField(read_only=True)
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_top_certification = serializers.BooleanField(required=False, default=False)
    hero_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    hero_subtitle = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def get_id(self, obj):
        return str(obj.id)

    def to_representation(self, instance):
        """Properly serialize MongoEngine document"""
        return {
            'id': str(instance.id),
            'name': instance.title,  # Frontend expects 'name'
            'title': instance.title,
            'main_category': getattr(instance, 'main_category', '') or '',
            'description': instance.description or '',
            'content': instance.content or '',
            'faqs': getattr(instance, 'faqs', []) or [],
            'icon': instance.icon,
            'slug': instance.slug,
            'is_active': getattr(instance, 'is_active', True),
            'meta_title': instance.meta_title or '',
            'meta_keywords': instance.meta_keywords or '',
            'meta_description': instance.meta_description or '',
            'is_top_certification': _to_bool(getattr(instance, 'is_top_certification', False)),
            'hero_title': getattr(instance, 'hero_title', '') or '',
            'hero_subtitle': getattr(instance, 'hero_subtitle', '') or '',
        }

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
