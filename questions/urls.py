from django.urls import path
from . import views

urlpatterns = [
    # Admin APIs - Specific patterns MUST come before catch-all patterns
    path('admin/course/<str:course_id>/', views.get_questions_by_course, name='get_questions_by_course'),
    path('admin/create/', views.create_question, name='create_question'),
    path('admin/bulk-delete/', views.bulk_delete_questions, name='bulk_delete_questions'),
    path('admin/upload-csv/', views.upload_questions_csv, name='upload_questions_csv'),
    path('admin/<str:question_id>/update/', views.update_question, name='update_question'),
    path('admin/<str:question_id>/delete/', views.delete_question, name='delete_question'),
    # Catch-all pattern MUST be last
    path('admin/<str:question_id>/', views.get_question, name='get_question'),
    
    # Public API for test player
    path('test/<str:course_id>/<str:test_id>/', views.get_test_questions, name='get_test_questions'),
]

