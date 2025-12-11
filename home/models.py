from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ListField, DictField
import datetime


# =================== HERO SECTION ===================
class HeroSection(Document):
    title = StringField(required=True)
    subtitle = StringField()
    background_image_url = StringField()
    stats = ListField(DictField())  # [{ "label": "850+", "description": "Practice Tests" }]
    
    # SEO
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    
    # System fields
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "hero_sections",
        "strict": False  # Ignore extra fields in old documents
    }

    def __str__(self):
        return self.title


# =================== EXAMS PAGE TRUST BAR ===================
class ExamsPageTrustBar(Document):
    items = ListField(DictField())  # [{ "icon": "CheckCircle2", "label": "94% Match", "description": "Real exam difficulty" }]
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "exams_page_trust_bar",
        "strict": False
    }


# =================== EXAMS PAGE ABOUT SECTION ===================
class ExamsPageAbout(Document):
    heading = StringField(default="About All Popular Exams Preparation")
    content = StringField()  # Can contain multiple paragraphs separated by \n\n
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "exams_page_about",
        "strict": False
    }


# =================== VALUE PROPOSITIONS SECTION ===================
class ValuePropositionsSection(Document):
    heading = StringField(default="Why Choose AllExamQuestions?")
    subtitle = StringField(default="Everything you need to ace your certification exam in one place")
    heading_font_family = StringField(default="font-bold")  # Tailwind classes
    heading_font_size = StringField(default="text-4xl")
    heading_color = StringField(default="text-[#0C1A35]")
    subtitle_font_size = StringField(default="text-lg")
    subtitle_color = StringField(default="text-[#0C1A35]/70")
    
    # SEO
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    
    # System
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "value_propositions_section",
        "strict": False
    }


# =================== VALUE PROPOSITIONS ===================
class ValueProposition(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    icon = StringField(default="Gift")  # Lucide icon name
    order = IntField(default=0)
    
    # System
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "value_propositions",
        "strict": False,
        "ordering": ["order"]
    }


# =================== TESTIMONIALS ===================
class Testimonial(Document):
    name = StringField(required=True)
    role = StringField(required=True)
    text = StringField(required=True)
    rating = IntField(default=5, min_value=1, max_value=5)
    
    # Featured testimonials show on homepage
    is_featured = BooleanField(default=False)
    is_active = BooleanField(default=True)
    
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "testimonials",
        "strict": False
    }


# =================== BLOG POSTS ===================
class BlogPost(Document):
    title = StringField(required=True)
    excerpt = StringField(required=True)
    content = StringField()
    slug = StringField(required=True, unique=True)
    thumbnail_url = StringField()  # Image URL for blog post
    image_url = StringField()  # Alias for compatibility
    category = StringField()
    tags = ListField(StringField())
    reading_time = StringField(default="5 min read")  # e.g., "5 min read"
    
    # Homepage display
    is_featured = BooleanField(default=False)
    is_active = BooleanField(default=True)
    
    # SEO
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "blog_posts",
        "strict": False
    }


# =================== RECENTLY UPDATED EXAMS ===================
class RecentlyUpdatedExam(Document):
    name = StringField(required=True)
    code = StringField(required=True)
    provider = StringField(required=True)
    questions = IntField(default=0)
    slug = StringField(required=True)
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "recently_updated_exams",
        "strict": False
    }


# =================== FAQs ===================
class FAQ(Document):
    question = StringField(required=True)
    answer = StringField(required=True)
    order = IntField(default=0)
    category = StringField()  # Optional category for grouping
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "faqs",
        "strict": False,
        "ordering": ["order"]
    }


# =================== EMAIL SUBSCRIBE SECTION ===================
class EmailSubscribeSection(Document):
    heading = StringField(default="Stay Updated with Latest Exams")
    title = StringField(default="")  # Alias for heading, for frontend compatibility
    subtitle = StringField(default="Get notified about new practice tests and updates")
    button_text = StringField(default="Subscribe Now")
    privacy_text = StringField(default="No spam. Unsubscribe anytime. Your privacy is protected.")
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "email_subscribe_section",
        "strict": False
    }


# =================== EMAIL SUBSCRIBERS ===================
class EmailSubscriber(Document):
    email = StringField(required=True, unique=True)
    is_active = BooleanField(default=True)
    subscribed_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "email_subscribers",
        "strict": False
    }


# =================== TOP CATEGORIES SECTION ===================
class TopCategoriesSection(Document):
    heading = StringField(default="Top Certification Categories")
    subtitle = StringField(default="Explore certifications by category")
    heading_font_family = StringField(default="font-bold")  # Tailwind classes
    heading_font_size = StringField(default="text-4xl")
    heading_color = StringField(default="text-[#0C1A35]")
    subtitle_font_size = StringField(default="text-lg")
    subtitle_color = StringField(default="text-[#0C1A35]/70")
    
    # SEO
    meta_title = StringField()
    meta_keywords = StringField()
    meta_description = StringField()
    
    # System
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "top_categories_section",
        "strict": False
    }
