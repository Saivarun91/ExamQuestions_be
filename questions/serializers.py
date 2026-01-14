from rest_framework import serializers
from .models import Question, CraftsmanQuestion


class QuestionSerializer(serializers.Serializer):
    """
    Serializer for both Question and CraftsmanQuestion models.
    Works with both models since they share the same field structure.
    """
    id = serializers.CharField(read_only=True)
    course_id = serializers.CharField(required=True)
    question_text = serializers.CharField(required=True)
    question_type = serializers.CharField(required=True)
    options = serializers.ListField(child=serializers.DictField(), required=True)
    correct_answers = serializers.ListField(child=serializers.CharField(), required=True)
    explanation = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    question_image = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    marks = serializers.IntegerField(required=False, default=1)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    
    def to_representation(self, instance):
        # Get status field (proper field in CraftsmanQuestion, dynamic in Question)
        status = getattr(instance, 'status', None)
        
        return {
            'id': str(instance.id),
            'course_id': str(instance.course.id) if instance.course else None,
            'question_text': instance.question_text,
            'question_type': instance.question_type,
            'options': instance.options or [],
            'correct_answers': instance.correct_answers or [],
            'explanation': instance.explanation or '',
            'question_image': instance.question_image or None,
            'marks': instance.marks or 1,
            'tags': instance.tags or [],
            'status': status,  # Status field (proper in CraftsmanQuestion, dynamic in Question)
            'created_at': instance.created_at.isoformat() if instance.created_at else None,
            'updated_at': instance.updated_at.isoformat() if instance.updated_at else None,
        }

