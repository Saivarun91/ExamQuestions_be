from django.urls import path
from . import views

urlpatterns = [
    # Admin APIs (must be above slug route)
    path('admin/list/', views.admin_course_list, name='admin_course_list'),
    path('admin/create/', views.course_create, name='course_create'),
    path('admin/<str:course_id>/update/', views.course_update, name='course_update'),
    path('admin/<str:course_id>/delete/', views.course_delete, name='course_delete'),

    # Pricing Management APIs
    path('admin/<str:course_id>/pricing/', views.manage_course_pricing, name='manage_course_pricing'),

    # Public APIs
    path('', views.course_list, name='course_list'),
    path('featured/', views.featured_courses, name='featured_courses'),
    path('category/<str:category_slug>/', views.courses_by_category, name='courses_by_category'),
    path('pricing/<str:provider>/<str:exam_code>/', views.get_pricing_by_slug, name='get_pricing_by_slug'),

    # SEO-Friendly exam URL
    path('exams/<str:course_identifier>/', views.course_detail, name='course_detail'),
]
