from mongoengine import Document, StringField
from django.utils.text import slugify

class Category(Document):
    title = StringField(required=True, unique=True)
    description = StringField()
    icon = StringField(required=True)  # Cloud, Shield, etc.
    slug = StringField(required=True, unique=True)

    # SEO fields
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()

    meta = {
        "collection": "categories",
        "strict": False
    }

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
