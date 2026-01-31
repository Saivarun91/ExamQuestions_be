from mongoengine import Document, StringField, ListField, DictField, IntField, DateTimeField, ReferenceField
import datetime
from courses.models import Course


class Question(Document):
    # Reference to course
    course = ReferenceField(Course, required=True)

    # Question details
    question_text = StringField(required=True)
    # single or multiple choice
    question_type = StringField(required=True, choices=['single', 'multiple'])
    # List of {text: "option text", image: "url"}
    options = ListField(DictField(), required=True)
    # List of correct answer texts
    correct_answers = ListField(StringField(), required=True)
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


class ParsingSession(Document):
    """
    Tracks parsing and generation sessions for QuestionCraftsmanSuite.
    Each session represents one "Parse & Save All" operation or generation batch.
    """
    # Session identification
    # e.g., "Document Parse - 2024-01-15"
    session_name = StringField(required=True)
    session_type = StringField(required=True, choices=[
                               'parse', 'generate'], default='parse')

    # Reference to course
    course = ReferenceField(Course, required=True)

    # Document/file information (for parse sessions)
    document_name = StringField(default=None)  # Original filename
    document_type = StringField(default=None)  # pdf, docx, etc.

    # Session statistics
    # Total questions created in this session
    total_questions = IntField(default=0)
    input_questions_count = IntField(default=0)  # Number of input questions
    generated_questions_count = IntField(
        default=0)  # Number of generated questions

    # Status and metadata
    status = StringField(default='completed', choices=[
                         'in_progress', 'completed', 'failed'])
    errors = ListField(StringField(), default=list)  # Any errors encountered

    # Configuration used
    parsing_instructions = StringField(default=None)
    model_used = StringField(default=None)  # Gemini model or OpenAI model used

    # Timestamps
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    completed_at = DateTimeField(default=None)

    meta = {
        "collection": "parsing_sessions",
        "strict": False,
        "indexes": [
            "course",
            "session_type",
            "status",
            "created_at"
        ]
    }


class CraftsmanQuestion(Document):
    """
    Dedicated model for QuestionCraftsmanSuite questions.
    Stores all parsed input questions, generated questions, and manually reviewed questions
    in a separate collection for better organization and management.
    """
    # Reference to course
    course = ReferenceField(Course, required=True)

    # Reference to parsing session (optional - for questions created in sessions)
    parsing_session = ReferenceField(ParsingSession, default=None, null=True)

    # Question details
    question_text = StringField(required=True)
    # single or multiple choice
    question_type = StringField(required=True, choices=['single', 'multiple'])
    # List of {text: "option text", image: "url"}
    options = ListField(DictField(), required=True)
    # List of correct answer texts
    correct_answers = ListField(StringField(), required=False)
    explanation = StringField(default=None)

    # Optional fields
    question_image = StringField(default=None)  # URL or base64
    marks = IntField(default=1)
    tags = ListField(StringField(), default=list)

    # Status field to track question origin/type
    # 'input' = parsed from document
    # 'generated' = AI-generated from input questions
    # 'manual_review' = manually reviewed/edited
    status = StringField(required=True, choices=[
                         'input', 'generated', 'manual_review','validated','pending','approved','rejected','clean','needs_review',], default='input')

    # Metadata
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        # Dedicated collection for QuestionCraftsmanSuite
        "collection": "craftsman_questions",
        "strict": False,
        "indexes": [
            "course",
            "question_type",
            "status",  # Index for filtering by status
            "parsing_session",  # Index for filtering by session
            "tags"
        ]
    }
