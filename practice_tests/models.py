from mongoengine import Document, StringField, IntField, FloatField, DateTimeField, ReferenceField
import datetime
from categories.models import Category  # adjust import path as needed


class PracticeTest(Document):
    slug = StringField(required=True)  # Not globally unique - unique per course/category
    title = StringField(required=True)
    category = ReferenceField(Category, required=False)  # Keep for backward compatibility
    course = ReferenceField('courses.Course', required=True)  # Required: Link to course (string reference to avoid circular import)
    questions = IntField(default=0)
    duration = IntField(default=0)
    avg_score = FloatField(default=0.0)
    attempts = IntField(default=0)
    enrolled_count = IntField(default=0)
    free_trial_questions = IntField(default=10)  # Number of questions to show in free trial
    
    # Test detail fields (admin-managed)
    overview = StringField(required=False, default="")
    instructions = StringField(required=False, default="")
    test_format = StringField(required=False, default="")
    duration_info = StringField(required=False, default="")
    total_questions_info = StringField(required=False, default="")
    language = StringField(required=False, default="English")
    difficulty_level = StringField(required=False, default="Medium")
    test_type = StringField(required=False, default="Practice Test")
    additional_info = StringField(required=False, default="")
    
    # Meta tags for SEO
    meta_title = StringField(required=False, default="")
    meta_keywords = StringField(required=False, default="")
    meta_description = StringField(required=False, default="")
    
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "practice_tests",
        "indexes": [
            # Composite index to ensure slug is unique per course
            [("slug", 1), ("course", 1)],
            # Composite index to ensure slug is unique per category (for backward compatibility)
            [("slug", 1), ("category", 1)],
        ]
    }
