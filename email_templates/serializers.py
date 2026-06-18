from rest_framework import serializers
from .models import EmailTemplate
from .utils import get_template_body_content, template_has_uploaded_file, get_template_file_kind


class EmailTemplateSerializer(serializers.Serializer):
    """Serializer for EmailTemplate model"""
    id = serializers.CharField(read_only=True)
    name = serializers.CharField(required=True)
    subject = serializers.CharField(required=True)
    body = serializers.CharField(required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    extra_fields = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)
    has_template_file = serializers.BooleanField(read_only=True)
    template_filename = serializers.CharField(read_only=True, allow_null=True)
    template_file_type = serializers.CharField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    def validate(self, attrs):
        body = (attrs.get("body") or "").strip()
        has_file = self.context.get("has_template_file", False)
        incoming_file = self.context.get("incoming_template_file", False)
        if not body and not has_file and not incoming_file:
            raise serializers.ValidationError(
                {"body": "Provide email body text or upload a template file (HTML, image, PDF, or any document)."}
            )
        return attrs

    def to_representation(self, instance):
        """Custom representation to handle MongoDB ObjectId"""
        has_file = template_has_uploaded_file(instance)
        filename = None
        if has_file and getattr(instance, "template_file", None):
            filename = getattr(instance.template_file, "filename", None) or getattr(
                instance.template_file, "name", None
            )

        file_kind = get_template_file_kind(instance) if has_file else None
        manual_body = getattr(instance, "body", "") or ""

        if has_file and file_kind == "text":
            body_display = get_template_body_content(instance)
        else:
            body_display = manual_body

        return {
            "id": str(instance.id),
            "name": getattr(instance, "name", ""),
            "subject": getattr(instance, "subject", ""),
            "body": body_display,
            "description": getattr(instance, "description", ""),
            "extra_fields": getattr(instance, "extra_fields", "") or "",
            "is_active": bool(getattr(instance, "is_active", True)),
            "has_template_file": has_file,
            "template_filename": filename,
            "template_file_type": file_kind,
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
