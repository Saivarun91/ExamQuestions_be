"""
Script to create a sample course for testing
Run: python manage.py shell < create_sample_course.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from courses.models import Course
from providers.models import Provider
from categories.models import Category

def create_sample_course():
    print("Creating sample course...")
    
    # Get or create AWS provider
    try:
        provider = Provider.objects.get(slug='aws')
        print(f"✓ Found provider: {provider.name}")
    except Provider.DoesNotExist:
        provider = Provider(
            name='AWS',
            slug='aws',
            description='Amazon Web Services',
            is_active=True
        )
        provider.save()
        print(f"✓ Created provider: {provider.name}")
    
    # Get or create category
    try:
        category = Category.objects.get(slug='cloud-certifications')
        print(f"✓ Found category: {category.title}")
    except Category.DoesNotExist:
        category = Category(
            title='Cloud Certifications',
            slug='cloud-certifications',
            description='Cloud computing certifications',
            is_active=True
        )
        category.save()
        print(f"✓ Created category: {category.title}")
    
    # Create sample course
    slug = 'aws-a122'
    try:
        course = Course.objects.get(slug=slug)
        print(f"⚠ Course already exists: {course.title}")
    except Course.DoesNotExist:
        course = Course(
            provider=provider,
            title='AWS Sample Certification',
            code='A122',
            slug=slug,
            practice_exams=3,
            questions=100,
            badge='New',
            category=category,
            short_description='Sample AWS certification for testing',
            about='This is a sample course for testing the pricing functionality.',
            difficulty='Intermediate',
            duration='120 minutes',
            passing_score='700/1000',
            pass_rate=85,
            rating=4.5,
            is_active=True,
            
            # Sample pricing plans
            pricing_plans=[
                {
                    'name': 'Basic',
                    'duration': '1 month (30 days)',
                    'duration_months': '1',
                    'duration_days': '30',
                    'price': '₹299',
                    'original_price': '₹599',
                    'discount_percentage': 50,
                    'popular': False,
                    'status': 'active',
                    'features': [
                        'Full question bank',
                        'Detailed explanations',
                        'Unlimited attempts'
                    ]
                },
                {
                    'name': 'Premium',
                    'duration': '3 months (90 days)',
                    'duration_months': '3',
                    'duration_days': '90',
                    'price': '₹499',
                    'original_price': '₹999',
                    'discount_percentage': 50,
                    'popular': True,
                    'status': 'active',
                    'features': [
                        'Everything in Basic',
                        'Priority support',
                        'Performance analytics',
                        'Extended access'
                    ]
                },
                {
                    'name': 'Pro',
                    'duration': '6 months (180 days)',
                    'duration_months': '6',
                    'duration_days': '180',
                    'price': '₹799',
                    'original_price': '₹1599',
                    'discount_percentage': 50,
                    'popular': False,
                    'status': 'active',
                    'features': [
                        'Everything in Premium',
                        'Lifetime updates',
                        'Expert mentorship',
                        'Certificate of completion'
                    ]
                }
            ],
            
            # Sample pricing features
            pricing_features=[
                {
                    'icon': 'BookOpen',
                    'title': 'Full question bank',
                    'description': 'Access all questions for this exam'
                },
                {
                    'icon': 'CheckCircle2',
                    'title': 'Correct answers + explanations',
                    'description': 'Learn from detailed explanations'
                },
                {
                    'icon': 'Clock',
                    'title': 'Timed exam mode',
                    'description': 'Practice under real exam conditions'
                },
                {
                    'icon': 'RefreshCw',
                    'title': 'Unlimited attempts',
                    'description': 'Take the test as many times as you need'
                }
            ],
            
            # Sample comparison table
            pricing_comparison=[
                {'feature': 'Questions', 'free_value': '5 only', 'paid_value': 'Full access'},
                {'feature': 'Explanations', 'free_value': 'Limited', 'paid_value': 'Full explanations'},
                {'feature': 'Attempts', 'free_value': '1', 'paid_value': 'Unlimited'},
                {'feature': 'Timed mode', 'free_value': '✗', 'paid_value': '✓'},
                {'feature': 'Analytics', 'free_value': '✗', 'paid_value': '✓'}
            ],
            
            # Sample testimonials
            pricing_testimonials=[
                {
                    'name': 'John Doe',
                    'text': 'Great course! Helped me pass the exam.',
                    'rating': 5
                },
                {
                    'name': 'Jane Smith',
                    'text': 'Excellent explanations and practice questions.',
                    'rating': 5
                }
            ],
            
            # Sample FAQs
            pricing_faqs=[
                {
                    'question': 'Do I get all practice tests?',
                    'answer': 'Yes! You get access to all practice tests with detailed explanations.'
                },
                {
                    'question': 'What happens after my access expires?',
                    'answer': 'You can repurchase access anytime to continue practicing.'
                }
            ]
        )
        course.save()
        print(f"✓ Created course: {course.title} (slug: {course.slug})")
        print(f"✓ Pricing plans: {len(course.pricing_plans)}")
        print(f"✓ You can now access: /exams/aws/a122/practice/pricing")
    
    return course

if __name__ == '__main__':
    course = create_sample_course()
    print("\n" + "="*50)
    print("✅ Sample course created successfully!")
    print(f"Course ID: {course.id}")
    print(f"Course Slug: {course.slug}")
    print(f"Test URL: http://localhost:3000/exams/aws/a122/practice/pricing")
    print("="*50)

