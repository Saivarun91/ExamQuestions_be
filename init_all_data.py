"""
Master script to initialize all home page and course data.
Run this using: python manage.py shell < init_all_data.py
"""

print("=" * 60)
print("🎯 INITIALIZING ALL HOME PAGE & COURSE DATA")
print("=" * 60)

# Import all models
from home.models import (
    HeroSection, ValueProposition, ValuePropositionsSection, BlogPost, RecentlyUpdatedExam,
    FAQ, EmailSubscribeSection
)
from courses.models import Course
from providers.models import Provider

# =================== HERO SECTION ===================
print("\n1️⃣ Creating Hero Section...")
HeroSection.objects.all().delete()
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
print(f"   ✅ Hero Section created")

# =================== VALUE PROPOSITIONS SECTION ===================
print("\n2️⃣ Creating Value Propositions Section Settings...")
ValuePropositionsSection.objects.all().delete()
vp_section = ValuePropositionsSection(
    heading="Why Choose AllExamQuestions?",
    subtitle="Everything you need to ace your certification exam in one place",
    heading_font_family="font-bold",
    heading_font_size="text-4xl",
    heading_color="text-[#0C1A35]",
    subtitle_font_size="text-lg",
    subtitle_color="text-[#0C1A35]/70",
    meta_title="Why Choose AllExamQuestions - Best Features for Exam Prep",
    meta_keywords="exam preparation, practice questions, ai simulator, free exam prep, certification study",
    meta_description="Discover why thousands choose AllExamQuestions: 100% free to start, daily updates, AI-powered simulator, and realistic questions."
)
vp_section.save()
print(f"   ✅ Value Propositions Section settings created")

# =================== VALUE PROPOSITIONS ===================
print("\n3️⃣ Creating Value Propositions...")
ValueProposition.objects.all().delete()
propositions = [
    {"title": "100% Free to Start", "description": "Access practice questions at no cost", "icon": "Gift", "order": 1},
    {"title": "Updated Daily", "description": "Fresh questions added every single day", "icon": "Clock", "order": 2},
    {"title": "AI-Powered Exam Simulator", "description": "Realistic exam environment & timing", "icon": "Brain", "order": 3},
    {"title": "Realistic & Verified Questions", "description": "Peer-reviewed by certified professionals", "icon": "CheckCircle", "order": 4},
    {"title": "Community-Driven Accuracy", "description": "Crowdsourced validation & feedback", "icon": "Users", "order": 5},
    {"title": "Detailed Explanations", "description": "Learn the 'why' behind every answer", "icon": "FileText", "order": 6},
]
for prop_data in propositions:
    ValueProposition(**prop_data).save()
print(f"   ✅ {len(propositions)} propositions created")

# =================== BLOG POSTS ===================
print("\n4️⃣ Creating Blog Posts...")
BlogPost.objects.all().delete()
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
        "is_featured": True
    },
    {
        "title": "Azure vs AWS: Which Exam Should You Take?",
        "excerpt": "Compare the two leading cloud platforms and decide which certification path is right for you.",
        "image_url": "/assets/blog-azure.jpg",
        "url": "/blog/azure-vs-aws",
        "author": "Admin",
        "is_featured": True
    },
]
for blog_data in blogs:
    BlogPost(**blog_data).save()
print(f"   ✅ {len(blogs)} blog posts created")

# =================== RECENTLY UPDATED EXAMS ===================
print("\n5️⃣ Creating Recently Updated Exams...")
RecentlyUpdatedExam.objects.all().delete()
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
    RecentlyUpdatedExam(**exam_data).save()
print(f"   ✅ {len(exams)} recently updated exams created")

# =================== FAQs ===================
print("\n6️⃣ Creating FAQs...")
FAQ.objects.all().delete()
faqs = [
    {"question": "Are the practice questions similar to the real exam?", "answer": "Yes. Our questions closely match real exam difficulty and format based on continuous community feedback.", "order": 1},
    {"question": "How often are the questions updated?", "answer": "We update content daily based on exam changes and user reports.", "order": 2},
    {"question": "Is AllExamQuestions free to start?", "answer": "Yes. You can explore questions for free. Premium gives full access and advanced features.", "order": 3},
    {"question": "Can I cancel my subscription anytime?", "answer": "Absolutely. You can cancel whenever you want—no commitments.", "order": 4},
    {"question": "Do you support all certification providers?", "answer": "Yes. We cover AWS, Azure, Google Cloud, Cisco, CompTIA, PMI, Meta, Red Hat, Oracle, SAP and many more.", "order": 5},
    {"question": "Do these questions guarantee I will pass?", "answer": "No platform can guarantee results, but our learners consistently report high success rates.", "order": 6},
]
for faq_data in faqs:
    FAQ(**faq_data).save()
print(f"   ✅ {len(faqs)} FAQs created")

# =================== EMAIL SUBSCRIBE SECTION ===================
print("\n7️⃣ Creating Email Subscribe Section...")
EmailSubscribeSection.objects.all().delete()
email_section = EmailSubscribeSection(
    title="Get Free Weekly Exam Updates",
    subtitle="Latest dumps, new questions & exam alerts delivered to your inbox",
    button_text="Subscribe",
    privacy_text="No spam. Unsubscribe anytime. Your privacy is protected."
)
email_section.save()
print("   ✅ Email Subscribe Section created")

