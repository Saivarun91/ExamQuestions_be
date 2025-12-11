from django.urls import path
from . import views

urlpatterns = [
    path('log/', views.log_search, name='log_search'),
    path('', views.get_search_logs, name='get_search_logs'),
]

