from django.contrib import admin
from django.urls import path, include
# from .sitemap import sitemap_view

from .sitemap import (
    sitemap_index,
    categories_sitemap,
    providers_sitemap,
    blogs_sitemap,
    exams_sitemap,
)

print("🔥 MAIN URLS LOADED 🔥")
urlpatterns = [
    path('admin/', admin.site.urls),
    # Specific API paths first (before catch-all patterns)
    path("api/dashboard/", include("dashboard.urls")),
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
    path("api/reviews/", include("reviews.urls")),
    path("api/search-logs/", include("search_logs.urls")),
    path("api/email-templates/", include("email_templates.urls")),
    path("api/leads/", include("leads.urls")),
    path("api/notifications/", include("notifications.urls")),
    path("api/providers/", include("providers.urls")),
    path("api/pricing/", include("pricing.urls")),
    path("api/parsing-suite/", include("parsing_suite.urls")),
    path("api/question-generator/", include("question_generator.urls")),
    path("api/question-validation/", include("question_validation.urls")),
    path("api/", include("Languages.urls")),
    # path("sitemap.xml", sitemap_view), 
    # path("sitemap.xml", sitemap_view, name="sitemap"),
    path("sitemap.xml", sitemap_index),
    path("api/sitemap.xml", sitemap_index),

    path("categories-sitemap.xml", categories_sitemap),
    path("api/categories-sitemap.xml", categories_sitemap),

    path("providers-sitemap.xml", providers_sitemap),
    path("api/providers-sitemap.xml", providers_sitemap),

    path("blogs-sitemap.xml", blogs_sitemap),
    path("api/blogs-sitemap.xml", blogs_sitemap),

    path("exams-sitemap.xml", exams_sitemap),
    path("api/exams-sitemap.xml", exams_sitemap),

    # Catch-all pattern last
    path('api/', include('exams.urls')),

]
