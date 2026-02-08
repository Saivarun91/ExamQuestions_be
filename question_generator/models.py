from mongoengine import Document, StringField, ListField, DictField, DateTimeField
import datetime


class GeneratedQuestion(Document):
    """Generated question: question_text, question_type, options (text+explanation per option), correct_answers, explanation."""
    question_text = StringField(required=True)
    question_type = StringField(default="single-correct")  # "single-correct" | "multiple-correct"
    options = ListField(DictField(), default=list)  # [{text, explanation}, ...]
    correct_answers = ListField(StringField(), default=list)
    explanation = StringField(default="")
    batch_id = StringField(default="")
    session_id = StringField(default="") 
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "question_generator_generated",
        "strict": False,
        "indexes": ["created_at", "session_id"],
    }
