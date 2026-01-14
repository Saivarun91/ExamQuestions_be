from django.core.management.base import BaseCommand
from courses.models import Course
from providers.models import Provider
from categories.models import Category


class Command(BaseCommand):
    help = 'Creates a sample course with pricing data for testing'

    def handle(self, *args, **options):
        self.stdout.write("Creating sample course...")
        
        # Get or create AWS provider
        try:
            provider = Provider.objects.get(slug='aws')
            self.stdout.write(self.style.SUCCESS(f"✓ Found provider: {provider.name}"))
        except Provider.DoesNotExist:
            provider = Provider(
                name='AWS',
                slug='aws',
                description='Amazon Web Services',
                is_active=True
            )
            provider.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Created provider: {provider.name}"))
        
        # Get or create category
        try:
            category = Category.objects.get(slug='cloud-certifications')
            self.stdout.write(self.style.SUCCESS(f"✓ Found category: {category.title}"))
        except Category.DoesNotExist:
            category = Category(
                title='Cloud Certifications',
                slug='cloud-certifications',
                description='Cloud computing certifications',
                is_active=True
            )
            category.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Created category: {category.title}"))
        
        # Create sample course
        slug = 'aws-a122'
        try:
            course = Course.objects.get(slug=slug)
            self.stdout.write(self.style.WARNING(f"⚠ Course already exists: {course.title}"))
            self.stdout.write(f"Course ID: {course.id}")
            self.stdout.write(f"URL: http://localhost:3000/exams/aws/a122/practice/pricing")
            return
        except Course.DoesNotExist:
            pass
        
        course = Course(
            provider=provider,
            title='AWS Sample Certification A122',
            code='A122',
            slug=slug,
            practice_exams=3,
            questions=100,
            badge='New',
            category=category,
            short_description='Sample AWS certification for testing pricing features',
            about='This is a sample course for testing the pricing functionality. It includes sample pricing plans, features, testimonials, and FAQs.',
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
                        'Unlimited attempts',
                        'Timed mode',
                        'Review mode'
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
                        'Extended access',
                        'Progress tracking'
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
                        'Certificate of completion',
                        'Premium support'
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
                },
                {
                    'icon': 'Target',
                    'title': 'Review mode',
                    'description': 'Review all answers and explanations'
                },
                {
                    'icon': 'BarChart3',
                    'title': 'Performance analytics',
                    'description': 'Track your progress and identify weak areas'
                },
                {
                    'icon': 'TrendingUp',
                    'title': 'Topic-wise performance',
                    'description': 'See your performance by topic'
                },
                {
                    'icon': 'Bell',
                    'title': 'Question updates',
                    'description': 'Get the latest questions automatically'
                }
            ],
            
            # Sample comparison table
            pricing_comparison=[
                {'feature': 'Questions', 'free_value': '5 only', 'paid_value': 'Full access'},
                {'feature': 'Explanations', 'free_value': 'Limited', 'paid_value': 'Full explanations'},
                {'feature': 'Review mode', 'free_value': 'Limited', 'paid_value': 'Complete review'},
                {'feature': 'Attempts', 'free_value': '1', 'paid_value': 'Unlimited'},
                {'feature': 'Timed mode', 'free_value': '✗', 'paid_value': '✓'},
                {'feature': 'Analytics', 'free_value': '✗', 'paid_value': '✓'},
                {'feature': 'Validity', 'free_value': 'Unlimited', 'paid_value': '1 / 3 / 6 Months'}
            ],
            
            # Sample testimonials
            pricing_testimonials=[
                {
                    'name': 'Priya Sharma',
                    'text': 'Helped me clear the exam on first attempt! The explanations were incredibly detailed.',
                    'rating': 5
                },
                {
                    'name': 'Rahul Verma',
                    'text': 'Explanations were top-notch. Best investment for exam preparation.',
                    'rating': 5
                },
                {
                    'name': 'Amit Kumar',
                    'text': 'The closest match to real exam questions. Highly recommended!',
                    'rating': 5
                }
            ],
            
            # Sample FAQs
            pricing_faqs=[
                {
                    'question': 'Do I get all practice tests for this exam?',
                    'answer': 'Yes! You get access to the complete question bank with all practice tests, detailed explanations, and analytics for this specific exam.'
                },
                {
                    'question': 'What happens after my access expires?',
                    'answer': 'After your access period ends, you won\'t be able to take new tests. However, you can repurchase access anytime to continue practicing.'
                },
                {
                    'question': 'Are question updates included?',
                    'answer': 'Yes! All question updates are included during your access period. You\'ll automatically get the latest questions without any additional cost.'
                },
                {
                    'question': 'Is this a one-time payment?',
                    'answer': 'Yes, this is a one-time payment for the selected duration. There are no recurring charges or hidden fees.'
                },
                {
                    'question': 'Can I repurchase if needed?',
                    'answer': 'Absolutely! You can repurchase access anytime after your current access expires. Your previous progress and analytics will be preserved.'
                },
                {
                    'question': 'Do I get instant access after payment?',
                    'answer': 'Yes! Your access is activated immediately after successful payment. You can start practicing right away.'
                }
            ]
        )
        course.save()
        
        self.stdout.write(self.style.SUCCESS(f"\n✅ Sample course created successfully!"))
        self.stdout.write(f"Course ID: {course.id}")
        self.stdout.write(f"Course Slug: {course.slug}")
        self.stdout.write(f"Pricing plans: {len(course.pricing_plans)}")
        self.stdout.write(f"\n🌐 Test URLs:")
        self.stdout.write(f"  - Pricing: http://localhost:3000/exams/aws/a122/practice/pricing")
        self.stdout.write(f"  - Admin: http://localhost:3000/admin/courses/{course.id}/pricing")
        self.stdout.write(self.style.SUCCESS("\n✅ You can now test the pricing page!"))

