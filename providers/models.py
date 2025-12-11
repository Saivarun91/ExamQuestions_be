from mongoengine import Document, StringField, BooleanField, IntField, DateTimeField, FileField
from django.utils.text import slugify
import datetime

class Provider(Document):
    name = StringField(required=True, unique=True)
    icon = StringField(required=True)  # Cloud, Shield, Award, Database, Code, Building
    slug = StringField(required=True, unique=True)
    logo = FileField(required=False)  # Optional logo image file
    
    # SEO Fields
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    
    # Display Settings
    order = IntField(default=0)
    is_active = BooleanField(default=True)
    
    # Timestamps
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "providers",
        "ordering": ["order"],
        "strict": False
    }

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        self.updated_at = datetime.datetime.utcnow()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
