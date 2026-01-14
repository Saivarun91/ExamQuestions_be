"""
Initialize sample data for home page sections.
Run this script using: python manage.py shell < home/init_home_data.py
"""

from home.models import (
    HeroSection, ValueProposition, BlogPost, RecentlyUpdatedExam,
    FAQ, EmailSubscribeSection
)

print("🚀 Initializing Home Page Data...")

# =================== HERO SECTION ===================
print("\n1️⃣ Creating Hero Section...")
HeroSection.objects.all().delete()  # Clear existing
hero = HeroSection(
    title="Your Shortcut to Passing Any Certification Exam",
    subtitle="Accurate, updated, exam-style questions trusted by thousands of professionals preparing for their next big certification.",
    stats=[
        {"value": "94%", "label": "matched real exam difficulty"},
        {"value": "97%", "label": "passed using our practice"},
        {"value": "1.8M+", "label": "monthly practice sessions"}
    ],
    meta_title="AllExamQuestions - Best Certification Exam Practice Platform",
    meta_keywords="certification exams, practice questions, AWS, Azure, Cisco, CompTIA",
    meta_description="Ace your certification exams with our accurate, updated practice questions. Trusted by thousands of professionals worldwide."
)
hero.save()
print(f"✅ Hero Section created: {hero.id}")

# =================== VALUE PROPOSITIONS ===================
print("\n2️⃣ Creating Value Propositions...")
ValueProposition.objects.all().delete()  # Clear existing
propositions = [
    {"title": "100% Free to Start", "description": "Access practice questions at no cost", "icon": "Gift", "order": 1},
    {"title": "Updated Daily", "description": "Fresh questions added every single day", "icon": "Clock", "order": 2},
    {"title": "AI-Powered Exam Simulator", "description": "Realistic exam environment & timing", "icon": "Brain", "order": 3},
    {"title": "Realistic & Verified Questions", "description": "Peer-reviewed by certified professionals", "icon": "CheckCircle", "order": 4},
    {"title": "Community-Driven Accuracy", "description": "Crowdsourced validation & feedback", "icon": "Users", "order": 5},
    {"title": "Detailed Explanations", "description": "Learn the 'why' behind every answer", "icon": "FileText", "order": 6},
]
for prop_data in propositions:
    prop = ValueProposition(**prop_data)
    prop.save()
    print(f"✅ Created: {prop.title}")

# =================== BLOG POSTS ===================
print("\n3️⃣ Creating Blog Posts...")
BlogPost.objects.all().delete()  # Clear existing
blogs = [
    {
        "title": "How to Clear AWS SAA-C03 in 30 Days",
        "excerpt": "A comprehensive study plan to ace your AWS Solutions Architect exam in just one month.",
        "image_url": "/assets/blog-aws.jpg",
        "url": "/blog/aws-saa-c03-30-days",
        "author": "Admin",
        "is_featured": True,
        "meta_title": "AWS SAA-C03 Study Guide - Pass in 30 Days",
        "meta_keywords": "AWS, SAA-C03, certification, study guide",
        "meta_description": "Complete guide to passing AWS Solutions Architect exam in 30 days"
    },
    {
        "title": "Best Certifications for 2025",
        "excerpt": "Top IT certifications that will boost your career and salary in the coming year.",
        "image_url": "/assets/blog-cert.jpg",
        "url": "/blog/best-certifications-2025",
        "author": "Admin",
        "is_featured": True,
        "meta_title": "Best IT Certifications for 2025",
        "meta_keywords": "IT certifications, 2025, career growth",
        "meta_description": "Discover the top IT certifications for 2025"
    },
    {
        "title": "Azure vs AWS: Which Exam Should You Take?",
        "excerpt": "Compare the two leading cloud platforms and decide which certification path is right for you.",
        "image_url": "/assets/blog-azure.jpg",
        "url": "/blog/azure-vs-aws",
        "author": "Admin",
        "is_featured": True,
        "meta_title": "Azure vs AWS Certifications Comparison",
        "meta_keywords": "Azure, AWS, cloud certifications, comparison",
        "meta_description": "Compare Azure and AWS certifications to choose the right path"
    },
]
for blog_data in blogs:
    blog = BlogPost(**blog_data)
    blog.save()
    print(f"✅ Created: {blog.title}")

