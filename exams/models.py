from mongoengine import (
    Document, StringField, IntField, ListField, ReferenceField, DictField, DateTimeField,
    FloatField, BooleanField, ObjectIdField, FileField
)
from datetime import datetime
from users.models import User
from bson import ObjectId

# -------------------------------
# MODELS
# -------------------------------

class Question(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    category = ReferenceField("practice_tests.PracticeTest", required=True)  # <-- string reference
    question_text = StringField(required=False)  # Optional - can be empty if question_image is provided
    question_image = FileField(required=False)  # Optional - can be empty if question_text is provided
    question_type = StringField(choices=['MCQ', 'SINGLE', 'TRUE_FALSE'], required=True)
    # Options can be strings (text) or dicts with 'text' and/or 'image_url'
    options = ListField(DictField())  # Changed to DictField to support both text and image
    correct_answers = ListField(StringField())  # Store option index or option identifier
    marks = IntField(default=1)
    explanation = StringField()
    tags = ListField(StringField())
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'questions'}

from mongoengine import Document, ReferenceField, FileField, DateTimeField, StringField
from django.utils import timezone
from categories.models import Category  # make sure Category is also a MongoEngine Document
from users.models import User  # or your custom user document


class CSVFile(Document):
    category = ReferenceField(Category, required=True, reverse_delete_rule=2)  # CASCADE
    file_path = StringField(required=True)  # store path or name of uploaded file
    uploaded_by = ReferenceField(User, null=True)
    uploaded_at = DateTimeField(default=timezone.now)

    meta = {
        'collection': 'csv_files',
        'ordering': ['-uploaded_at']
    }

    def __str__(self):
        return f"{self.file_path} ({self.category.id})"



class Exam(Document):
    category = ReferenceField("practice_tests.PracticeTest", required=True)  # <-- string reference
    title = StringField(required=True)
    description = StringField()
    duration = IntField(required=True)
    total_marks = IntField(default=0)
    questions_per_test = IntField(required=True)
    passing_score = FloatField(default=60.0)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'exams'}


class TestAttempt(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    user = ReferenceField(User, required=True)
    exam = ReferenceField("Exam", required=False)
    category = ReferenceField("practice_tests.PracticeTest", required=True)  # <-- string reference
    questions = ListField(DictField())
    user_answers = ListField(DictField())
    score = FloatField(default=0)
    total_marks = IntField(default=0)
    percentage = FloatField(default=0)
    passed = BooleanField(default=False)
    start_time = DateTimeField(default=datetime.utcnow)
    end_time = DateTimeField()
    duration_taken = IntField()
    time_limit = IntField(required=True)
    is_time_up = BooleanField(default=False)
    is_completed = BooleanField(default=False)
    is_trial = BooleanField(default=False)  # Mark if this is a trial attempt
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'test_attempts'}


class QuestionBank(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    category = ReferenceField("practice_tests.PracticeTest", required=True)  # <-- string reference
    name = StringField(required=True)
    description = StringField()
    questions = ListField(ReferenceField("Question"))  # <-- string reference
    total_questions = IntField(default=0)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'question_banks'}
