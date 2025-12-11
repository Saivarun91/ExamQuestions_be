from django.urls import path
from . import views

urlpatterns = [
    path("create/", views.create_exam, name="create_exam"),
    path("all/", views.list_exams, name="list_exams"),

    # SEO-friendly exam URLs
    path("<str:provider_slug>/<str:code_slug>/", views.get_exam, name="get_exam"),

    path("update/<str:exam_id>/", views.update_exam, name="update_exam"),
    path("delete/<str:exam_id>/", views.delete_exam, name="delete_exam"),
]
