"""
Initialize sample courses data for FeaturedExams section.
Run this script using: python manage.py shell < courses/init_courses_data.py
"""

from courses.models import Course
from providers.models import Provider

print("🚀 Initializing Featured Courses Data...")

# Clear existing courses
Course.objects.all().delete()

courses = [
    {
        "provider": "AWS",
        "title": "AWS Solutions Architect Associate",
        "code": "SAA-C03",
        "slug": "aws-saa-c03",
        "practice_exams": 3,
        "questions": 850,
        "badge": "Updated this week",
        "meta_title": "AWS SAA-C03 Practice Exams - Solutions Architect Associate",
        "meta_keywords": "AWS, SAA-C03, Solutions Architect, certification",
        "meta_description": "Practice for AWS Solutions Architect Associate exam with 850+ questions across 3 practice exams."
    },
    {
        "provider": "Microsoft Azure",
        "title": "Azure Administrator",
        "code": "AZ-104",
        "slug": "azure-az-104",
        "practice_exams": 2,
        "questions": 720,
        "badge": "Popular",
        "meta_title": "Azure AZ-104 Practice Exams - Administrator",
        "meta_keywords": "Azure, AZ-104, Administrator, certification",
        "meta_description": "Prepare for Azure Administrator certification with 720+ practice questions."
    },
    {
        "provider": "Cisco",
        "title": "CCNA 200-301",
        "code": "CCNA",
        "slug": "cisco-ccna-200-301",
        "practice_exams": 5,
        "questions": 1200,
        "badge": "Bestseller",
        "meta_title": "CCNA 200-301 Practice Exams - Cisco Certification",
        "meta_keywords": "Cisco, CCNA, 200-301, networking, certification",
        "meta_description": "Master CCNA 200-301 with 1200+ practice questions across 5 comprehensive exams."
    },
    {
        "provider": "Google Cloud",
        "title": "GCP Professional Cloud Architect",
        "code": "GCP-PCA",
        "slug": "gcp-pca",
        "practice_exams": 2,
        "questions": 650,
        "badge": "New",
        "meta_title": "GCP Professional Cloud Architect Practice Exams",
        "meta_keywords": "GCP, Google Cloud, Cloud Architect, certification",
        "meta_description": "Ace the GCP Professional Cloud Architect exam with 650+ practice questions."
    },
    {
        "provider": "CompTIA",
        "title": "CompTIA Security+",
        "code": "SY0-701",
        "slug": "comptia-sy0-701",
        "practice_exams": 4,
        "questions": 980,
        "badge": "Updated this week",
        "meta_title": "CompTIA Security+ SY0-701 Practice Exams",
        "meta_keywords": "CompTIA, Security+, SY0-701, security, certification",
        "meta_description": "Prepare for CompTIA Security+ with 980+ updated practice questions."
    },
    {
        "provider": "AWS",
        "title": "AWS Developer Associate",
        "code": "DVA-C02",
        "slug": "aws-dva-c02",
        "practice_exams": 2,
        "questions": 780,
        "badge": "Popular",
        "meta_title": "AWS DVA-C02 Practice Exams - Developer Associate",
        "meta_keywords": "AWS, DVA-C02, Developer, certification",
        "meta_description": "Master AWS Developer Associate certification with 780+ practice questions."
    },
]

for course_data in courses:
    # Resolve provider name to Provider object
    provider_name = course_data.pop('provider')
    try:
        provider = Provider.objects.get(name=provider_name)
    except Provider.DoesNotExist:
        print(f"⚠️  Provider '{provider_name}' not found. Skipping course: {course_data['title']}")
        continue
    
    # Create course with provider reference
    course = Course(provider=provider, **course_data)
    course.save()
    print(f"✅ Created: {course.title} ({course.code}) - Provider: {provider.name}")

print(f"\n🎉 {len(courses)} courses initialized successfully!")
print("\n📝 Next Steps:")
print("  1. Restart Django server")
print("  2. Visit http://localhost:8000/api/courses/ to test")
print("  3. Refresh your frontend home page")
print("  4. Featured Exams section should now display these courses")

