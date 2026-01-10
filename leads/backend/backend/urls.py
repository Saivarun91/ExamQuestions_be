from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('providers.urls')),  # Include providers URLs
    path("api/exams/", include("exams.urls")),
]
