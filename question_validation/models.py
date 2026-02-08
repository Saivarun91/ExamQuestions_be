"""Store validation results: OpenAI answer vs Gemini answer per question."""
from mongoengine import Document, StringField, ListField, DictField, DateTimeField, BooleanField
import datetime


class ValidatedQuestion(Document):
    """One validation result: question, OpenAI answer(s), Gemini answer(s), match or not."""
    generated_question_id = StringField(required=True)
    question_text = StringField(required=True)
    options = ListField(DictField(), default=list)  # [{text, explanation}, ...]
    openai_answers = ListField(StringField(), default=list)  # correct_answers from OpenAI
    gemini_answers = ListField(StringField(), default=list)  # answer(s) from Gemini (question+options only)
    explanation = StringField(default="")  # overall explanation from OpenAI
    is_valid = BooleanField(default=False)  # True if openai_answers match gemini_answers
    validated_at = DateTimeField(default=datetime.datetime.utcnow)
    session_id = StringField(default="")
    session_name = StringField(default="")

    batch_id = StringField(default="")  # group validation runs

    meta = {
        "collection": "question_validation_validated",
        "strict": False,
        "indexes": ["validated_at", "batch_id", "generated_question_id"],
    }
