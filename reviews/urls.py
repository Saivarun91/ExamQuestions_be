from django.urls import path
from reviews.views import (
    submit_review,
    create_review,
    get_all_reviews,
    get_reviews,
    get_user_coupons,
    verify_coupon,
    get_all_reviews_admin,
    approve_review,
    reject_review,
    toggle_testimonial,
    create_coupon,
    get_all_coupons,
    update_coupon,
    delete_coupon,
    assign_coupon_to_lead,
    assign_coupon_to_user,
    send_coupon_to_all,
)

urlpatterns = [
    # Specific paths first (before catch-all patterns)
    path('submit/', submit_review, name='submit_review'),
    path('create/', create_review, name='create_review'),
    path('admin/all/', get_all_reviews, name='get_all_reviews'),
    path('coupons/', get_user_coupons, name='get_user_coupons'),
    path('coupons/verify/', verify_coupon, name='verify_coupon'),
    path('verify-coupon/', verify_coupon, name='verify_coupon_alt'),  # Alternative URL for frontend compatibility
    path('admin/', get_all_reviews_admin, name='get_all_reviews_admin'),
    path('category/<str:category_id>/', get_reviews, name='get_reviews_by_category'),
    # Admin coupon management
    path('admin/coupons/', get_all_coupons, name='get_all_coupons'),
    path('admin/coupons/create/', create_coupon, name='create_coupon'),
    path('admin/coupons/<str:coupon_id>/update/', update_coupon, name='update_coupon'),
    path('admin/coupons/<str:coupon_id>/delete/', delete_coupon, name='delete_coupon'),
    path('admin/coupons/assign/lead/<str:lead_id>/', assign_coupon_to_lead, name='assign_coupon_to_lead'),
    path('admin/coupons/assign/user/<str:user_id>/', assign_coupon_to_user, name='assign_coupon_to_user'),
    path('admin/coupons/send-to-all/', send_coupon_to_all, name='send_coupon_to_all'),
    # Parameterized paths last
    path('<str:review_id>/approve/', approve_review, name='approve_review'),
    path('<str:review_id>/reject/', reject_review, name='reject_review'),
    path('<str:review_id>/testimonial/', toggle_testimonial, name='toggle_testimonial'),
    # Default path last
    path('', get_reviews, name='get_reviews'),
]

