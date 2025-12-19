from mongoengine import Document, StringField, BooleanField, IntField, DateTimeField, FloatField, ListField, EmbeddedDocument, EmbeddedDocumentField
from datetime import datetime

class AdminSettings(Document):
    site_name = StringField(default="PrepTara")
    admin_email = StringField(default="admin@preptara.com")
    logo_url = StringField(default="")
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


class SitemapURL(EmbeddedDocument):
    url = StringField(required=True)
    priority = FloatField(default=0.5, min_value=0.0, max_value=1.0)
    changefreq = StringField(default="monthly", choices=["always", "hourly", "daily", "weekly", "monthly", "yearly", "never"])
    lastmod = DateTimeField(default=datetime.utcnow)


class Sitemap(Document):
    urls = ListField(EmbeddedDocumentField(SitemapURL), default=list)
    updated_at = DateTimeField(default=datetime.utcnow)
    
    meta = {'collection': 'sitemap'}
