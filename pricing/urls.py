from django.urls import path
from . import views

urlpatterns = [
    # Public endpoints
    path('plans/', views.get_pricing_plans, name='pricing_plans'),
    
    # Admin endpoints
    path('admin/plans/', views.admin_get_all_plans, name='admin_pricing_plans'),
    path('admin/plans/create/', views.admin_create_plan, name='admin_create_plan'),
    path('admin/plans/<str:plan_id>/update/', views.admin_update_plan, name='admin_update_plan'),
    path('admin/plans/<str:plan_id>/delete/', views.admin_delete_plan, name='admin_delete_plan'),
    path('admin/plans/initialize/', views.admin_initialize_plans, name='admin_initialize_plans'),
]

