from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.submit_lead, name='submit_lead'),
    path('', views.get_leads, name='get_leads'),
    path('<str:lead_id>/update/', views.update_lead_status, name='update_lead_status'),
    path('<str:lead_id>/delete/', views.delete_lead, name='delete_lead'),
]

