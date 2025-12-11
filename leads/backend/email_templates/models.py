from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime

class EmailTemplate(Document):
    name = StringField(required=True, unique=True)  # e.g., "Welcome Email", "Password Reset"
    subject = StringField(required=True)  # Email subject line
    body = StringField(required=True)  # Email body (HTML or plain text)
    description = StringField()  # Optional description of when this template is used
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "email_templates",
        "strict": False
    }

    def save(self, *args, **kwargs):
        """Override save to update updated_at timestamp"""
        self.updated_at = datetime.utcnow()
        return super(EmailTemplate, self).save(*args, **kwargs)

