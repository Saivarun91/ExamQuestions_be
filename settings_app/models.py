from mongoengine import Document, StringField, BooleanField, IntField, DateTimeField, FloatField, ListField, EmbeddedDocument, EmbeddedDocumentField, DictField
from datetime import datetime


class AdminSettings(Document):
    site_name = StringField(default="PrepTara")
    admin_email = StringField(default="admin@preptara.com")
    logo_url = StringField(default="")
    email_notifications = BooleanField(default=True)
    maintenance_mode = BooleanField(default=False)
    default_user_role = StringField(default="user", choices=[
                                    "user", "moderator", "admin"])
    session_timeout = IntField(default=30)

    # Contact Details Fields
    contact_email = StringField(default="")
    contact_phone = StringField(default="")
    contact_address = StringField(default="")
    contact_website = StringField(default="")

    # Popular Providers Carousel Settings
    # Auto-scroll interval in milliseconds (default 1.5 seconds)
    providers_carousel_speed = IntField(default=1500)
    # Logo max size in pixels (default 80px)
    providers_logo_size = IntField(default=80)

    # Social Media URLs
    social_facebook_url = StringField(default="")
    social_twitter_url = StringField(default="")
    social_linkedin_url = StringField(default="")
    social_youtube_url = StringField(default="")
    social_instagram_url = StringField(default="")

    # Configuration fields for question parsing and generation
    parsing_instructions = StringField(default="")
    max_retry_count = IntField(default=3)
    temperature = FloatField(default=0.0)
    model_selector = StringField(default="gpt-4")
    gemini_api_key = StringField(default="")
    openai_api_key = StringField(default="")
    prompts = DictField(default=dict)  # Store prompts as nested dictionary

    meta = {'collection': 'admin_settings', 'strict': False}


class PrivacyPolicy(Document):
    content = StringField(required=True, default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'privacy_policy'}


class TermsOfService(Document):
    content = StringField(required=True, default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'terms_of_service'}


class RefundCancellationPolicy(Document):
    content = StringField(required=True, default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'refund_cancellation_policy'}


class Disclaimer(Document):
    content = StringField(required=True, default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'disclaimer'}


class ContactUs(Document):
    contact_email = StringField(default="")
    contact_phone = StringField(default="")
    contact_address = StringField(default="")
    contact_website = StringField(default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'contact_us'}


class SitemapURL(EmbeddedDocument):
    url = StringField(required=True)
    priority = FloatField(default=0.5, min_value=0.0, max_value=1.0)
    changefreq = StringField(default="monthly", choices=[
                             "always", "hourly", "daily", "weekly", "monthly", "yearly", "never"])
    lastmod = DateTimeField(default=datetime.utcnow)


class Sitemap(Document):
    urls = ListField(EmbeddedDocumentField(SitemapURL), default=list)
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'sitemap'}
