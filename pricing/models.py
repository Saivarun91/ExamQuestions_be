from mongoengine import Document, StringField, IntField, BooleanField, DateTimeField, ListField
import datetime


class PricingPlan(Document):
    """Pricing plan model for subscription tiers"""
    # Basic Info
    name = StringField(required=True)  # e.g., "Basic", "Premium", "Pro"
    price = IntField(required=True)  # Price (e.g., 999 for ₹999)
    currency = StringField(default="INR")
    currency_symbol = StringField(default="₹")
    
    # Duration
    duration_months = IntField(default=1)  # Duration in months
    duration_days = IntField(default=30)  # Duration in days
    
    # Pricing Details
    original_price = IntField(default=0)  # Original price before discount
    discount_percentage = IntField(default=0)  # Discount percentage
    per_day_cost = StringField(default="0")  # Cost per day
    
    # Features & Styling
    features = ListField(StringField(), default=list)
    color_scheme = StringField(default="blue")  # "blue", "green", "gray"
    is_popular = BooleanField(default=False)  # Mark as most popular
    display_order = IntField(default=0)  # Display order (lower numbers first)
    
    # PDF Add-on
    pdf_enabled = BooleanField(default=True)
    pdf_price = IntField(default=0)  # Additional cost for PDF
    
    # Status
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    
    meta = {
        'collection': 'pricing_plans',
        'indexes': ['name', 'is_active', 'is_popular', 'display_order']
    }
    
    def __str__(self):
        return f"{self.name} - {self.currency_symbol}{self.price}"

