from django.urls import path
from exams.views import (
    create_question,
    update_question,
    delete_question,
    bulk_delete_questions,
    get_question_by_id,
    get_question_image,
    upload_questions_csv,
    get_csv_files,
    delete_csv_file,
    create_exam,
    get_questions,
    start_test,
    submit_test,
    get_test_result,
    get_attempt_questions,
    get_result_summary,
    create_question_bank,
    get_test_rankings,
    get_topic_wise_analysis,
    get_or_create_test_attempt,
)

urlpatterns = [
    # 🧩 Question Management
     
  path('questions/create/', create_question, name='create_question'),
  path('questions/update/<str:question_id>/', update_question, name='update_question'),
  path('questions/delete/<str:question_id>/', delete_question, name='delete_question'),
  # specific question-related endpoints should come BEFORE the
  # catch-all `questions/<str:question_id>/` route so they are
  # matched correctly (otherwise 'upload-csv' is treated as an id).
  path('questions/bulk-delete/', bulk_delete_questions, name='bulk_delete_questions'),
  path('questions/upload-csv/', upload_questions_csv, name='upload_questions_csv'),
  path('questions/csv-files/', get_csv_files, name='get_csv_files'),
  path('questions/csv-files/delete/<str:csv_id>/', delete_csv_file, name='delete_csv_file'),
  path('questions/', get_questions, name='get_questions'),
  path('questions/<str:question_id>/image/', get_question_image, name='get_question_image'),
  path('questions/<str:question_id>/', get_question_by_id, name='get_question_by_id'),

  # path('questions_view/',questions_view, name='questions_view'),

    # 🧩 Exam Management
  path('create/', create_exam, name='create-exam'),
  path('start/', start_test, name='start-test'),
  # IMPORTANT: More specific patterns must come BEFORE parameterized patterns
  path('attempt/get-or-create/', get_or_create_test_attempt, name='get-or-create-test-attempt'),
  path("attempt/<str:attempt_id>/questions/", get_attempt_questions, name="get_attempt_questions"),
  path('attempt/<str:attempt_id>/submit/', submit_test, name='submit-test'),
  path("results/<str:attempt_id>/", get_test_result, name="get_test_result"),
  path("results/<str:attempt_id>/summary/", get_result_summary, name="get_result_summary"),
  path('question-bank/create/', create_question_bank, name='create-question-bank'),
  path('rankings/<str:category_id>/', get_test_rankings, name='get_test_rankings'),
  path('attempt/<str:attempt_id>/topic-analysis/', get_topic_wise_analysis, name='get_topic_wise_analysis'),
]
