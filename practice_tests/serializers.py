from rest_framework import serializers
from .models import PracticeTest


class PracticeTestSerializer(serializers.Serializer):
    """Custom serializer for MongoEngine PracticeTest model"""
    id = serializers.SerializerMethodField()
    slug = serializers.CharField()
    title = serializers.CharField()
    questions = serializers.IntegerField(default=0)
    duration = serializers.IntegerField(default=0)
    avg_score = serializers.FloatField(default=0.0)
    attempts = serializers.IntegerField(default=0)
    enrolled_count = serializers.IntegerField(default=0)
    free_trial_questions = serializers.IntegerField(default=10)
    
    # Test detail fields
    overview = serializers.CharField(allow_blank=True, required=False)
    instructions = serializers.CharField(allow_blank=True, required=False)
    test_format = serializers.CharField(allow_blank=True, required=False)
    duration_info = serializers.CharField(allow_blank=True, required=False)
    total_questions_info = serializers.CharField(allow_blank=True, required=False)
    language = serializers.CharField(default="English", required=False)
    difficulty_level = serializers.CharField(default="Medium", required=False)
    test_type = serializers.CharField(default="Practice Test", required=False)
    additional_info = serializers.CharField(allow_blank=True, required=False)
    
    # SEO fields
    meta_title = serializers.CharField(allow_blank=True, required=False)
    meta_keywords = serializers.CharField(allow_blank=True, required=False)
    meta_description = serializers.CharField(allow_blank=True, required=False)
    
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    category = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()

    def get_id(self, obj):
        return str(obj.id)

    def get_category(self, obj):
        try:
            if obj.category:
                return {
                    "id": str(obj.category.id),
                    "name": obj.category.name,
                }
        except:
            pass
        return None

    def get_course(self, obj):
        try:
            if obj.course:
                return {
                    "id": str(obj.course.id),
                    "name": obj.course.name,
                }
        except:
            pass
        return None

    def create(self, validated_data):
        return PracticeTest(**validated_data).save()

    def update(self, instance, validated_data):
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance
