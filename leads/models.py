from mongoengine import Document, StringField, DateTimeField, ObjectIdField, ReferenceField
from datetime import datetime
from bson import ObjectId

class Lead(Document):
    _id = ObjectIdField(default=ObjectId, primary_key=True)
    name = StringField(required=True)
    email = StringField(required=True)
    phone_number = StringField(required=False)  # Phone number field
    whatsapp_number = StringField(required=True)
    course = StringField(required=False)  # Course name selected (optional for general inquiries)
    course_id = StringField(required=False)  # Optional course ID if available
    search_query = StringField(required=False)  # What they searched for
    ip_address = StringField(required=False)
    user_agent = StringField(required=False)
    status = StringField(choices=['new', 'contacted', 'converted', 'closed'], default='new')
    notes = StringField(required=False)  # Admin can add notes
    contacted_at = DateTimeField(required=False)  # When admin contacted them
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'leads',
        'ordering': ['-created_at']
    }
    
    def __str__(self):
        return f"Lead: {self.name} - {self.email} - {self.course}"

