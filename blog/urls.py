from django.urls import path
from . import views

urlpatterns = [
    path("", views.get_all_blogs, name="get_all_blogs"),
    path("create/", views.create_blog, name="create_blog"),
    path("<str:blog_id>/", views.get_blog, name="get_blog"),
    path("<str:blog_id>/update/", views.update_blog, name="update_blog"),
    path("<str:blog_id>/delete/", views.delete_blog, name="delete_blog"),
]
