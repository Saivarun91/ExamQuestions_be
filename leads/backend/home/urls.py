from django.urls import path
from .views import (
    create_hero_section,
    get_hero_image,
    update_hero_section,
    get_hero_section,
    search_courses,
    create_analytics_stat,
    update_analytics_stat,
    delete_analytics_stat,
    get_analytics_stats,
    create_feature,
    update_feature,
    delete_feature,
    get_features,
    create_testimonial,
    update_testimonial,
    delete_testimonial,
    get_testimonial_image,
    get_testimonials,
    get_top_testimonials,
    get_faqs,
    create_faq,
    update_faq,
    delete_faq,
    create_cta_section,
    update_cta_section,
    delete_cta_section,
    get_active_cta_section,get_active_hero_section,
    get_about_section,
    create_or_update_about_section
    

)


urlpatterns = [
    path("hero/add/", create_hero_section, name="create_hero_section"),
    path("hero/", get_active_hero_section, name="get_active_hero_section"),
    path("hero-section/<str:hero_id>/image/", get_hero_image, name="get_hero_image"),
    path("hero/update/<str:hero_id>/", update_hero_section, name="update_hero_section"),
    path("hero/", get_hero_section, name="get_hero_section"),
    path("hero/search/", search_courses, name="search_courses"),

    path("analytics/", get_analytics_stats, name="get_analytics_stats"),
    path("analytics/create/", create_analytics_stat, name="create_analytics_stat"),
    path("analytics/update/<str:stat_id>/", update_analytics_stat, name="update_analytics_stat"),
    path("analytics/delete/<str:stat_id>/", delete_analytics_stat, name="delete_analytics_stat"),
    


    path("features/", get_features, name="get_features"),
    path("features/add/", create_feature, name="create_feature"),       # POST - Admin
    path("features/update/<str:feature_id>/", update_feature, name="update_feature"),  # PUT/POST
    path("features/delete/<str:feature_id>/", delete_feature, name="delete_feature"),  # DELETE

    path("testimonials/", get_testimonials, name="get_testimonials"),
    path("testimonials/top/", get_top_testimonials, name="get_top_testimonials"),
    path("testimonials/create/", create_testimonial, name="create_testimonial"),
    path("testimonials/update/<str:testimonial_id>/",update_testimonial, name="update_testimonial"),
    path("testimonials/delete/<str:testimonial_id>/", delete_testimonial, name="delete_testimonial"),
    path("testimonials/image/<str:testimonial_id>/", get_testimonial_image, name="get_testimonial_image"),
    

    

    path("faqs/", get_faqs, name="get_faqs"),              # Public
    path("faqs/create/", create_faq, name="create_faq"),   # Admin
    path("faqs/update/<str:faq_id>/", update_faq, name="update_faq"),
    path("faqs/delete/<str:faq_id>/", delete_faq, name="delete_faq"),

    path("cta/", get_active_cta_section, name="get_active_cta_section"),
    path("cta/add/", create_cta_section, name="create_cta_section"),
    path("api/cta/update/<str:cta_id>/", update_cta_section, name="update_cta_section"),
    path("api/cta/delete/<str:cta_id>/", delete_cta_section, name="delete_cta_section"),
    
    path("about/", get_about_section, name="get_about_section"),
    path("about/create/", create_or_update_about_section, name="create_or_update_about_section"),
    path("about/update/", create_or_update_about_section, name="update_about_section"),

]
