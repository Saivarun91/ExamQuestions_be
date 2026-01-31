from django.urls import path
from . import views

urlpatterns = [
    # Admin APIs - Specific patterns MUST come before catch-all patterns
    path('admin/get-configuration/', views.get_configuration, name='get_configuration'),
    path('admin/save-configuration/', views.save_configuration, name='save_configuration'),
    path('admin/get-counts/', views.get_counts, name='get_counts'),
    path('admin/questions-by-type/<str:question_type>/', views.get_questions_by_type, name='get_questions_by_type'),
    path('admin/parse-document/', views.parse_document, name='parse_document'),
    path('admin/generate-from-input/', views.generate_from_input, name='generate_from_input'),
    path('admin/parsing-sessions/', views.get_parsing_sessions, name='get_parsing_sessions'),
    path('admin/parsing-session/<str:session_id>/questions/', views.get_questions_by_session, name='get_questions_by_session'),
    path('admin/parsed-question/<str:question_id>/delete/', views.delete_parsed_question, name='delete_parsed_question'),
    path('admin/bulk-delete-parsed-questions/', views.bulk_delete_parsed_questions, name='bulk_delete_parsed_questions'),
    path('admin/course/<str:course_id>/', views.get_questions_by_course, name='get_questions_by_course'),
    path('admin/create/', views.create_question, name='create_question'),
    path('admin/bulk-delete/', views.bulk_delete_questions, name='bulk_delete_questions'),
    path('admin/upload-csv/', views.upload_questions_csv, name='upload_questions_csv'),
    path('admin/download-csv/', views.download_csv, name='download_csv'),
    path('admin/parsed-question/<str:question_id>/update/', views.update_parsed_question, name='update_parsed_question'),
    path('admin/<str:question_id>/update/', views.update_question, name='update_question'),
    path('admin/<str:question_id>/delete/', views.delete_question, name='delete_question'),
    # Catch-all pattern MUST be last
    path('admin/<str:question_id>/', views.get_question, name='get_question'),
    
    # Public API for test player
    path('test/<str:course_id>/<str:test_id>/', views.get_test_questions, name='get_test_questions'),
]

