from django.urls import path
from . import views

urlpatterns = [
    # ✅ Get tests by category (put before slug-based routes) - backward compatibility
    path('category/<str:category_id>/', views.tests_by_category, name='tests_by_category'),
    
    # ✅ Get tests by course
    path('course/<str:course_id>/', views.tests_by_course, name='tests_by_course'),

    # ✅ Get all tests
    path('', views.get_all_tests, name='get_all_tests'),

    # ✅ Create a new test
    path('create/', views.create_test, name='create_test'),

    # ✅ Update a test by slug
    path('<str:slug>/update/', views.update_test, name='update_test'),

    # ✅ Delete a test by slug
    path('<str:slug>/delete/', views.delete_test, name='delete_test'),

    # ✅ Get a single test by slug (keep last)
    path('<str:slug>/', views.get_test_by_slug, name='get_test_by_slug'),
]
