from django.urls import path
from . import views

urlpatterns = [
    # Public APIs - Home Page Sections
    path('hero/', views.get_hero_section, name='get_hero_section'),
    path('value-propositions-section/', views.get_value_propositions_section, name='get_value_propositions_section'),
    path('value-propositions/', views.get_value_propositions, name='get_value_propositions'),
    path('testimonials/', views.get_testimonials, name='get_testimonials'),
    path('blog-posts/', views.get_blog_posts, name='get_blog_posts'),
    path('blog-posts/slug/<str:slug>/', views.get_blog_post_by_slug, name='get_blog_post_by_slug'),
    path('recently-updated-exams/', views.get_recently_updated_exams, name='get_recently_updated_exams'),
    path('faqs/', views.get_faqs, name='get_faqs'),
    path('email-subscribe-section/', views.get_email_subscribe_section, name='get_email_subscribe_section'),
    path('exams-trust-bar/', views.get_exams_trust_bar, name='get_exams_trust_bar'),
    path('exams-about/', views.get_exams_about, name='get_exams_about'),
    path('top-categories-section/', views.get_top_categories_section, name='get_top_categories_section'),
    path('featured-exams-section/', views.get_featured_exams_section, name='get_featured_exams_section'),
    path('popular-providers-section/', views.get_popular_providers_section, name='get_popular_providers_section'),
    path('testimonials-section/', views.get_testimonials_section, name='get_testimonials_section'),
    path('blog-posts-section/', views.get_blog_posts_section, name='get_blog_posts_section'),
    path('recently-updated-section/', views.get_recently_updated_section, name='get_recently_updated_section'),
    path('faqs-section/', views.get_faqs_section, name='get_faqs_section'),
    
    # Admin APIs - Hero Section
    path('admin/hero/', views.manage_hero_section, name='manage_hero_section'),
    
    # Admin APIs - Value Propositions
    path('admin/value-propositions-section/', views.manage_value_propositions_section, name='manage_value_propositions_section'),
    path('admin/value-propositions/', views.manage_value_propositions, name='manage_value_propositions'),
    path('admin/value-propositions/<str:proposition_id>/', views.manage_value_proposition_by_id, name='manage_value_proposition_by_id'),
    
    # Admin APIs - Testimonials
    path('admin/testimonials/', views.manage_testimonials, name='manage_testimonials'),
    path('admin/testimonials/<str:testimonial_id>/', views.manage_testimonial_by_id, name='manage_testimonial_by_id'),
    
    # Admin APIs - Blog Posts
    path('admin/blog-posts/', views.manage_blog_posts, name='manage_blog_posts'),
    path('admin/blog-posts/<str:post_id>/', views.manage_blog_post_by_id, name='manage_blog_post_by_id'),
    
    # Admin APIs - FAQs
    path('admin/faqs/', views.manage_faqs, name='manage_faqs'),
    path('admin/faqs/<str:faq_id>/', views.manage_faq_by_id, name='manage_faq_by_id'),
    
    # Admin APIs - Recently Updated
    path('admin/recently-updated-exams/', views.manage_recently_updated_exams, name='manage_recently_updated_exams'),
    path('admin/recently-updated-exams/<str:exam_id>/', views.manage_recently_updated_exam_by_id, name='manage_recently_updated_exam_by_id'),
    
    # Admin APIs - Exams Page
    path('admin/exams-trust-bar/', views.manage_exams_trust_bar, name='manage_exams_trust_bar'),
    path('admin/exams-about/', views.manage_exams_about, name='manage_exams_about'),
    
    # Admin APIs - Email Subscribe Section
    path('admin/email-subscribe-section/', views.manage_email_subscribe_section, name='manage_email_subscribe_section'),
    path('admin/email-subscribers/', views.get_email_subscribers, name='get_email_subscribers'),
    path('admin/email-subscribers/<str:subscriber_id>/', views.manage_email_subscriber_by_id, name='manage_email_subscriber_by_id'),
    
    # Admin APIs - Top Categories Section
    path('admin/top-categories-section/', views.manage_top_categories_section, name='manage_top_categories_section'),
    
    # Admin APIs - Section Settings
    path('admin/featured-exams-section/', views.manage_featured_exams_section, name='manage_featured_exams_section'),
    path('admin/popular-providers-section/', views.manage_popular_providers_section, name='manage_popular_providers_section'),
    path('admin/testimonials-section/', views.manage_testimonials_section, name='manage_testimonials_section'),
    path('admin/blog-posts-section/', views.manage_blog_posts_section, name='manage_blog_posts_section'),
    path('admin/recently-updated-section/', views.manage_recently_updated_section, name='manage_recently_updated_section'),
    path('admin/faqs-section/', views.manage_faqs_section, name='manage_faqs_section'),
    
    # Admin APIs - Home Page SEO
    path('admin/home-page-seo/', views.manage_home_page_seo, name='manage_home_page_seo'),
    
    # Admin APIs - Exam Details SEO
    path('admin/exam-details-seo/', views.manage_exam_details_seo, name='manage_exam_details_seo'),
    
    # Admin APIs - Exams Page SEO
    path('admin/exams-page-seo/', views.manage_exams_page_seo, name='manage_exams_page_seo'),
    
    # Admin APIs - Pricing Plans SEO
    path('admin/pricing-plans-seo/', views.manage_pricing_plans_seo, name='manage_pricing_plans_seo'),
]
