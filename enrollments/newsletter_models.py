# Newsletter model for managing followup emails and newsletters
from mongoengine import Document, StringField, DateTimeField, BooleanField, IntField, ObjectIdField
from bson import ObjectId
from datetime import datetime


class Newsletter(Document):
    id = ObjectIdField(primary_key=True, default=ObjectId)
    subject = StringField(required=True)
    content = StringField(required=True)  # HTML content
    sent_to_purchased_users = BooleanField(default=True)  # Only send to users who have made purchases
    sent_count = IntField(default=0)  # Number of emails sent
    created_at = DateTimeField(default=datetime.utcnow)
    sent_at = DateTimeField(required=False)  # When the newsletter was sent
    is_sent = BooleanField(default=False)  # Whether the newsletter has been sent
    
    meta = {"collection": "newsletters"}

