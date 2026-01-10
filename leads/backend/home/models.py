from mongoengine import (
    Document,
    StringField,
    BooleanField,
    FileField,
    IntField,
    FloatField,
    DynamicField,
    ReferenceField
)

class HeroSection(Document):
    title = StringField(required=True, max_length=255)
    subtitle = StringField()
    search_placeholder = StringField(default="Search courses...")
    # background_image = FileField()  # you can store file metadata (GridFS)
    background_image_url = StringField() 
    is_active = BooleanField(default=True)

    meta = {
        "collection": "hero_section"
    }

    def __str__(self):
        return self.title


class AnalyticsStat(Document):
    title = StringField(required=True)  # e.g. "Students found the real exam almost same"
    value = DynamicField(required=True)  # e.g. "94%" or "1056"
    icon = StringField(required=True)   # e.g. "FileCheck", "Users", "TrendingUp"
    gradient = StringField(default="from-blue-500 to-cyan-600")
    is_active = BooleanField(default=True)

    meta = {'collection': 'analytics_stats'}


class Feature(Document):
    title = StringField(required=True)
    description = StringField(required=True)
    icon = StringField(required=True)  # e.g. "BarChart3", "BookOpen"
    gradient = StringField(required=True)  # e.g. "from-blue-500 via-cyan-500 to-teal-600"
    is_active = BooleanField(default=True)

    meta = {"collection": "features"}

    def __str__(self):
        return self.title



class Testimonial(Document):
    name = StringField(required=True)
    role = StringField(required=True)  # e.g., "UPSC CSE 2024"
    text = StringField(required=True)
    image = FileField()  # Admin can upload image/
    image_url = StringField()  # store Cloudinary image URL
    rating = IntField(default=5)
    category = ReferenceField("TestCategory", required=False)  # Optional: link to course/category
    is_featured = BooleanField(default=False)  # For top testimonials on home page
    is_active = BooleanField(default=True)

    meta = {"collection": "testimonials"}

    def __str__(self):
        return self.name



from mongoengine import Document, StringField, DateTimeField
import datetime

class FAQ(Document):
    question = StringField(required=True)
    answer = StringField(required=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {'collection': 'faqs'}


from mongoengine import Document, StringField, BooleanField, FileField, DateTimeField
import datetime

class CTASection(Document):
    heading = StringField(required=True, max_length=255)
    subheading = StringField()  # optional
    button_text_primary = StringField()  # optional
    button_link_primary = StringField()  # optional
    button_text_secondary = StringField()  # optional
    button_link_secondary = StringField()  # optional
    footer_note = StringField()  # optional
    background_image = FileField()  # optional
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        "collection": "cta_section"
    }

    def __str__(self):
        return self.heading


from mongoengine import Document, StringField, BooleanField, DateTimeField, ListField, DictField
import datetime

class AboutSection(Document):
    # Hero Section
    hero_title = StringField(default="About PrepTara")
    hero_subtitle = StringField(default="Empowering learners. Inspiring success.")
    
    # Mission & Vision
    mission_title = StringField(default="Our Mission")
    mission_description = StringField(default="To democratize quality education and make competitive exam preparation accessible to every aspiring student across India. We believe that with the right guidance and tools, every student can achieve their dreams.")
    
    vision_title = StringField(default="Our Vision")
    vision_description = StringField(default="To become India's most trusted and comprehensive platform for competitive exam preparation, helping millions of students transform their aspirations into achievements through technology and innovation.")
    
    # Stats
    stats = ListField(DictField(), default=[
        {"icon": "UserCheck", "number": "50,000+", "label": "Active Students"},
        {"icon": "BookOpen", "number": "1,000+", "label": "Practice Tests"},
        {"icon": "CheckCircle", "number": "98%", "label": "Success Rate"},
        {"icon": "Clock", "number": "24/7", "label": "Support"}
    ])
    
    # Values
    values_title = StringField(default="Our Values")
    values_subtitle = StringField(default="The principles that guide everything we do")
    values = ListField(DictField(), default=[
        {"icon": "Lightbulb", "title": "Innovation", "description": "Continuously improving our platform with cutting-edge technology"},
        {"icon": "Heart", "title": "Student First", "description": "Every decision we make puts student success at the center"},
        {"icon": "Award", "title": "Excellence", "description": "Committed to delivering the highest quality education"},
        {"icon": "Users", "title": "Community", "description": "Building a supportive network of learners and educators"}
    ])
    
    # Story Section
    story_title = StringField(default="Our Story")
    story_paragraphs = ListField(StringField(), default=[
        "PrepTara was born from a simple observation: millions of talented students across India struggle to access quality preparation resources for competitive exams. In 2020, a group of educators and technologists came together with a mission to change this.",
        "We started with a vision to create a platform that combines the best of technology and pedagogy. Today, PrepTara serves over 50,000 students across India, offering comprehensive preparation for UPSC, SSC, Banking, NEET, JEE, CAT, and many other competitive examinations.",
        "Our journey has just begun, and we're committed to continuously evolving our platform to meet the changing needs of students and the education landscape."
    ])
    story_image_url = StringField()
    
    # Quote
    quote_text = StringField(default="Empowering learners. Inspiring success.")
    quote_author = StringField(default="PrepTara Team")
    
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    
    meta = {
        "collection": "about_section"
    }
    
    def __str__(self):
        return "About Section"


