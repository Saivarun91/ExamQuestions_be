from mongoengine import Document, StringField, ListField, DictField, IntField, DateTimeField, ReferenceField
import datetime
from courses.models import Course


class Question(Document):
    # Reference to course
    course = ReferenceField(Course, required=True)
    
    # Question details
    question_text = StringField(required=True)
    question_type = StringField(required=True, choices=['single', 'multiple'])  # single or multiple choice
    options = ListField(DictField(), required=True)  # List of {text: "option text", image: "url"}
    correct_answers = ListField(StringField(), required=True)  # List of correct answer texts
    explanation = StringField(default=None)
    
    # Optional fields
    question_image = StringField(default=None)  # URL or base64
    marks = IntField(default=1)
    tags = ListField(StringField(), default=list)
    
    # Metadata
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    
    meta = {
        "collection": "questions",
        "strict": False,
        "indexes": [
            "course",
            "question_type",
            "tags"
        ]
    }

