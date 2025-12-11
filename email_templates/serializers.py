from rest_framework import serializers
from .models import EmailTemplate

class EmailTemplateSerializer(serializers.Serializer):
    """Serializer for EmailTemplate model"""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True)
    subject = serializers.CharField(required=True)
    body = serializers.CharField(required=True)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_active = serializers.BooleanField(required=False, default=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def to_representation(self, instance):
        """Custom representation to handle MongoDB ObjectId"""
        return {
            "id": str(instance.id),
            "name": getattr(instance, "name", ""),
            "subject": getattr(instance, "subject", ""),
            "body": getattr(instance, "body", ""),
            "description": getattr(instance, "description", ""),
            "is_active": bool(getattr(instance, "is_active", True)),
            "created_at": instance.created_at.isoformat() if hasattr(instance, "created_at") and instance.created_at else None,
            "updated_at": instance.updated_at.isoformat() if hasattr(instance, "updated_at") and instance.updated_at else None,
        }
    
    def create(self, validated_data):
        """Create a new EmailTemplate instance"""
        return EmailTemplate.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update an existing EmailTemplate instance"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

