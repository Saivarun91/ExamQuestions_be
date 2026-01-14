# models.py
from mongoengine import Document, StringField, IntField, DateField, ObjectIdField, ReferenceField
from bson import ObjectId
from categories.models import Category  # ✅ Import the category model

class Enrollment(Document):
    id = ObjectIdField(primary_key=True, default=ObjectId)
    user_name = StringField(required=True, max_length=100)  # or ReferenceField(User) if needed
    category = ReferenceField(Category, required=False)  # Optional for backward compatibility
    course = ReferenceField("Course", required=False)  # Course reference for course-level enrollment
    duration_months = IntField(required=True)
    enrolled_date = DateField(required=True)
    expiry_date = DateField(required=True)
    payment = ReferenceField("Payment", required=False)  # Link to payment

    meta = {"collection": "enrollments"}