# =================== PROVIDERS ===================
print("\n8️⃣ Creating Providers...")
Provider.objects.all().delete()
providers = [
    {"name": "AWS", "icon": "Cloud", "slug": "aws", "order": 1, "meta_title": "AWS Certification Practice Exams", "meta_keywords": "AWS, cloud, certification", "meta_description": "Practice for AWS certification exams"},
    {"name": "Microsoft Azure", "icon": "Cloud", "slug": "azure", "order": 2, "meta_title": "Azure Certification Practice", "meta_keywords": "Azure, Microsoft, cloud", "meta_description": "Azure certification practice questions"},
    {"name": "Google Cloud", "icon": "Cloud", "slug": "google-cloud", "order": 3, "meta_title": "GCP Certification Practice", "meta_keywords": "GCP, Google Cloud", "meta_description": "Google Cloud certification prep"},
    {"name": "Cisco", "icon": "Shield", "slug": "cisco", "order": 4, "meta_title": "Cisco Certification Practice", "meta_keywords": "Cisco, networking, CCNA", "meta_description": "Cisco certification practice"},
    {"name": "CompTIA", "icon": "Award", "slug": "comptia", "order": 5, "meta_title": "CompTIA Certification Practice", "meta_keywords": "CompTIA, Security+, A+", "meta_description": "CompTIA certification prep"},
    {"name": "Oracle", "icon": "Database", "slug": "oracle", "order": 6, "meta_title": "Oracle Certification Practice", "meta_keywords": "Oracle, database", "meta_description": "Oracle certification practice"},
    {"name": "SAP", "icon": "Database", "slug": "sap", "order": 7, "meta_title": "SAP Certification Practice", "meta_keywords": "SAP, ERP", "meta_description": "SAP certification preparation"},
    {"name": "PMI", "icon": "Award", "slug": "pmi", "order": 8, "meta_title": "PMI PMP Certification Practice", "meta_keywords": "PMI, PMP, project management", "meta_description": "PMP certification practice"},
    {"name": "Meta", "icon": "Code", "slug": "meta", "order": 9, "meta_title": "Meta Certification Practice", "meta_keywords": "Meta, Facebook", "meta_description": "Meta certification preparation"},
    {"name": "Red Hat", "icon": "Building", "slug": "red-hat", "order": 10, "meta_title": "Red Hat Certification Practice", "meta_keywords": "Red Hat, Linux", "meta_description": "Red Hat certification prep"},
]
for provider_data in providers:
    Provider(**provider_data).save()
print(f"   ✅ {len(providers)} providers created")

# =================== FEATURED COURSES ===================
print("\n9️⃣ Creating Featured Courses...")
Course.objects.all().delete()
courses = [
    {"provider": "AWS", "title": "AWS Solutions Architect Associate", "code": "SAA-C03", "slug": "aws-saa-c03", "practice_exams": 3, "questions": 850, "badge": "Updated this week"},
    {"provider": "Microsoft Azure", "title": "Azure Administrator", "code": "AZ-104", "slug": "azure-az-104", "practice_exams": 2, "questions": 720, "badge": "Popular"},
    {"provider": "Cisco", "title": "CCNA 200-301", "code": "CCNA", "slug": "cisco-ccna-200-301", "practice_exams": 5, "questions": 1200, "badge": "Bestseller"},
    {"provider": "Google Cloud", "title": "GCP Professional Cloud Architect", "code": "GCP-PCA", "slug": "gcp-pca", "practice_exams": 2, "questions": 650, "badge": "New"},
    {"provider": "CompTIA", "title": "CompTIA Security+", "code": "SY0-701", "slug": "comptia-sy0-701", "practice_exams": 4, "questions": 980, "badge": "Updated this week"},
    {"provider": "AWS", "title": "AWS Developer Associate", "code": "DVA-C02", "slug": "aws-dva-c02", "practice_exams": 2, "questions": 780, "badge": "Popular"},
]
for course_data in courses:
    # Resolve provider name to Provider object
    provider_name = course_data.pop('provider')
    try:
        provider = Provider.objects.get(name=provider_name)
        course = Course(provider=provider, **course_data)
        course.save()
        print(f"   ✅ Created: {course.title} ({course.code})")
    except Provider.DoesNotExist:
        print(f"   ⚠️  Provider '{provider_name}' not found. Skipping course: {course_data['title']}")
print(f"   ✅ {len(courses)} courses processed")

print("\n" + "=" * 60)
print("🎉 ALL DATA INITIALIZED SUCCESSFULLY!")
print("=" * 60)
print("\n📝 Next Steps:")
print("  1. Restart Django server: python manage.py runserver")
print("  2. Test APIs:")
print("     - http://localhost:8000/api/home/hero/")
print("     - http://localhost:8000/api/home/value-propositions/")
print("     - http://localhost:8000/api/home/blog-posts/")
print("     - http://localhost:8000/api/home/recently-updated-exams/")
print("     - http://localhost:8000/api/home/faqs/")
print("     - http://localhost:8000/api/courses/")
print("     - http://localhost:8000/api/providers/")
print("  3. Refresh frontend home page")
print("  4. Build admin UI for managing these sections")
print("\n✨ Happy coding!")

