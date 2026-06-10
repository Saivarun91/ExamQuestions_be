from mongoengine import Document, StringField, BooleanField, ReferenceField

class Language(Document):
    name = StringField(required=True)
    code = StringField(required=True, unique=True)
    is_active = BooleanField(default=True)
    font_family = StringField()

    meta = {
        "collection": "languages",
        "strict": False
    }

    def __str__(self):
        return self.name


class Translation(Document):
    language = ReferenceField(
        "Language",
        required=True
    )

    key = StringField(required=True)

    value = StringField(required=True)

    source_text = StringField()

    is_manual = BooleanField(default=False)

    meta = {
        "collection": "translations",
        "strict": False,
    }