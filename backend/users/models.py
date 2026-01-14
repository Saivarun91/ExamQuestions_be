


import mongoengine as me
import bcrypt
from bson import ObjectId
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password


class User(me.Document):
    fullname = me.StringField(required=True)
    email = me.StringField(required=True, unique=True)
    phone_number = me.StringField(required=True)
    role = me.StringField(required=True, choices=['student', 'admin'], default='student')
    location = me.StringField()
    password = me.StringField(required=True)  # hashed
    # confirm_password = me.StringField(required=True) 
    enrolled_courses = me.ListField(me.GenericReferenceField())  # Can hold both Course and TestCategory references
    

    meta = {'collection': 'users'}

    def set_password(self, raw_password):
        self.password = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt()).decode()

    def check_password(self, raw_password):
        return bcrypt.checkpw(raw_password.encode('utf-8'), self.password.encode('utf-8'))


class Admin(me.Document):
    _id = me.ObjectIdField(default=ObjectId, primary_key=True)
    name = me.StringField(required=True, max_length=100)
    email = me.EmailField(required=True, unique=True)
    password = me.StringField(required=True)
    # confirm_password = me.StringField(required=True)
    role = me.StringField(default='admin')
    is_active = me.BooleanField(default=True)
    created_at = me.DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'admins'}

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)


class PasswordResetToken(me.Document):
    email = me.StringField(required=True)
    otp = me.StringField(required=True)
    token = me.StringField(default=None, null=True)  # Optional field for backward compatibility with existing index
    created_at = me.DateTimeField(default=datetime.utcnow)
    expires_at = me.DateTimeField(required=True)
    used = me.BooleanField(default=False)
    
    meta = {
        'collection': 'password_reset_tokens',
        'indexes': [
            {'fields': ['email', 'otp', 'used'], 'unique': False},
        ]
    }
