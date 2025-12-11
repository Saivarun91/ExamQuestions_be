from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    title = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True)
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
            'icon': instance.icon,
            'slug': instance.slug,
            'is_active': getattr(instance, 'is_active', True),
            'meta_title': instance.meta_title or '',
            'meta_keywords': instance.meta_keywords or '',
            'meta_description': instance.meta_description or '',
        }

    def create(self, validated_data):
        category = Category(**validated_data)
        category.save()
        return category

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
