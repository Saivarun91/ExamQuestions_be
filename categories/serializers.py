from rest_framework import serializers
from .models import Category
from django.utils.text import slugify


class CategorySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.CharField(required=True)
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

    def get_id(self, obj):
        return str(obj.id)

    def to_representation(self, instance):
        """Properly serialize MongoEngine document"""
        return {
            'id': str(instance.id),
            'name': instance.title,  # Frontend expects 'name'
            'title': instance.title,
            'description': instance.description or '',
            'content': instance.content or '',
            'faqs': getattr(instance, 'faqs', []) or [],
            'icon': instance.icon,
            'slug': instance.slug,
            'is_active': getattr(instance, 'is_active', True),
            'meta_title': instance.meta_title or '',
            'meta_keywords': instance.meta_keywords or '',
            'meta_description': instance.meta_description or '',
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
