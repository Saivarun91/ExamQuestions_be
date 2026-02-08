from django.apps import AppConfig


class QuestionValidationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'question_validation'
    verbose_name = 'Question Validation (Gemini vs OpenAI)'
