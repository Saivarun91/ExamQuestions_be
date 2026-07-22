from mongoengine import Document, StringField, BooleanField, IntField, DateTimeField, FloatField, ListField, EmbeddedDocument, EmbeddedDocumentField, DictField
from datetime import datetime


class AdminSettings(Document):
    site_name = StringField(default="PrepTara")
    admin_email = StringField(default="admin@preptara.com")
    logo_url = StringField(default="")
    email_notifications = BooleanField(default=True)
    maintenance_mode = BooleanField(default=False)
    default_user_role = StringField(default="user", choices=["user", "moderator", "admin"])
    session_timeout = IntField(default=30)

    # Contact Details
    contact_email = StringField(default="")
    contact_phone = StringField(default="")
    contact_address = StringField(default="")
    contact_website = StringField(default="")

    # Providers Carousel
    providers_carousel_speed = IntField(default=1500)
    providers_logo_size = IntField(default=80)

    # Social Media
    social_facebook_url = StringField(default="")
    social_twitter_url = StringField(default="")
    social_linkedin_url = StringField(default="")
    social_youtube_url = StringField(default="")
    social_instagram_url = StringField(default="")

    # 🔥 LLM CONFIG (MISSING BEFORE)
    parsing_instructions = StringField(default="")
    max_retry_count = IntField(default=3)
    temperature = FloatField(default=0.0)
    top_p = FloatField(default=1.0)
    frequency_penalty = FloatField(default=0.0)
    presence_penalty = FloatField(default=0.0)
    max_output_tokens = IntField(default=2000)

    model_selector = StringField(default="gpt-4")
    gemini_model_selector = StringField(default="gemini-1.5-flash-latest")
    gemini_api_key = StringField(default="")

    openai_api_key = StringField(default="")

    prompts = DictField(default=dict)

    meta = {
        'collection': 'admin_settings',
        'strict': False
    }

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


class EditorPolicy(Document):
    content = StringField(required=True, default="")
    meta_title = StringField(default="")
    meta_keywords = StringField(default="")
    meta_description = StringField(default="")
    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {'collection': 'editor_policy'}


class FooterSettings(Document):
    """Editable site footer content managed from the admin panel."""
    providers_title = StringField(default="Exam Providers Covered")
    resources_title = StringField(default="Resources")
    legal_title = StringField(default="Legal")
    contact_title = StringField(default="Contact Us")

    blogs_label = StringField(default="Blogs")
    faq_label = StringField(default="FAQ")
    privacy_policy_label = StringField(default="Privacy Policy")
    terms_label = StringField(default="Terms & Conditions")
    refund_policy_label = StringField(default="Refund & Cancellation Policy")
    disclaimer_link_label = StringField(default="Disclaimer")
    editor_policy_label = StringField(default="Editor Policy")
    contact_us_label = StringField(default="Contact Us")

    copyright = StringField(default="© 2025 AllExamQuestions. All rights reserved.")
    brand_line = StringField(default="A Brand of TutorKhoj Private Limited")
    disclaimer_label = StringField(default="Disclaimer:")
    disclaimer_text = StringField(
        default=(
            "All trademarks, certification names, course titles, and logos displayed on this website "
            "are the property of their respective owners and are used solely for identification and "
            "informational purposes. AllExamQuestions is an independent exam preparation platform and "
            "is not affiliated with, endorsed by, authorized by, or sponsored by any exam provider, "
            "certification body, or brand mentioned on this website. Any brand names, product names, "
            "or service names are used only to describe the corresponding exams or content. Some "
            "graphics used on this website are sourced from royalty-free or publicly available "
            "resources and are believed to be free for commercial use."
        )
    )
    ssl_secure = StringField(default="SSL Secure")
    no_providers = StringField(default="No providers available")
    loading = StringField(default="Loading...")

    providers_limit = IntField(default=5)
    show_social_links = BooleanField(default=True)
    show_disclaimer = BooleanField(default=True)

    updated_at = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'footer_settings',
        'strict': False,
    }


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
