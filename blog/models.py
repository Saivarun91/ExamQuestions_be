from mongoengine import Document, StringField, DateTimeField
from datetime import datetime

class Blog(Document):
    title = StringField(required=True, max_length=255)
    excerpt = StringField()
    category = StringField(max_length=100)
    author = StringField(max_length=100)
    date = DateTimeField(default=datetime.utcnow)
    read_time = StringField()
    image_url = StringField()

    # ✅ New Meta Fields
    meta_title = StringField(max_length=255)
    meta_description = StringField(max_length=500)
    meta_keywords = StringField(max_length=255)

    meta = {"collection": "blogs"}

    def to_json(self):
        return {
            "id": str(self.id),
            "title": self.title,
            "excerpt": self.excerpt,
            "category": self.category,
            "author": self.author,
            "date": self.date.strftime("%Y-%m-%d"),
            "readTime": self.read_time,
            "image_url": self.image_url,
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
        }
