from mongoengine import Document, StringField, IntField, ReferenceField, DateTimeField, BooleanField, ObjectIdField, FloatField, ListField
from datetime import datetime
from bson import ObjectId

class Review(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    user = ReferenceField("users.User", required=True)
    category = ReferenceField("categories.Category", required=False)  # Optional: link to course/category
    course = ReferenceField("courses.Course", required=False)  # Link to specific course
    rating = IntField(required=True, min_value=1, max_value=5)
    comment = StringField(required=False)  # Made optional for backward compatibility
    text = StringField(required=False)  # Alternative field name
    is_approved = BooleanField(default=False)  # Admin can approve reviews
    is_active = BooleanField(default=True)
    is_testimonial = BooleanField(default=False)  # Admin can mark as testimonial
    coupon_generated = BooleanField(default=False)  # Track if coupon was generated
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "reviews"}

    def __str__(self):
        return f"Review by {self.user.fullname if hasattr(self.user, 'fullname') else 'User'} - {self.rating} stars"


class Coupon(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    code = StringField(required=True)  # Removed unique constraint to allow same code for multiple users
    user = ReferenceField("users.User", required=False)  # Optional for common coupons
    review = ReferenceField("Review", required=False)  # Link to review if generated from review
    lead = ReferenceField("leads.Lead", required=False)  # Link to lead if assigned to a lead
    discount_type = StringField(choices=['percentage', 'fixed'], default='percentage')
    discount_value = FloatField(required=True)  # Percentage (0-100) or fixed amount
    min_purchase = FloatField(default=0)  # Minimum purchase amount to use coupon
    max_discount = FloatField(default=None)  # Maximum discount amount (for percentage)
    valid_from = DateTimeField(default=datetime.utcnow)
    valid_until = DateTimeField(required=True)
    is_active = BooleanField(default=True)
    is_common = BooleanField(default=False)  # True if this is a common coupon for all students
    created_by_admin = BooleanField(default=False)  # True if created by admin
    is_used = BooleanField(default=False)  # Deprecated: kept for backward compatibility
    used_at = DateTimeField()
    used_by = ListField(ObjectIdField(), default=[])  # List of user IDs who have used this coupon
    created_at = DateTimeField(default=datetime.utcnow)

    meta = {"collection": "coupons"}

    def __str__(self):
        return f"Coupon {self.code} - {self.discount_value}{'%' if self.discount_type == 'percentage' else ' INR'}"

