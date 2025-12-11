from django.urls import path
from . import views

urlpatterns = [
    # -------------------------
    # Frontend pages (SEO-friendly)
    # -------------------------
    path('', views.home, name='home'),  # Homepage

    # Exams by provider (optional keyword for filtering)
    path('exams/<str:provider_slug>/', views.exams_by_provider, name='exams_by_provider'),
    path('exams/<str:provider_slug>/<str:keyword_slug>/', views.exams_by_provider, name='exams_by_provider_keyword'),

    # Search exams across all providers
    path('search/<str:keyword_slug>/', views.search_exams, name='search_exams'),

    # -------------------------
    # Backend API endpoints (for Postman / Next.js)
    # -------------------------
    path('api/providers/', views.providers_list, name='providers_list'),  # GET all active providers
    path('api/providers/create/', views.provider_create, name='provider_create'),  # POST
    path('api/providers/update/<str:provider_id>/', views.provider_update, name='provider_update'),  # PUT
    path('api/providers/delete/<str:provider_id>/', views.provider_delete, name='provider_delete'),  # DELETE
]
