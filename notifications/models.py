from mongoengine import Document, StringField, ReferenceField, DateTimeField, BooleanField, ObjectIdField
from datetime import datetime
from bson import ObjectId


class Notification(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    user = ReferenceField("users.User", required=True)
    type = StringField(required=True, choices=[
        'coupon', 
        'enrollment', 
        'test', 
        'announcement', 
        'deadline',
        'review_approved',
        'course_update',
        'coupon_expiring',
        'coupon_expired'
    ])
    title = StringField(required=True)
    message = StringField(required=True)
    is_read = BooleanField(default=False)
    read_at = DateTimeField()
    link = StringField(required=False)  # Optional link to related page
    metadata = StringField(required=False)  # JSON string for additional data
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {"collection": "notifications", "ordering": ["-created_at"]}
    
    def __str__(self):
        return f"Notification for {self.user.fullname if hasattr(self.user, 'fullname') else 'User'} - {self.title}"

