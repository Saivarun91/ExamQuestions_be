from rest_framework import serializers
from .models import Course
import datetime

class CourseSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    provider = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    code = serializers.CharField(required=False)
    slug = serializers.CharField(required=False)
    practice_exams = serializers.IntegerField(required=False)
    questions = serializers.IntegerField(required=False)
    badge = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    category = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # Pricing fields
    actual_price = serializers.FloatField(required=False, allow_null=True)
    offer_price = serializers.FloatField(required=False, allow_null=True)
    currency = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_featured = serializers.BooleanField(required=False)

    # Exam details fields
    short_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    about = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    eligibility = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    exam_pattern = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    pass_rate = serializers.IntegerField(required=False, allow_null=True)
    rating = serializers.FloatField(required=False, allow_null=True)
    difficulty = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    duration = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    passing_score = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    whats_included = serializers.ListField(child=serializers.CharField(), required=False)
    why_matters = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    topics = serializers.ListField(child=serializers.DictField(), required=False)
    practice_tests_list = serializers.ListField(child=serializers.DictField(), required=False)  # For backward compatibility in API
    testimonials = serializers.ListField(child=serializers.DictField(), required=False)
    faqs = serializers.ListField(child=serializers.DictField(), required=False)
    test_instructions = serializers.ListField(child=serializers.CharField(), required=False)
    test_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    
    # Pricing fields
    pricing_plans = serializers.ListField(child=serializers.DictField(), required=False)
    pricing_features = serializers.ListField(child=serializers.DictField(), required=False)
    pricing_testimonials = serializers.ListField(child=serializers.DictField(), required=False)
    pricing_faqs = serializers.ListField(child=serializers.DictField(), required=False)
    pricing_comparison = serializers.ListField(child=serializers.DictField(), required=False)

    # SEO fields
    meta_title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_keywords = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    meta_description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    is_active = serializers.BooleanField(required=False)

    def to_representation(self, instance):
        """Custom serialization to handle missing fields gracefully."""
        # Handle provider - get provider.name if it's a ReferenceField
        provider_value = getattr(instance, 'provider', None)
        if provider_value:
            # If it's a ReferenceField object, get the name attribute
            if hasattr(provider_value, 'name'):
                provider_value = provider_value.name
            else:
                provider_value = str(provider_value)
        else:
            provider_value = ''
        
        # Handle category - get category.title and slug if it's a ReferenceField
        category_value = getattr(instance, 'category', None)
        category_slug = None
        if category_value:
            # If it's a ReferenceField object, get the title and slug attributes
            if hasattr(category_value, 'slug'):
                category_slug = category_value.slug
            if hasattr(category_value, 'title'):
                category_value = category_value.title
            elif hasattr(category_value, 'id'):
                category_value = str(category_value.id)
            else:
                category_value = str(category_value)
        else:
            category_value = None

        return {
            'id': str(instance.id),
            'provider': provider_value,
            'title': getattr(instance, 'title', getattr(instance, 'name', '')),
            'code': getattr(instance, 'code', ''),
            'slug': getattr(instance, 'slug', ''),
            'practice_exams': getattr(instance, 'practice_exams', 0),
            'questions': getattr(instance, 'questions', 0),
            'badge': getattr(instance, 'badge', None),
            'category': category_value,
            'category_slug': category_slug,
            
            # Exam details fields
            'short_description': getattr(instance, 'short_description', None),
            'about': getattr(instance, 'about', None),
            'eligibility': getattr(instance, 'eligibility', None),
            'exam_pattern': getattr(instance, 'exam_pattern', None),
            'pass_rate': getattr(instance, 'pass_rate', None),
            'rating': getattr(instance, 'rating', None),
            'difficulty': getattr(instance, 'difficulty', None),
            'duration': getattr(instance, 'duration', None),
            'passing_score': getattr(instance, 'passing_score', None),
            'whats_included': getattr(instance, 'whats_included', []),
            'why_matters': getattr(instance, 'why_matters', None),
            'topics': getattr(instance, 'topics', []),
            # Convert practice_tests references to list format for API compatibility
            'practice_tests_list': self._serialize_practice_tests(instance),
            'testimonials': getattr(instance, 'testimonials', []),
            'faqs': getattr(instance, 'faqs', []),
            'test_instructions': getattr(instance, 'test_instructions', []),
            'test_description': getattr(instance, 'test_description', None),
            
            # Pricing fields
            'pricing_plans': getattr(instance, 'pricing_plans', []),
            'pricing_features': getattr(instance, 'pricing_features', []),
            'pricing_testimonials': getattr(instance, 'pricing_testimonials', []),
            'pricing_faqs': getattr(instance, 'pricing_faqs', []),
            'pricing_comparison': getattr(instance, 'pricing_comparison', []),
            
            # SEO fields
            'meta_title': getattr(instance, 'meta_title', None),
            'meta_keywords': getattr(instance, 'meta_keywords', None),
            'meta_description': getattr(instance, 'meta_description', None),
            'is_active': getattr(instance, 'is_active', True),
        }

    def _serialize_practice_tests(self, instance):
        """Convert practice_tests references to list format for API."""
        practice_tests_list = []
        seen_ids = set()  # Track seen practice test IDs to avoid duplicates
        try:
            # Get practice_tests from reference field
            practice_tests = getattr(instance, 'practice_tests', [])
            for pt in practice_tests:
                if pt:  # Check if reference is not None
                    pt_id = str(pt.id)
                    # Skip if we've already seen this practice test
                    if pt_id in seen_ids:
                        continue
                    seen_ids.add(pt_id)
                    practice_tests_list.append({
                        'id': pt_id,
                        'name': getattr(pt, 'title', ''),
                        'title': getattr(pt, 'title', ''),
                        'description': getattr(pt, 'overview', ''),
                        'questions': getattr(pt, 'questions', 0),
                        'difficulty': getattr(pt, 'difficulty_level', 'Intermediate'),
                        'duration': str(getattr(pt, 'duration', 0)),
                    })
        except Exception as e:
            # Fallback to old practice_tests_list if references fail
            practice_tests_list = getattr(instance, 'practice_tests_list', [])
            # Also deduplicate the fallback list
            if practice_tests_list:
                seen_ids = set()
                deduplicated_list = []
                for pt in practice_tests_list:
                    pt_id = pt.get('id') or pt.get('_id') or str(hash(str(pt)))
                    if pt_id not in seen_ids:
                        seen_ids.add(pt_id)
                        deduplicated_list.append(pt)
                practice_tests_list = deduplicated_list
        return practice_tests_list

    def create(self, validated_data):
        return Course(**validated_data).save()

    def update(self, instance, validated_data):
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.updated_at = datetime.datetime.utcnow()
        instance.save()
        return instance
 