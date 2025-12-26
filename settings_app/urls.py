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
    path('refund-cancellation-policy/', views.get_refund_cancellation_policy, name='get_refund_cancellation_policy'),
    path('refund-cancellation-policy/update/', views.update_refund_cancellation_policy, name='update_refund_cancellation_policy'),
    path('disclaimer/', views.get_disclaimer, name='get_disclaimer'),
    path('disclaimer/update/', views.update_disclaimer, name='update_disclaimer'),
    path('contact-us/', views.get_contact_us, name='get_contact_us'),
    path('contact-us/update/', views.update_contact_us, name='update_contact_us'),
    path('sitemap/', views.get_sitemap, name='get_sitemap'),
    path('sitemap/add/', views.add_sitemap_url, name='add_sitemap_url'),
    path('sitemap/update/', views.update_sitemap_url, name='update_sitemap_url'),
    path('sitemap/delete/', views.delete_sitemap_url, name='delete_sitemap_url'),
]
