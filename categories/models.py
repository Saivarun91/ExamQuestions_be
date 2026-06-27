from mongoengine import Document, StringField, ListField, DictField, BooleanField, FileField
from django.utils.text import slugify

class Category(Document):
    title = StringField(required=True, unique=True)
    main_category = StringField()
    description = StringField()
    content = StringField()
    faqs = ListField(DictField())
    icon = StringField(required=True)  # Cloud, Shield, etc.
    image_url = StringField(required=False, default=None)  # Category image shown on UI
    image = FileField(required=False)  # Uploaded category image (served via API)
    slug = StringField(required=True, unique=True)

    # SEO fields
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    is_top_certification = BooleanField(default=False)

    # Hero section (category detail page)
    page_title = StringField()
    hero_title = StringField()
    hero_subtitle = StringField()

    meta = {
        "collection": "categories",
        "strict": False,
        "indexes": [
            "title",
            "slug",
            "main_category",
            "is_top_certification",
            [("title", 1), ("slug", 1)],
        ],
    }

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
