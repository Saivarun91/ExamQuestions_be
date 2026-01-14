from django.db import models

# Create your models here.
from mongoengine import Document, StringField, IntField
from django.utils.text import slugify


class Exam(Document):
    provider = StringField(required=True, max_length=100)
    title = StringField(required=True, max_length=255)
    code = StringField(required=True, max_length=50)
    badge = StringField(max_length=50, default="")

    practiceExams = IntField(default=0)
    questions = IntField(default=0)

    # SEO slugs (auto-generated)
    provider_slug = StringField(max_length=120)
    code_slug = StringField(max_length=120)

    meta = {
        "collection": "exams",
        "ordering": ["provider", "title"]
    }

    def save(self, *args, **kwargs):
        self.provider_slug = slugify(self.provider)
        self.code_slug = slugify(self.code)
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.code})"
