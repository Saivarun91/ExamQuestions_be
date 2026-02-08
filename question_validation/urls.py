from django.urls import path
from . import views

urlpatterns = [
    path('run-validation/', views.run_validation),
    path('validated-questions/', views.get_validated_questions),
    path('validated-question/<str:validated_id>/update/', views.update_validated_question),
    path('validated-question/<str:validated_id>/delete/', views.delete_validated_question),
    path('validated-questions/bulk-delete/', views.bulk_delete_validated_questions),
    path('validated-questions/download-csv/', views.download_validated_questions_csv),
]
