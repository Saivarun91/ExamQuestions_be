from django.urls import path
from . import views

urlpatterns = [
    path('', views.template_list, name='template_list'),
    path('create/', views.template_create, name='template_create'),
    path('bulk-delete/', views.template_bulk_delete, name='template_bulk_delete'),
    path('<str:template_id>/', views.template_detail, name='template_detail'),
    path('<str:template_id>/update/', views.template_update, name='template_update'),
    path('<str:template_id>/delete/', views.template_delete, name='template_delete'),
]

