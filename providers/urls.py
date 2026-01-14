from django.urls import path
from . import views

urlpatterns = [
    # Public APIs - specific routes first
    path('', views.provider_list, name='provider-list'),  # GET active providers
    path('<str:provider_id>/logo/', views.provider_logo, name='provider-logo'),  # GET logo image (must come before slug route)
    path('<str:provider_slug>/', views.provider_detail, name='provider-detail'),  # GET by slug
    
    # Admin APIs
    path('admin/list/', views.admin_provider_list, name='admin-provider-list'),  # GET all
    path('admin/create/', views.admin_provider_create, name='admin-provider-create'),  # POST
    path('admin/<str:provider_id>/update/', views.admin_provider_update, name='admin-provider-update'),  # PUT
    path('admin/<str:provider_id>/delete/', views.admin_provider_delete, name='admin-provider-delete'),  # DELETE
    
    # Legacy endpoints (keep for backward compatibility)
    path('create/', views.provider_create, name='provider-create'),
    path('<str:provider_slug>/update/', views.provider_update, name='provider-update'),
    path('<str:provider_slug>/delete/', views.provider_delete, name='provider-delete'),
    path('bulk-delete/', views.provider_bulk_delete, name='provider-bulk-delete'),
]
