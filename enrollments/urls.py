from django.urls import path
from .views import (
    check_enrollment,
    create_enrollment,
    get_enrollments,
    get_enrollment_detail,
    delete_enrollment,
    update_enrollment,
    check_practice_enrollment,
    create_razorpay_order,
    verify_razorpay_payment,
    create_pricing_plan_order,
    get_user_enrollments,
    billing_history,
    download_invoice,
    create_newsletter,
    send_newsletter,
    get_newsletters,
    get_newsletter_detail,
    delete_newsletter,
)

urlpatterns = [
    # Check if user enrolled
    path("", get_enrollments, name="get_enrollments"),
    path("user/", get_user_enrollments, name="get_user_enrollments"),
    path("billing-history/", billing_history, name="billing_history"),
    path("check/<str:category_id>/", check_enrollment, name="check_enrollment"),
    

    # Create enrollment
    path("create/", create_enrollment, name="create_enrollment"),

    path("check/<str:practice_id>/test/", check_practice_enrollment, name="check_practice_enrollment"),
    # Get all enrollments

    # Razorpay payment endpoints (MUST come before <str:enrollment_id>/ to avoid matching conflicts)
    path("payment/create-order/", create_razorpay_order, name="create_razorpay_order"),
    path("payment/create-pricing-order/", create_pricing_plan_order, name="create_pricing_plan_order"),
    path("payment/verify/", verify_razorpay_payment, name="verify_razorpay_payment"),
    path("payment/<str:payment_id>/invoice/", download_invoice, name="download_invoice"),
    
    # Newsletter endpoints (MUST come before <str:enrollment_id>/ to avoid matching conflicts)
    path("newsletters/", get_newsletters, name="get_newsletters"),
    path("newsletters/create/", create_newsletter, name="create_newsletter"),
    path("newsletters/<str:newsletter_id>/", get_newsletter_detail, name="get_newsletter_detail"),
    path("newsletters/<str:newsletter_id>/send/", send_newsletter, name="send_newsletter"),
    path("newsletters/<str:newsletter_id>/delete/", delete_newsletter, name="delete_newsletter"),

    # Get single enrollment (use str id) - MUST come after all specific paths
    path("<str:enrollment_id>/", get_enrollment_detail, name="get_enrollment_detail"),

    # Delete enrollment
    path("<str:enrollment_id>/delete/", delete_enrollment, name="delete_enrollment"),

    # Update enrollment
    path("<str:enrollment_id>/update/", update_enrollment, name="update_enrollment"),
]
