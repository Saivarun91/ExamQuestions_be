from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ListField, DictField, FloatField, ReferenceField
import datetime
from categories.models import Category
from providers.models import Provider


class Course(Document):
    # BASIC FIELDS
    provider = ReferenceField(Provider, required=True)  # Reference to Provider document
    title = StringField(required=True)              # AWS Architect, CCNA, etc
    code = StringField(required=True)               # SAA-C03, AZ-104, etc
    slug = StringField(required=True)               # SEO-friendly URL slug
    practice_exams = IntField(default=0)            # Number of practice exams
    questions = IntField(default=0)                 # Number of questions
    badge = StringField(default=None)               # "Updated this week"

    # Category (optional)
    category = ReferenceField(Category, required=False)  # Reference to Category document

    # PRICING FIELDS
    actual_price = FloatField(default=0.0)          # Original price (e.g., 4999.00)
    offer_price = FloatField(default=0.0)           # Discounted price (e.g., 2999.00)
    currency = StringField(default="INR")           # Currency (INR, USD, etc.)
    
    # Featured flag
    is_featured = BooleanField(default=False)       # Show in Featured Exams section

    # EXAM DETAILS PAGE FIELDS
    short_description = StringField(default=None)   # Short description for cards
    about = StringField(default=None)               # Exam description
    eligibility = StringField(default=None)         # Eligibility criteria
    exam_pattern = StringField(default=None)        # Exam pattern/format details
    pass_rate = IntField(default=None)              # Pass rate percentage (e.g., 94)
    rating = FloatField(default=None)               # Rating out of 5 (e.g., 4.8)
    difficulty = StringField(default=None)          # Beginner, Intermediate, Advanced
    duration = StringField(default=None)            # Exam duration (e.g., "130 minutes")
    passing_score = StringField(default=None)       # Passing score (e.g., "720/1000")
    
    # Lists for exam details
    whats_included = ListField(StringField(), default=list)     # List of included features
    why_matters = StringField(default=None)                     # Why this certification matters
    topics = ListField(DictField(), default=list)               # List of topics with name and weight
    practice_tests = ListField(ReferenceField('practice_tests.PracticeTest'), default=list)  # List of practice test references
    testimonials = ListField(DictField(), default=list)         # List of testimonials
    faqs = ListField(DictField(), default=list)                 # List of FAQs
    test_instructions = ListField(StringField(), default=list)  # Test instructions for practice tests
    test_description = StringField(default=None)                # Description shown on test player page
    
    # PRICING FIELDS
    hero_title = StringField(default="Choose Your Access Plan")  # Hero section title
    hero_subtitle = StringField(default="Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.")  # Hero section subtitle
    pricing_plans = ListField(DictField(), default=list)        # List of pricing plans (name, duration, price, popular, features)
    pricing_features = ListField(DictField(), default=list)     # List of features included (icon, title, description)
    pricing_testimonials = ListField(DictField(), default=list) # Testimonials specific to pricing page
    pricing_faqs = ListField(DictField(), default=list)         # FAQs specific to pricing page
    pricing_comparison = ListField(DictField(), default=list)   # Free vs Paid comparison table (feature, free, paid)

    # SEO FIELDS
    meta_title = StringField(default=None)
    meta_keywords = StringField(default=None)
    meta_description = StringField(default=None)

    # SYSTEM FIELDS
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "courses",
        "strict": False
    }
