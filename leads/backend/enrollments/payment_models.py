# Payment model for Razorpay integration
from mongoengine import Document, StringField, FloatField, DateTimeField, ObjectIdField, ReferenceField
from bson import ObjectId
from datetime import datetime

class Payment(Document):
    id = ObjectIdField(primary_key=True, default=ObjectId)
    user_id = StringField(required=True)  # User ID
    enrollment_id = ReferenceField("Enrollment", required=False)  # Linked enrollment
    razorpay_order_id = StringField(required=True)  # Razorpay order ID
    razorpay_payment_id = StringField(required=False)  # Payment ID after successful payment
    razorpay_signature = StringField(required=False)  # Payment signature for verification
    amount = FloatField(required=True)  # Amount in rupees
    currency = StringField(default="INR")
    status = StringField(default="pending")  # pending, completed, failed, refunded
    payment_method = StringField(default="razorpay")
    coupon_code = StringField(required=False)  # Coupon code if used
    discount_amount = FloatField(default=0)  # Discount amount applied
    created_at = DateTimeField(default=datetime.utcnow)
    updated_at = DateTimeField(default=datetime.utcnow)
    paid_at = DateTimeField(required=False)
    
    meta = {"collection": "payments"}

