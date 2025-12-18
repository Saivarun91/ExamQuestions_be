from django.urls import path
from . import views

urlpatterns = [
    path('public/', views.get_public_settings, name='get_public_settings'),
    path('get/', views.get_admin_settings, name='get_admin_settings'),
    path('update/', views.update_admin_settings, name='update_admin_settings'),
    path('privacy-policy/', views.get_privacy_policy, name='get_privacy_policy'),
    path('privacy-policy/update/', views.update_privacy_policy, name='update_privacy_policy'),
    path('terms-of-service/', views.get_terms_of_service, name='get_terms_of_service'),
    path('terms-of-service/update/', views.update_terms_of_service, name='update_terms_of_service'),
    path('sitemap/', views.get_sitemap, name='get_sitemap'),
    path('sitemap/add/', views.add_sitemap_url, name='add_sitemap_url'),
    path('sitemap/update/', views.update_sitemap_url, name='update_sitemap_url'),
    path('sitemap/delete/', views.delete_sitemap_url, name='delete_sitemap_url'),
]
