from rest_framework import serializers
from .models import Language, Translation

class LanguageSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    name = serializers.CharField()
    code = serializers.CharField()
    is_active = serializers.BooleanField()
    font_family = serializers.CharField(required=False, allow_blank=True)

    def get_id(self, obj):
        return str(obj.id)
class TranslationSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    language = serializers.CharField()
    key = serializers.CharField()
    value = serializers.CharField()