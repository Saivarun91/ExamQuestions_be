from django.urls import path
from . import views_config
from . import views_parse
from . import views_questions

urlpatterns = [
    path('get-config/', views_config.get_config),
    path('save-config/', views_config.save_config),
    path('test-parse/', views_parse.test_parse),
    path('parse-save-all/', views_parse.parse_save_all),
    path('input-questions/', views_questions.get_input_questions),
    path('input-question/<str:question_id>/update/', views_questions.update_parsed_question),
    path('input-question/<str:question_id>/delete/', views_questions.delete_parsed_question),
    path('input-questions/bulk-delete/', views_questions.bulk_delete_parsed_questions),
]
