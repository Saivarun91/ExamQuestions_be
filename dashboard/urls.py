from django.urls import path
from . import views
print("🔥 DASHBOARD URLS LOADED 🔥")

urlpatterns = [
    path('', views.get_dashboard_data, name='dashboard_data'),
]
    