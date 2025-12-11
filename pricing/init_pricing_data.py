"""
Initialize pricing plans in the database
Run this script to populate sample pricing data
"""

from pricing.models import PricingPlan

def init_pricing_data():
    """Create sample pricing plans"""
    
    # Clear existing plans (optional - comment out if you want to keep existing data)
    PricingPlan.objects.delete()
    
    # Create pricing plans
    plans = [
        {
            'name': 'Basic',
            'price': 999,
            'currency': 'INR',
            'currency_symbol': '₹',
            'duration_months': 1,
            'duration_days': 30,
            'original_price': 1999,
            'discount_percentage': 50,
            'per_day_cost': '33.30',
            'features': [
                'Access to all practice questions',
                'Basic explanations for answers',
                'Progress tracking',
                '30 days of access',
                'Email support'
            ],
            'color_scheme': 'gray',
            'is_popular': False,
            'pdf_enabled': True,
            'pdf_price': 199,
            'is_active': True,
            'display_order': 1
        },
        {
            'name': 'Premium',
            'price': 1499,
            'currency': 'INR',
            'currency_symbol': '₹',
            'duration_months': 3,
            'duration_days': 90,
            'original_price': 2999,
            'discount_percentage': 50,
            'per_day_cost': '16.66',
            'features': [
                'Access to all practice questions',
                'Detailed explanations for all answers',
                'Advanced progress tracking & analytics',
                '90 days of access',
                'Priority email support',
                'Unlimited practice attempts',
                'Timed exam mode'
            ],
            'color_scheme': 'blue',
            'is_popular': True,
            'pdf_enabled': True,
            'pdf_price': 299,
            'is_active': True,
            'display_order': 0  # Show first (most popular)
        },
        {
            'name': 'Pro',
            'price': 2499,
            'currency': 'INR',
            'currency_symbol': '₹',
            'duration_months': 6,
            'duration_days': 180,
            'original_price': 4999,
            'discount_percentage': 50,
            'per_day_cost': '13.88',
            'features': [
                'Access to all practice questions',
                'Detailed explanations for all answers',
                'Advanced progress tracking & analytics',
                '180 days of access',
                'Priority email & chat support',
                'Unlimited practice attempts',
                'Timed exam mode',
                'Performance insights & recommendations',
                'PDF version included'
            ],
            'color_scheme': 'green',
            'is_popular': False,
            'pdf_enabled': True,
            'pdf_price': 0,  # Already included
            'is_active': True,
            'display_order': 2
        }
    ]
    
    created_plans = []
    for plan_data in plans:
        plan = PricingPlan(**plan_data)
        plan.save()
        created_plans.append(plan)
        print(f"✓ Created plan: {plan.name} - {plan.currency_symbol}{plan.price}")
    
    print(f"\n✓ Successfully created {len(created_plans)} pricing plans!")
    return created_plans

if __name__ == '__main__':
    print("Initializing pricing data...")
    init_pricing_data()

