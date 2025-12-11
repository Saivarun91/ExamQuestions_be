from rest_framework import serializers

class ProviderSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True)
    icon = serializers.CharField(required=True)
    slug = serializers.CharField(required=False)
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    order = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)

    def to_representation(self, instance):
        """Convert ObjectId to string for JSON serialization"""
        # Build logo URL if logo exists
        logo_url = None
        if hasattr(instance, 'logo') and instance.logo:
            request = self.context.get('request', None)
            if request:
                logo_url = f"{request.scheme}://{request.get_host()}/api/providers/{str(instance.id)}/logo/"
            else:
                logo_url = f"/api/providers/{str(instance.id)}/logo/"
        
        return {
            'id': str(instance.id),
            'name': instance.name,
            'icon': instance.icon,
            'slug': instance.slug,
            'logo_url': logo_url,
            'meta_title': getattr(instance, 'meta_title', None),
            'meta_keywords': getattr(instance, 'meta_keywords', None),
            'meta_description': getattr(instance, 'meta_description', None),
            'order': getattr(instance, 'order', 0),
            'is_active': getattr(instance, 'is_active', True),
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
        instance.meta_title = validated_data.get("meta_title", instance.meta_title)
        instance.meta_keywords = validated_data.get("meta_keywords", instance.meta_keywords)
        instance.meta_description = validated_data.get("meta_description", instance.meta_description)
        instance.order = validated_data.get("order", instance.order)
        instance.is_active = validated_data.get("is_active", instance.is_active)
        instance.save()
        return instance
