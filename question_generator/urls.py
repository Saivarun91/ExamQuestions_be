from django.urls import path
from . import views

urlpatterns = [
    path('generate-from-input/', views.generate_from_input),
    path('generated-questions/', views.get_generated_questions),
    path('generated-question/<str:question_id>/update/', views.update_generated_question),
    path('generated-question/<str:question_id>/delete/', views.delete_generated_question),
    path('generated-questions/bulk-delete/', views.bulk_delete_generated_questions),
    path('regenerate-questions/', views.regenerate_questions),
    path('validate-with-gemini/', views.validate_with_gemini),
    # path('generate-from-input-batch/', views.generate_from_input_batch),
]
