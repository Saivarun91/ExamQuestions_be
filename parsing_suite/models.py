from mongoengine import Document, StringField, ListField, DateTimeField
import datetime


class ParsedInputQuestion(Document):
    """Stores parsed questions: question_text, options (list of strings), parsing_flag (VALID|INVALID). batch_id = current document."""
    question_text = StringField(required=True)
    options = ListField(StringField(), required=True)
    parsing_flag = StringField(default="VALID")
    batch_id = StringField(default="")
    session_id = StringField(default="") 
    created_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "parsing_suite_input_questions",
        "strict": False,
        "indexes": ["created_at", "batch_id"],
    }
