from django.urls import path
from . import views
from . import analytics

urlpatterns = [
    path("", views.category_list, name="category-list"),
    path("create/", views.category_create, name="category-create"),
    path("analytics/", analytics.get_analytics, name="analytics"),
    path("top-certifications/", views.category_top_certifications, name="category-top-certifications"),
    path("<str:category_id>/image/", views.category_image, name="category-image"),
    path("<slug:slug>/", views.category_detail, name="category-detail"),
    path("<slug:slug>/update/", views.category_update, name="category-update"),
    path("<slug:slug>/upload-image/", views.category_upload_image, name="category-upload-image"),
    path("<slug:slug>/delete/", views.category_delete, name="category-delete"),
]
