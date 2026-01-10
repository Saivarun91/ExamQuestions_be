from mongoengine import Document, StringField, BooleanField
from bson import ObjectId

class Provider(Document):
    name = StringField(required=True, unique=True)
    slug = StringField(required=True, unique=True)
    is_active = BooleanField(default=True)

    # Optional SEO fields
    meta_title = StringField(default=None)
    meta_keywords = StringField(default=None)
    meta_description = StringField(default=None)

    meta = {
        "collection": "providers",
        "strict": False
    }

    def to_json(self):
        """
        Return provider as JSON-safe dictionary
        Include ID as string for frontend
        """
        return {
            "id": str(self.id),  # Convert ObjectId to string
            "name": self.name,
            "slug": self.slug
        }
