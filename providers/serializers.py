from rest_framework import serializers
from common.text_limits import clamp_to_word_limit

class ProviderSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True)
    icon = serializers.CharField(required=True)
    slug = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=2000)
    website_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    logo_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    page_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    faqs = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True,
    )
    order = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)
    show_in_popular_providers = serializers.BooleanField(required=False)

    def validate_description(self, value):
        return clamp_to_word_limit(value)

    def to_representation(self, instance):
        """Convert ObjectId to string for JSON serialization"""
        if self.context.get("lite"):
            return self._lite_representation(instance)
        return self._full_representation(instance)

    def _lite_representation(self, instance):
        logo_url = self._resolve_logo_url(instance)
        return {
            "id": str(instance.id),
            "name": instance.name,
            "icon": instance.icon,
            "slug": instance.slug,
            "description": self._get_dynamic(instance, "description", None),
            "website_url": self._get_dynamic(instance, "website_url", None),
            "logo_url": logo_url,
            "order": getattr(instance, "order", 0),
            "is_active": getattr(instance, "is_active", True),
            "show_in_popular_providers": self._get_dynamic(
                instance, "show_in_popular_providers", True
            ),
        }

    def _get_dynamic(self, instance, field, default=None):
        value = getattr(instance, field, default)
        if value is not None:
            return value
        try:
            if (
                hasattr(instance, "_data")
                and instance._data is not None
                and field in instance._data
            ):
                return instance._data.get(field, default)
        except Exception:
            pass
        return default

    def _resolve_logo_url(self, instance):
        if hasattr(instance, "logo_url") and instance.logo_url:
            return instance.logo_url
        if hasattr(instance, "logo") and instance.logo:
            request = self.context.get("request", None)
            if request:
                return f"{request.scheme}://{request.get_host()}/api/providers/{str(instance.id)}/logo/"
            return f"/api/providers/{str(instance.id)}/logo/"
        return None

    def _full_representation(self, instance):
        logo_url = self._resolve_logo_url(instance)
        return {
            'id': str(instance.id),
            'name': instance.name,
            'icon': instance.icon,
            'slug': instance.slug,
            'description': self._get_dynamic(instance, 'description', None),
            'website_url': self._get_dynamic(instance, 'website_url', None),
            'logo_url': logo_url,
            'meta_title': getattr(instance, 'meta_title', None),
            'meta_keywords': getattr(instance, 'meta_keywords', None),
            'meta_description': getattr(instance, 'meta_description', None),
            'page_title': self._get_dynamic(instance, 'page_title', ""),
            'content': self._get_dynamic(instance, 'content', ""),
            'faqs': self._get_dynamic(instance, 'faqs', []) or [],
            'order': getattr(instance, 'order', 0),
            'is_active': getattr(instance, 'is_active', True),
            'show_in_popular_providers': self._get_dynamic(
                instance, 'show_in_popular_providers', True
            ),
        }

    def create(self, validated_data):
        from .models import Provider
        provider = Provider(**validated_data)
        provider.save()
        return provider

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.icon = validated_data.get("icon", instance.icon)
        instance.slug = validated_data.get("slug", instance.slug)
        instance.description = validated_data.get("description", getattr(instance, "description", ""))
        instance.website_url = validated_data.get("website_url", getattr(instance, "website_url", ""))
        instance.logo_url = validated_data.get("logo_url", instance.logo_url)
        instance.meta_title = validated_data.get("meta_title", instance.meta_title)
        instance.meta_keywords = validated_data.get("meta_keywords", instance.meta_keywords)
        instance.meta_description = validated_data.get("meta_description", instance.meta_description)
        instance.page_title = validated_data.get("page_title", getattr(instance, "page_title", ""))
        instance.content = validated_data.get("content", getattr(instance, "content", ""))
        instance.faqs = validated_data.get("faqs", getattr(instance, "faqs", []))
        instance.order = validated_data.get("order", instance.order)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.show_in_popular_providers = validated_data.get(
            "show_in_popular_providers",
            getattr(instance, "show_in_popular_providers", False),
        )
        instance.save()
        return instance
