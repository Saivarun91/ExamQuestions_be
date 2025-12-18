from django.contrib import admin
from django.urls import path, include
from .sitemap import sitemap_view

urlpatterns = [
    path('admin/', admin.site.urls),
    # Specific API paths first (before catch-all patterns)
    path('api/users/', include('users.urls')),
    path('api/categories/', include('categories.urls')),
    path('api/courses/', include('courses.urls')),
    path('api/questions/', include('questions.urls')),
    path('api/tests/', include('practice_tests.urls')),
    path('api/exams/', include('exams.urls')),
    path('api/admin/', include('exams.urls')), 
    path('api/enrollments/', include('enrollments.urls')), 
    path("api/settings/", include("settings_app.urls")),   
    path("api/home/", include("home.urls")),
    path("api/blogs/", include("blog.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/reviews/", include("reviews.urls")),
    path("api/search-logs/", include("search_logs.urls")),
    path("api/email-templates/", include("email_templates.urls")),
    path("api/leads/", include("leads.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/providers/", include("providers.urls")),
    path("api/pricing/", include("pricing.urls")),
    # Catch-all pattern last
    path('api/', include('exams.urls')),
    path("sitemap.xml", sitemap_view), 
]
