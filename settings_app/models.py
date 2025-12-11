from mongoengine import Document, StringField, BooleanField, IntField, DateTimeField, FloatField
from datetime import datetime

class AdminSettings(Document):
    site_name = StringField(default="PrepTara")
    admin_email = StringField(default="admin@preptara.com")
    email_notifications = BooleanField(default=True)
    maintenance_mode = BooleanField(default=False)
    default_user_role = StringField(default="user", choices=["user", "moderator", "admin"])
    session_timeout = IntField(default=30)
    
    # Contact Details Fields
    contact_email = StringField(default="")
    contact_phone = StringField(default="")
    contact_address = StringField(default="")
    contact_website = StringField(default="")
    
    # Popular Providers Carousel Settings
    providers_carousel_speed = IntField(default=1500)  # Auto-scroll interval in milliseconds (default 1.5 seconds)
    providers_logo_size = IntField(default=80)  # Logo max size in pixels (default 80px)

    meta = {'collection': 'admin_settings'}


class PrivacyPolicy(Document):
    content = StringField(required=True, default="")
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'privacy_policy'}


class TermsOfService(Document):
    content = StringField(required=True, default="")
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'terms_of_service'}