# =================== RECENTLY UPDATED EXAMS ===================
print("\n4️⃣ Creating Recently Updated Exams...")
RecentlyUpdatedExam.objects.all().delete()  # Clear existing
exams = [
    {"name": "AWS Solutions Architect Associate", "provider": "AWS", "code": "SAA-C03", "updated": "2 hours ago", "practice_exams": 3, "questions": 850, "slug": "aws-saa-c03", "order": 1},
    {"name": "Azure Administrator", "provider": "Microsoft", "code": "AZ-104", "updated": "5 hours ago", "practice_exams": 2, "questions": 720, "slug": "azure-az-104", "order": 2},
    {"name": "CompTIA Security+", "provider": "CompTIA", "code": "SY0-701", "updated": "8 hours ago", "practice_exams": 4, "questions": 980, "slug": "comptia-sy0-701", "order": 3},
    {"name": "CCNA 200-301", "provider": "Cisco", "code": "CCNA", "updated": "12 hours ago", "practice_exams": 5, "questions": 1200, "slug": "cisco-ccna-200-301", "order": 4},
    {"name": "Google Cloud Professional", "provider": "Google", "code": "GCP-PCA", "updated": "1 day ago", "practice_exams": 2, "questions": 650, "slug": "gcp-pca", "order": 5},
    {"name": "PMP Certification", "provider": "PMI", "code": "PMP", "updated": "1 day ago", "practice_exams": 3, "questions": 890, "slug": "pmi-pmp", "order": 6},
    {"name": "AWS Developer Associate", "provider": "AWS", "code": "DVA-C02", "updated": "2 days ago", "practice_exams": 2, "questions": 780, "slug": "aws-dva-c02", "order": 7},
    {"name": "Azure Data Engineer", "provider": "Microsoft", "code": "DP-203", "updated": "2 days ago", "practice_exams": 2, "questions": 560, "slug": "azure-dp-203", "order": 8},
]
for exam_data in exams:
    exam = RecentlyUpdatedExam(**exam_data)
    exam.save()
    print(f"✅ Created: {exam.name}")

# =================== FAQs ===================
print("\n5️⃣ Creating FAQs...")
FAQ.objects.all().delete()  # Clear existing
faqs = [
    {
        "question": "Are the practice questions similar to the real exam?",
        "answer": "Yes. Our questions closely match real exam difficulty and format based on continuous community feedback.",
        "order": 1
    },
    {
        "question": "How often are the questions updated?",
        "answer": "We update content daily based on exam changes and user reports.",
        "order": 2
    },
    {
        "question": "Is AllExamQuestions free to start?",
        "answer": "Yes. You can explore questions for free. Premium gives full access and advanced features.",
        "order": 3
    },
    {
        "question": "Can I cancel my subscription anytime?",
        "answer": "Absolutely. You can cancel whenever you want—no commitments.",
        "order": 4
    },
    {
        "question": "Do you support all certification providers?",
        "answer": "Yes. We cover AWS, Azure, Google Cloud, Cisco, CompTIA, PMI, Meta, Red Hat, Oracle, SAP and many more.",
        "order": 5
    },
    {
        "question": "Do these questions guarantee I will pass?",
        "answer": "No platform can guarantee results, but our learners consistently report high success rates.",
        "order": 6
    },
]
for faq_data in faqs:
    faq = FAQ(**faq_data)
    faq.save()
    print(f"✅ Created: {faq.question[:50]}...")

# =================== EMAIL SUBSCRIBE SECTION ===================
print("\n6️⃣ Creating Email Subscribe Section...")
EmailSubscribeSection.objects.all().delete()  # Clear existing
email_section = EmailSubscribeSection(
    title="Get Free Weekly Exam Updates",
    subtitle="Latest dumps, new questions & exam alerts delivered to your inbox",
    button_text="Subscribe",
    privacy_text="No spam. Unsubscribe anytime. Your privacy is protected."
)
email_section.save()
print(f"✅ Email Subscribe Section created: {email_section.id}")

print("\n🎉 All home page data initialized successfully!")
print("\n📝 Next Steps:")
print("  1. Restart Django server")
print("  2. Visit http://localhost:8000/api/home/hero/ to test")
print("  3. Refresh your frontend home page")
print("  4. Build admin UI for managing these sections")

