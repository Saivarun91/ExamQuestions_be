from mongoengine import Document, StringField, DateTimeField, ReferenceField, ObjectIdField
from datetime import datetime
from bson import ObjectId
from users.models import User

class SearchLog(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    query = StringField(required=True)
    user = ReferenceField(User, required=False)  # Optional - can be anonymous
    ip_address = StringField(required=False)
    user_agent = StringField(required=False)
    created_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'search_logs',
        'ordering': ['-created_at']
    }
    
    def __str__(self):
        return f"Search: {self.query} at {self.created_at}"

