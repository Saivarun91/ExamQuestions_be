# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import AllowAny
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from .models import (
#     HeroSection, ValuePropositionsSection, ValueProposition,
#     Testimonial, BlogPost, RecentlyUpdatedExam, FAQ,
#     EmailSubscribeSection, EmailSubscriber, TopCategoriesSection,
#     ExamsPageTrustBar, ExamsPageAbout
# )
# from common.middleware import authenticate, restrict
# from bson import ObjectId
# import json
# from datetime import datetime


# # =================== HERO SECTION ===================
# @csrf_exempt
# def get_hero_section(request):
#     """Get hero section data for homepage"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         hero = HeroSection.objects(is_active=True).first()
#         if not hero:
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "title": "Master Your Certification Exams",
#                     "subtitle": "Practice with real exam questions",
#                     "stats": []
#                 }
#             })

#         return JsonResponse({
#             "success": True,
#             "data": {
#                 "id": str(hero.id),
#                 "title": hero.title,
#                 "subtitle": hero.subtitle or "",
#                 "background_image_url": hero.background_image_url or "",
#                 "stats": hero.stats or [],
#                 "meta_title": hero.meta_title or "",
#                 "meta_keywords": hero.meta_keywords or "",
#                 "meta_description": hero.meta_description or "",
#             }
#         })
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @authenticate
# @restrict(['admin'])
# def manage_hero_section(request):
#     """Admin: Create/Update hero section"""
#     if request.method == 'POST' or request.method == 'PUT':
#         try:
#             data = json.loads(request.body)
            
#             # Get or create hero (only one active)
#             hero = HeroSection.objects(is_active=True).first()
#             if not hero:
#                 hero = HeroSection()
            
#             # Update fields
#             hero.title = data.get('title', hero.title)
#             hero.subtitle = data.get('subtitle', hero.subtitle)
#             hero.background_image_url = data.get('background_image_url', hero.background_image_url)
#             hero.stats = data.get('stats', hero.stats)
#             hero.meta_title = data.get('meta_title', hero.meta_title)
#             hero.meta_keywords = data.get('meta_keywords', hero.meta_keywords)
#             hero.meta_description = data.get('meta_description', hero.meta_description)
#             hero.updated_at = datetime.utcnow()
#             hero.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Hero section updated successfully",
#                 "data": {
#                     "id": str(hero.id),
#                     "title": hero.title,
#                     "subtitle": hero.subtitle or "",
#                     "background_image_url": hero.background_image_url or "",
#                     "stats": hero.stats or [],
#                     "meta_title": hero.meta_title or "",
#                     "meta_keywords": hero.meta_keywords or "",
#                     "meta_description": hero.meta_description or "",
#                 }
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'GET':
#         try:
#             hero = HeroSection.objects(is_active=True).first()
#             if not hero:
#                 return JsonResponse({"error": "Hero section not found"}, status=404)
            
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "id": str(hero.id),
#                     "title": hero.title,
#                     "subtitle": hero.subtitle or "",
#                     "background_image_url": hero.background_image_url or "",
#                     "stats": hero.stats or [],
#                     "meta_title": hero.meta_title or "",
#                     "meta_keywords": hero.meta_keywords or "",
#                     "meta_description": hero.meta_description or "",
#                 }
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


# # =================== EXAMS PAGE TRUST BAR ===================
# @csrf_exempt
# def get_exams_trust_bar(request):
#     """Get trust bar items for exams page"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
#         if not trust_bar:
#             # Default trust bar items
#             default_items = [
#                 {"icon": "CheckCircle2", "label": "94% Match", "description": "Real exam difficulty"},
#                 {"icon": "Clock", "label": "Daily Updates", "description": "Fresh content"},
#                 {"icon": "Users", "label": "Trusted by 1000s", "description": "Active learners"},
#                 {"icon": "BarChart3", "label": "Real Exam Style", "description": "Authentic questions"}
#             ]
#             return JsonResponse({"success": True, "data": default_items})
        
#         return JsonResponse({"success": True, "data": trust_bar.items or []})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @authenticate
# @restrict(['admin'])
# def manage_exams_trust_bar(request):
#     """Admin: Manage exams page trust bar"""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
            
#             trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
#             if not trust_bar:
#                 trust_bar = ExamsPageTrustBar()
            
#             trust_bar.items = data.get('items', [])
#             trust_bar.updated_at = datetime.utcnow()
#             trust_bar.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Trust bar updated successfully"
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'GET':
#         try:
#             trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
#             if not trust_bar:
#                 default_items = [
#                     {"icon": "CheckCircle2", "label": "94% Match", "description": "Real exam difficulty"},
#                     {"icon": "Clock", "label": "Daily Updates", "description": "Fresh content"},
#                     {"icon": "Users", "label": "Trusted by 1000s", "description": "Active learners"},
#                     {"icon": "BarChart3", "label": "Real Exam Style", "description": "Authentic questions"}
#                 ]
#                 return JsonResponse({"success": True, "data": default_items})
            
#             return JsonResponse({"success": True, "data": trust_bar.items or []})
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


# # =================== EXAMS PAGE ABOUT SECTION ===================
# @csrf_exempt
# def get_exams_about(request):
#     """Get about section for exams page"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         about = ExamsPageAbout.objects(is_active=True).first()
#         if not about:
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "heading": "About All Popular Exams Preparation",
#                     "content": "Preparation for certification and competitive exams requires strategic practice with high-quality questions that mirror actual exam patterns."
#                 }
#             })
        
#         return JsonResponse({
#             "success": True,
#             "data": {
#                 "heading": about.heading,
#                 "content": about.content
#             }
#         })
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @authenticate
# @restrict(['admin'])
# def manage_exams_about(request):
#     """Admin: Manage exams page about section"""
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
            
#             about = ExamsPageAbout.objects(is_active=True).first()
#             if not about:
#                 about = ExamsPageAbout()
            
#             about.heading = data.get('heading', about.heading)
#             about.content = data.get('content', about.content)
#             about.updated_at = datetime.utcnow()
#             about.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "About section updated successfully"
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'GET':
#         try:
#             about = ExamsPageAbout.objects(is_active=True).first()
#             if not about:
#                 return JsonResponse({
#                     "success": True,
#                     "data": {
#                         "heading": "About All Popular Exams Preparation",
#                         "content": "Preparation for certification and competitive exams requires strategic practice with high-quality questions that mirror actual exam patterns."
#                     }
#                 })
            
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "heading": about.heading,
#                     "content": about.content
#                 }
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


# # =================== VALUE PROPOSITIONS SECTION ===================
# @csrf_exempt
# def get_value_propositions_section(request):
#     """Get value propositions section settings"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         section = ValuePropositionsSection.objects(is_active=True).first()

#         if not section:
#             # Return defaults
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "heading": "Why Choose AllExamQuestions?",
#                     "subtitle": "Everything you need to ace your certification exam in one place",
#                     "heading_font_family": "font-bold",
#                     "heading_font_size": "text-4xl",
#                     "heading_color": "text-[#0C1A35]",
#                     "subtitle_font_size": "text-lg",
#                     "subtitle_color": "text-[#0C1A35]/70"
#                 }
#             })
        
#         return JsonResponse({
#             "success": True,
#             "data": {
#                 "id": str(section.id),
#                 "heading": section.heading,
#                 "subtitle": section.subtitle,
#                 "heading_font_family": section.heading_font_family,
#                 "heading_font_size": section.heading_font_size,
#                 "heading_color": section.heading_color,
#                 "subtitle_font_size": section.subtitle_font_size,
#                 "subtitle_color": section.subtitle_color,
#                 "meta_title": section.meta_title,
#                 "meta_keywords": section.meta_keywords,
#                 "meta_description": section.meta_description,
#             }
#         })
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =================== VALUE PROPOSITIONS ===================
# @csrf_exempt
# def get_value_propositions(request):
#     """Get all active value propositions"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         propositions = ValueProposition.objects(is_active=True).order_by('order')
#         data = []
#         for prop in propositions:
#             data.append({
#                 "id": str(prop.id),
#                 "icon": prop.icon or "",
#                 "title": prop.title,
#                 "description": prop.description or "",
#                 "order": prop.order or 0
#             })
        
#         return JsonResponse({"success": True, "data": data})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @authenticate
# @restrict(['admin'])
# def manage_value_propositions(request):
#     """Admin: Manage individual value propositions"""
#     if request.method == 'GET':
#         try:
#             propositions = ValueProposition.objects.all().order_by('order')
#             data = []
#             for prop in propositions:
#                 data.append({
#                     "id": str(prop.id),
#                     "icon": prop.icon or "",
#                     "title": prop.title,
#                     "description": prop.description or "",
#                     "order": prop.order or 0,
#                     "is_active": prop.is_active
#                 })
#             return JsonResponse({"success": True, "data": data})
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             prop = ValueProposition()
#             prop.icon = data.get('icon', '')
#             prop.title = data.get('title', '')
#             prop.description = data.get('description', '')
#             prop.order = data.get('order', 0)
#             prop.is_active = data.get('is_active', True)
#             prop.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Value proposition created successfully",
#                 "data": {"id": str(prop.id)}
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'PUT':
#         try:
#             data = json.loads(request.body)
#             prop_id = data.get('id')
#             if not prop_id:
#                 return JsonResponse({"error": "ID is required"}, status=400)
            
#             prop = ValueProposition.objects.get(id=ObjectId(prop_id))
#             prop.icon = data.get('icon', prop.icon)
#             prop.title = data.get('title', prop.title)
#             prop.description = data.get('description', prop.description)
#             prop.order = data.get('order', prop.order)
#             prop.is_active = data.get('is_active', prop.is_active)
#             prop.updated_at = datetime.utcnow()
#             prop.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Value proposition updated successfully"
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'DELETE':
#         try:
#             data = json.loads(request.body)
#             prop_id = data.get('id')
#             if not prop_id:
#                 return JsonResponse({"error": "ID is required"}, status=400)
            
#             prop = ValueProposition.objects.get(id=ObjectId(prop_id))
#             prop.delete()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Value proposition deleted successfully"
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)


# @csrf_exempt
# @authenticate
# @restrict(['admin'])
# def manage_value_propositions_section(request):
#     """Admin: Create/Update value propositions section settings"""
#     if request.method == 'POST':
#     try:
#         data = json.loads(request.body)
            
#             # Get or create section (only one active)
#             section = ValuePropositionsSection.objects(is_active=True).first()
#             if not section:
#                 section = ValuePropositionsSection()
            
#             section.heading = data.get('heading', section.heading)
#             section.subtitle = data.get('subtitle', section.subtitle)
#             section.heading_font_family = data.get('heading_font_family', section.heading_font_family)
#             section.heading_font_size = data.get('heading_font_size', section.heading_font_size)
#             section.heading_color = data.get('heading_color', section.heading_color)
#             section.subtitle_font_size = data.get('subtitle_font_size', section.subtitle_font_size)
#             section.subtitle_color = data.get('subtitle_color', section.subtitle_color)
#             section.meta_title = data.get('meta_title', section.meta_title)
#             section.meta_keywords = data.get('meta_keywords', section.meta_keywords)
#             section.meta_description = data.get('meta_description', section.meta_description)
#             section.updated_at = datetime.utcnow()
#             section.save()
            
#             return JsonResponse({
#                 "success": True,
#                 "message": "Value propositions section updated successfully",
#                 "data": {"id": str(section.id)}
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     elif request.method == 'GET':
#         try:
#             section = ValuePropositionsSection.objects(is_active=True).first()
#             if not section:
#                 return JsonResponse({"error": "Section not found"}, status=404)
            
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "id": str(section.id),
#                     "heading": section.heading,
#                     "subtitle": section.subtitle,
#                     "heading_font_family": section.heading_font_family,
#                     "heading_font_size": section.heading_font_size,
#                     "heading_color": section.heading_color,
#                     "subtitle_font_size": section.subtitle_font_size,
#                     "subtitle_color": section.subtitle_color,
#                     "meta_title": section.meta_title,
#                     "meta_keywords": section.meta_keywords,
#                     "meta_description": section.meta_description,
#                 }
#             })
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=500)
    
#     else:
#         return JsonResponse({"error": "Method not allowed"}, status=405)


# # =================== TESTIMONIALS ===================
# @csrf_exempt
# def get_testimonials(request):
#     """Get all active and featured testimonials"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         testimonials = Testimonial.objects(is_active=True, is_featured=True).order_by('-created_at')
#         data = []
#         for test in testimonials:
#             data.append({
#                 "id": str(test.id),
#                 "name": test.name,
#                 "role": test.role or "",
#                 "review": test.review,
#                 "rating": test.rating or 5,
#                 "verified": test.verified or False
#             })
        
#         return JsonResponse({"success": True, "data": data})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =================== BLOG POSTS ===================
# @csrf_exempt
# def get_blog_posts(request):
#     """Get all active and featured blog posts"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         posts = BlogPost.objects(is_active=True, is_featured=True).order_by('-created_at').limit(6)
#         data = []
#         for post in posts:
#             data.append({
#                 "id": str(post.id),
#                 "title": post.title,
#                 "excerpt": post.excerpt or "",
#                 "image_url": post.image_url or "",
#                 "category": post.category or "",
#                 "reading_time": post.reading_time or "5 min read",
#                 "created_at": post.created_at.isoformat() if post.created_at else ""
#             })
        
#         return JsonResponse({"success": True, "data": data})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =================== RECENTLY UPDATED EXAMS ===================
# @csrf_exempt
# def get_recently_updated_exams(request):
#     """Get recently updated exams"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         from courses.models import Course
#         exams = Course.objects(is_active=True).order_by('-updated_at').limit(8)
#         data = []
#         for exam in exams:
#             data.append({
#                 "id": str(exam.id),
#                 "title": exam.title,
#                 "code": exam.code,
#                 "provider": exam.provider,
#                 "slug": exam.slug,
#                 "practice_exams": exam.practice_exams or 0,
#                 "questions": exam.questions or 0,
#                 "badge": exam.badge or ""
#             })
        
#         return JsonResponse({"success": True, "data": data})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =================== FAQS ===================
# @csrf_exempt
# def get_faqs(request):
#     """Get all active FAQs"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         faqs = FAQ.objects(is_active=True).order_by('order')
#         data = []
#         for faq in faqs:
#             data.append({
#                 "id": str(faq.id),
#                 "question": faq.question,
#                 "answer": faq.answer,
#                 "order": faq.order or 0
#             })
        
#         return JsonResponse({"success": True, "data": data})
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


# # =================== EMAIL SUBSCRIBE SECTION ===================
# @csrf_exempt
# def get_email_subscribe_section(request):
#     """Get email subscribe section data"""
#     if request.method != 'GET':
#         return JsonResponse({"error": "Method not allowed"}, status=405)
    
#     try:
#         section = EmailSubscribeSection.objects(is_active=True).first()
#         if not section:
#             return JsonResponse({
#                 "success": True,
#                 "data": {
#                     "heading": "Stay Updated",
#                     "description": "Get the latest exam questions and study materials",
#                     "button_text": "Subscribe",
#                     "placeholder": "Enter your email"
#                 }
#             })
        
#         return JsonResponse({
#             "success": True,
#             "data": {
#                 "id": str(section.id),
#                 "heading": section.heading,
#                 "description": section.description or "",
#                 "button_text": section.button_text or "Subscribe",
#                 "placeholder": section.placeholder or "Enter your email"
#             }
#         })
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)






from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    HeroSection, ValuePropositionsSection, ValueProposition,
    Testimonial, BlogPost, RecentlyUpdatedExam, FAQ,
    EmailSubscribeSection, EmailSubscriber, TopCategoriesSection,
    ExamsPageTrustBar, ExamsPageAbout, PricingPlansSeo,
    FeaturedExamsSection, PopularProvidersSection, TestimonialsSection,
    BlogPostsSection, RecentlyUpdatedSection, FAQsSection,
    HomePageSeo, ExamDetailsSeo, ExamsPageSeo
)
from common.middleware import authenticate, restrict
from bson import ObjectId
import json
from datetime import datetime


# =================== HERO SECTION ===================
@csrf_exempt
def get_hero_section(request):
    """Get hero section data for homepage"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        hero = HeroSection.objects(is_active=True).first()
        if not hero:
            return JsonResponse({
                "success": True,
                "data": {
                    "title": "Master Your Certification Exams",
                    "subtitle": "Practice with real exam questions",
                    "stats": []
                }
            })

        return JsonResponse({
            "success": True,
            "data": {
                "id": str(hero.id),
                "title": hero.title,
                "subtitle": hero.subtitle or "",
                "background_image_url": hero.background_image_url or "",
                "stats": hero.stats or [],
                "meta_title": hero.meta_title or "",
                "meta_keywords": hero.meta_keywords or "",
                "meta_description": hero.meta_description or "",
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_hero_section(request):
    """Admin: Create/Update hero section"""
    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)

            # Get or create hero
            hero = HeroSection.objects(is_active=True).first()
            if not hero:
                hero = HeroSection()

            hero.title = data.get('title', hero.title)
            hero.subtitle = data.get('subtitle', hero.subtitle)
            hero.background_image_url = data.get('background_image_url', hero.background_image_url)
            hero.stats = data.get('stats', hero.stats)
            hero.meta_title = data.get('meta_title', hero.meta_title)
            hero.meta_keywords = data.get('meta_keywords', hero.meta_keywords)
            hero.meta_description = data.get('meta_description', hero.meta_description)
            hero.updated_at = datetime.utcnow()
            hero.save()

            return JsonResponse({
                "success": True,
                "message": "Hero section updated successfully",
                "data": {
                    "id": str(hero.id),
                    "title": hero.title,
                    "subtitle": hero.subtitle or "",
                    "background_image_url": hero.background_image_url or "",
                    "stats": hero.stats or [],
                    "meta_title": hero.meta_title or "",
                    "meta_keywords": hero.meta_keywords or "",
                    "meta_description": hero.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            hero = HeroSection.objects(is_active=True).first()
            if not hero:
                return JsonResponse({"error": "Hero section not found"}, status=404)

            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(hero.id),
                    "title": hero.title,
                    "subtitle": hero.subtitle or "",
                    "background_image_url": hero.background_image_url or "",
                    "stats": hero.stats or [],
                    "meta_title": hero.meta_title or "",
                    "meta_keywords": hero.meta_keywords or "",
                    "meta_description": hero.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# =================== EXAMS PAGE TRUST BAR ===================
@csrf_exempt
def get_exams_trust_bar(request):
    """Get trust bar items for exams page"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
        if not trust_bar:
            default_items = [
                {"icon": "CheckCircle2", "label": "94% Match", "description": "Real exam difficulty"},
                {"icon": "Clock", "label": "Daily Updates", "description": "Fresh content"},
                {"icon": "Users", "label": "Trusted by 1000s", "description": "Active learners"},
                {"icon": "BarChart3", "label": "Real Exam Style", "description": "Authentic questions"}
            ]
            return JsonResponse({"success": True, "data": default_items})

        return JsonResponse({"success": True, "data": trust_bar.items or []})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_exams_trust_bar(request):
    """Admin: Manage exams page trust bar"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
            if not trust_bar:
                trust_bar = ExamsPageTrustBar()

            trust_bar.items = data.get('items', [])
            trust_bar.updated_at = datetime.utcnow()
            trust_bar.save()

            return JsonResponse({
                "success": True,
                "message": "Trust bar updated successfully"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            trust_bar = ExamsPageTrustBar.objects(is_active=True).first()
            if not trust_bar:
                default_items = [
                    {"icon": "CheckCircle2", "label": "94% Match", "description": "Real exam difficulty"},
                    {"icon": "Clock", "label": "Daily Updates", "description": "Fresh content"},
                    {"icon": "Users", "label": "Trusted by 1000s", "description": "Active learners"},
                    {"icon": "BarChart3", "label": "Real Exam Style", "description": "Authentic questions"}
                ]
                return JsonResponse({"success": True, "data": default_items})

            return JsonResponse({"success": True, "data": trust_bar.items or []})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# =================== EXAMS PAGE ABOUT SECTION ===================
@csrf_exempt
def get_exams_about(request):
    """Get about section for exams page"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        about = ExamsPageAbout.objects(is_active=True).first()
        if not about:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "About All Popular Exams Preparation",
                    "content": "Preparation for certification and competitive exams requires strategic practice with high-quality questions that mirror actual exam patterns."
                }
            })

        return JsonResponse({
            "success": True,
            "data": {
                "heading": about.heading,
                "content": about.content
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_exams_about(request):
    """Admin: Manage exams page about section"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            about = ExamsPageAbout.objects(is_active=True).first()
            if not about:
                about = ExamsPageAbout()

            about.heading = data.get('heading', about.heading)
            about.content = data.get('content', about.content)
            about.updated_at = datetime.utcnow()
            about.save()

            return JsonResponse({
                "success": True,
                "message": "About section updated successfully"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            about = ExamsPageAbout.objects(is_active=True).first()
            if not about:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "About All Popular Exams Preparation",
                        "content": "Preparation for certification and competitive exams requires strategic practice with high-quality questions that mirror actual exam patterns."
                    }
                })

            return JsonResponse({
                "success": True,
                "data": {
                    "heading": about.heading,
                    "content": about.content
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


# =================== VALUE PROPOSITIONS SECTION ===================
@csrf_exempt
def get_value_propositions_section(request):
    """Get value propositions section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        section = ValuePropositionsSection.objects(is_active=True).first()

        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Why Choose AllExamQuestions?",
                    "subtitle": "Everything you need to ace your certification exam in one place",
                    "heading_font_family": "font-bold",
                    "heading_font_size": "text-4xl",
                    "heading_color": "text-[#0C1A35]",
                    "subtitle_font_size": "text-lg",
                    "subtitle_color": "text-[#0C1A35]/70"
                }
            })

        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle,
                "heading_font_family": section.heading_font_family,
                "heading_font_size": section.heading_font_size,
                "heading_color": section.heading_color,
                "subtitle_font_size": section.subtitle_font_size,
                "subtitle_color": section.subtitle_color,
                "meta_title": section.meta_title,
                "meta_keywords": section.meta_keywords,
                "meta_description": section.meta_description,
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== VALUE PROPOSITIONS ===================
@csrf_exempt
def get_value_propositions(request):
    """Get all active value propositions"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        propositions = ValueProposition.objects(is_active=True).order_by('order')
        data = []
        for prop in propositions:
            data.append({
                "id": str(prop.id),
                "icon": prop.icon or "",
                "title": prop.title,
                "description": prop.description or "",
                "order": prop.order or 0
            })

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_value_propositions(request):
    """Admin: Manage individual value propositions"""
    if request.method == 'GET':
        try:
            propositions = ValueProposition.objects.all().order_by('order')
            data = []
            for prop in propositions:
                data.append({
                    "id": str(prop.id),
                    "icon": prop.icon or "",
                    "title": prop.title,
                    "description": prop.description or "",
                    "order": prop.order or 0,
                    "is_active": prop.is_active
                })
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            prop = ValueProposition()

            prop.icon = data.get('icon', '')
            prop.title = data.get('title', '')
            prop.description = data.get('description', '')
            prop.order = data.get('order', 0)
            prop.is_active = data.get('is_active', True)
            prop.save()

            return JsonResponse({
                "success": True,
                "message": "Value proposition created successfully",
                "data": {"id": str(prop.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            prop_id = data.get('id')
            if not prop_id:
                return JsonResponse({"error": "ID is required"}, status=400)

            prop = ValueProposition.objects.get(id=ObjectId(prop_id))
            prop.icon = data.get('icon', prop.icon)
            prop.title = data.get('title', prop.title)
            prop.description = data.get('description', prop.description)
            prop.order = data.get('order', prop.order)
            prop.is_active = data.get('is_active', prop.is_active)
            prop.updated_at = datetime.utcnow()
            prop.save()

            return JsonResponse({
                "success": True,
                "message": "Value proposition updated successfully"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            prop_id = data.get('id')
            if not prop_id:
                return JsonResponse({"error": "ID is required"}, status=400)

            prop = ValueProposition.objects.get(id=ObjectId(prop_id))
            prop.delete()

            return JsonResponse({
                "success": True,
                "message": "Value proposition deleted successfully"
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_value_proposition_by_id(request, proposition_id):
    """Admin: Update or delete a specific value proposition by ID"""
    try:
        if not ObjectId.is_valid(proposition_id):
            return JsonResponse({"error": "Invalid proposition ID"}, status=400)
        
        prop = ValueProposition.objects.get(id=ObjectId(proposition_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            prop.icon = data.get('icon', prop.icon)
            prop.title = data.get('title', prop.title)
            prop.description = data.get('description', prop.description)
            prop.order = data.get('order', prop.order)
            prop.is_active = data.get('is_active', prop.is_active)
            prop.updated_at = datetime.utcnow()
            prop.save()
            
            return JsonResponse({
                "success": True,
                "message": "Value proposition updated successfully"
            })
        
        elif request.method == 'DELETE':
            prop.delete()
            return JsonResponse({
                "success": True,
                "message": "Value proposition deleted successfully"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except ValueProposition.DoesNotExist:
        return JsonResponse({"error": "Value proposition not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_value_propositions_section(request):
    """Admin: Create/Update value propositions section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            section = ValuePropositionsSection.objects(is_active=True).first()
            if not section:
                section = ValuePropositionsSection()

            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.heading_font_family = data.get('heading_font_family', section.heading_font_family)
            section.heading_font_size = data.get('heading_font_size', section.heading_font_size)
            section.heading_color = data.get('heading_color', section.heading_color)
            section.subtitle_font_size = data.get('subtitle_font_size', section.subtitle_font_size)
            section.subtitle_color = data.get('subtitle_color', section.subtitle_color)
            section.meta_title = data.get('meta_title', section.meta_title)
            section.meta_keywords = data.get('meta_keywords', section.meta_keywords)
            section.meta_description = data.get('meta_description', section.meta_description)
            section.updated_at = datetime.utcnow()
            section.save()

            return JsonResponse({
                "success": True,
                "message": "Value propositions section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            section = ValuePropositionsSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({"error": "Section not found"}, status=404)

            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle,
                    "heading_font_family": section.heading_font_family,
                    "heading_font_size": section.heading_font_size,
                    "heading_color": section.heading_color,
                    "subtitle_font_size": section.subtitle_font_size,
                    "subtitle_color": section.subtitle_color,
                    "meta_title": section.meta_title,
                    "meta_keywords": section.meta_keywords,
                    "meta_description": section.meta_description,
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== TESTIMONIALS ===================
@csrf_exempt
def get_testimonials(request):
    """Get all active testimonials (featured and non-featured), including reviews marked as testimonials"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        from reviews.models import Review
        
        data = []
        seen_texts = set()  # Track seen testimonial text to avoid duplicates
        
        # Get ALL active testimonials (not just featured) - changed for testimonials page
        # Check if requesting all testimonials via query param
        get_all = request.GET.get('all', 'false').lower() == 'true'
        if get_all:
            testimonials = Testimonial.objects(is_active=True).order_by('-is_featured', '-created_at')
        else:
            # Default: only featured testimonials for home page
            testimonials = Testimonial.objects(is_active=True, is_featured=True).order_by('-created_at')
        for test in testimonials:
            testimonial_text = test.text.strip().lower()
            if testimonial_text in seen_texts:
                continue
            seen_texts.add(testimonial_text)
            
            data.append({
                "id": str(test.id),
                "name": test.name,
                "role": test.role or "",
                "review": test.text,
                "text": test.text,
                "rating": test.rating or 5,
                "verified": getattr(test, 'verified', False),
                "source": "testimonial"  # Mark as admin-created
            })
        
        # Get reviews marked as testimonials
        review_testimonials = Review.objects(
            is_approved=True, 
            is_active=True, 
            is_testimonial=True
        ).order_by('-rating', '-created_at')
        
        for review in review_testimonials:
            # Get user info
            user_name = "Student"
            user_role = "Student"
            try:
                if review.user:
                    user_name = getattr(review.user, 'fullname', None) or getattr(review.user, 'email', 'Student')
                    # Try to get role from course if available
                    if hasattr(review, 'course') and review.course:
                        user_role = f"{review.course.title} Student"
            except:
                pass
            
            review_text = (review.text or review.comment or "").strip().lower()
            if review_text in seen_texts:
                continue
            seen_texts.add(review_text)
            
            data.append({
                "id": f"review_{str(review.id)}",
                "name": user_name,
                "role": user_role,
                "review": review.text or review.comment or "",
                "text": review.text or review.comment or "",
                "rating": review.rating or 5,
                "verified": True,  # Reviews marked as testimonials are verified
                "source": "review"  # Mark as from review
            })

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_testimonials(request):
    """Admin: Manage testimonials (GET all, POST create, PUT update, DELETE)"""
    if request.method == 'GET':
        try:
            testimonials = Testimonial.objects.all().order_by('-created_at')
            data = []
            for test in testimonials:
                data.append({
                    "id": str(test.id),
                    "name": test.name,
                    "role": test.role or "",
                    "review": test.text,  # Model field is 'text'
                    "rating": test.rating or 5,
                    "verified": getattr(test, 'verified', False),  # Field doesn't exist in model
                    "is_active": test.is_active,
                    "is_featured": test.is_featured or False
                })
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            print("err : ", e);
            return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            testimonial = Testimonial()
            testimonial.name = data.get('name', '')
            testimonial.role = data.get('role', '')
            testimonial.text = data.get('review', data.get('text', ''))  # Model field is 'text'
            testimonial.rating = data.get('rating', 5)
            testimonial.is_active = data.get('is_active', True)
            testimonial.is_featured = data.get('is_featured', False)
            testimonial.save()
            
            return JsonResponse({
                "success": True,
                "message": "Testimonial created successfully",
                "data": {"id": str(testimonial.id)}
            })
        except Exception as e:
            print("err : ", e);
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_testimonial_by_id(request, testimonial_id):
    """Admin: Update or delete a specific testimonial by ID"""
    try:
        if not ObjectId.is_valid(testimonial_id):
            return JsonResponse({"error": "Invalid testimonial ID"}, status=400)
        
        testimonial = Testimonial.objects.get(id=ObjectId(testimonial_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            testimonial.name = data.get('name', testimonial.name)
            testimonial.role = data.get('role', testimonial.role)
            testimonial.text = data.get('review', data.get('text', testimonial.text))  # Model field is 'text'
            testimonial.rating = data.get('rating', testimonial.rating)
            testimonial.is_active = data.get('is_active', testimonial.is_active)
            testimonial.is_featured = data.get('is_featured', testimonial.is_featured)
            testimonial.updated_at = datetime.utcnow()
            testimonial.save()
            
            return JsonResponse({
                "success": True,
                "message": "Testimonial updated successfully"
            })
        
        elif request.method == 'DELETE':
            testimonial.delete()
            return JsonResponse({
                "success": True,
                "message": "Testimonial deleted successfully"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except Testimonial.DoesNotExist:
        return JsonResponse({"error": "Testimonial not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== BLOG POSTS ===================
@csrf_exempt
def get_blog_posts(request):
    """Get all active and featured blog posts for homepage"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        # Get all active and featured blog posts (no limit, show all)
        posts = BlogPost.objects(is_active=True, is_featured=True).order_by('-created_at')
        data = []
        for post in posts:
            data.append({
                "id": str(post.id),
                "title": post.title,
                "excerpt": post.excerpt or "",
                "content": post.content or "",  # Include content for detail page
                "image_url": post.thumbnail_url or post.image_url or "",  # Try both fields
                "slug": post.slug,
                "category": post.category or "",
                "reading_time": getattr(post, 'reading_time', '5 min read'),
                "created_at": post.created_at.isoformat() if post.created_at else "",
                "is_featured": post.is_featured,
                "is_active": post.is_active,
                "meta_title": getattr(post, 'meta_title', '') or post.title,
                "meta_description": getattr(post, 'meta_description', '') or post.excerpt
            })

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def get_blog_post_by_slug(request, slug):
    """Get a single blog post by slug for detail page"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        from urllib.parse import unquote
        slug = unquote(slug).lower().strip()
        
        post = BlogPost.objects(slug=slug, is_active=True).first()
        if not post:
            return JsonResponse({"error": "Blog post not found"}, status=404)
        
        data = {
            "id": str(post.id),
            "title": post.title,
            "excerpt": post.excerpt or "",
            "content": post.content or "",
            "image_url": post.thumbnail_url or post.image_url or "",
            "slug": post.slug,
            "category": post.category or "",
            "reading_time": getattr(post, 'reading_time', '5 min read'),
            "created_at": post.created_at.isoformat() if post.created_at else "",
            "updated_at": post.updated_at.isoformat() if post.updated_at else "",
            "is_featured": post.is_featured,
            "is_active": post.is_active,
            "meta_title": getattr(post, 'meta_title', '') or post.title,
            "meta_description": getattr(post, 'meta_description', '') or post.excerpt,
            "meta_keywords": getattr(post, 'meta_keywords', '') or ""
        }

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_blog_posts(request):
    """Admin: Manage blog posts"""
    if request.method == 'GET':
        try:
            posts = BlogPost.objects.all().order_by('-created_at')
            data = []
            for post in posts:
                data.append({
                    "id": str(post.id),
                    "title": post.title,
                    "excerpt": post.excerpt or "",
                    "image_url": post.thumbnail_url or post.image_url or "",  # Try both fields
                    "thumbnail_url": post.thumbnail_url or "",
                    "slug": post.slug,
                    "category": post.category or "",
                    "reading_time": getattr(post, 'reading_time', '5 min read'),
                    "is_active": post.is_active,
                    "is_featured": post.is_featured or False,
                    "created_at": post.created_at.isoformat() if post.created_at else "",
                    "meta_title": getattr(post, 'meta_title', '') or "",
                    "meta_keywords": getattr(post, 'meta_keywords', '') or "",
                    "meta_description": getattr(post, 'meta_description', '') or ""
                })
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Generate slug from title if not provided
            title = data.get('title', '')
            slug = data.get('slug', '')
            if not slug and title:
                import re
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
                # Ensure unique slug
                base_slug = slug
                counter = 1
                while BlogPost.objects(slug=slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
            
            post = BlogPost()
            post.title = title
            post.excerpt = data.get('excerpt', '')
            post.slug = slug
            post.content = data.get('content', '')
            post.image_url = data.get('image_url', '')
            post.thumbnail_url = data.get('thumbnail_url', data.get('image_url', ''))
            post.category = data.get('category', '')
            post.reading_time = data.get('reading_time', '5 min read')
            post.is_active = data.get('is_active', True)
            post.is_featured = data.get('is_featured', False)
            post.meta_title = data.get('meta_title', '')
            post.meta_keywords = data.get('meta_keywords', '')
            post.meta_description = data.get('meta_description', '')
            post.save()
            
            return JsonResponse({
                "success": True,
                "message": "Blog post created successfully",
                "data": {"id": str(post.id), "slug": post.slug}
            })
        except Exception as e:
            print("Blog post creation error:", e)
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_blog_post_by_id(request, post_id):
    """Admin: Update or delete a specific blog post by ID"""
    try:
        if not ObjectId.is_valid(post_id):
            return JsonResponse({"error": "Invalid post ID"}, status=400)
        
        post = BlogPost.objects.get(id=ObjectId(post_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            post.title = data.get('title', post.title)
            post.excerpt = data.get('excerpt', post.excerpt)
            
            # Handle image URL (both thumbnail_url and image_url for compatibility)
            if 'image_url' in data or 'thumbnail_url' in data:
                post.thumbnail_url = data.get('image_url', data.get('thumbnail_url', post.thumbnail_url))
                post.image_url = post.thumbnail_url  # Keep both in sync
            
            post.category = data.get('category', post.category)
            
            if 'reading_time' in data:
                post.reading_time = data.get('reading_time', post.reading_time)
            
            # Update slug if provided or title changed
            if 'slug' in data:
                post.slug = data['slug']
            elif 'title' in data and data['title'] != post.title:
                import re
                new_slug = re.sub(r'[^a-z0-9]+', '-', data['title'].lower()).strip('-')
                # Ensure unique slug
                base_slug = new_slug
                counter = 1
                while BlogPost.objects(slug=new_slug, id__ne=post.id).first():
                    new_slug = f"{base_slug}-{counter}"
                    counter += 1
                post.slug = new_slug
            
            post.content = data.get('content', post.content)
            post.is_active = data.get('is_active', post.is_active)
            post.is_featured = data.get('is_featured', post.is_featured)
            post.meta_title = data.get('meta_title', post.meta_title)
            post.meta_keywords = data.get('meta_keywords', post.meta_keywords)
            post.meta_description = data.get('meta_description', post.meta_description)
            post.updated_at = datetime.utcnow()
            post.save()
            
            return JsonResponse({
                "success": True,
                "message": "Blog post updated successfully"
            })
        
        elif request.method == 'DELETE':
            post.delete()
            return JsonResponse({
                "success": True,
                "message": "Blog post deleted successfully"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except BlogPost.DoesNotExist:
        return JsonResponse({"error": "Blog post not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== RECENTLY UPDATED EXAMS ===================
@csrf_exempt
def get_recently_updated_exams(request):
    """Get recently updated exams"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        from courses.models import Course
        exams = Course.objects(is_active=True).order_by('-updated_at').limit(8)
        data = []
        for exam in exams:
            # Get provider name (handle both ReferenceField and string)
            provider_name = exam.provider
            if hasattr(exam.provider, 'name'):
                provider_name = exam.provider.name
            elif isinstance(exam.provider, str):
                provider_name = exam.provider
            else:
                provider_name = str(exam.provider) if exam.provider else "Unknown"
            
            data.append({
                "id": str(exam.id),
                "title": exam.title,
                "code": exam.code,
                "provider": provider_name,
                "slug": exam.slug,
                "practice_exams": exam.practice_exams or 0,
                "questions": exam.questions or 0,
                "badge": exam.badge or "Recently Updated",
                "is_active": exam.is_active
            })

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_recently_updated_exams(request):
    """Admin: Manage recently updated exams"""
    if request.method == 'GET':
        try:
            from courses.models import Course
            exams = Course.objects.all().order_by('-updated_at')
            data = []
            for exam in exams:
                data.append({
                    "id": str(exam.id),
                    "title": exam.title,
                    "code": exam.code,
                    "provider": exam.provider,
                    "slug": exam.slug,
                    "practice_exams": exam.practice_exams or 0,
                    "questions": exam.questions or 0,
                    "badge": exam.badge or "",
                    "is_active": exam.is_active
                })
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_recently_updated_exam_by_id(request, exam_id):
    """Admin: Update or delete a recently updated exam entry"""
    try:
        from courses.models import Course
        
        if not ObjectId.is_valid(exam_id):
            return JsonResponse({"error": "Invalid exam ID"}, status=400)
        
        exam = Course.objects.get(id=ObjectId(exam_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            if 'badge' in data:
                exam.badge = data.get('badge', exam.badge)
            if 'is_active' in data:
                exam.is_active = data.get('is_active', exam.is_active)
            exam.updated_at = datetime.utcnow()
            exam.save()
            
            return JsonResponse({
                "success": True,
                "message": "Exam updated successfully"
            })
        
        elif request.method == 'DELETE':
            # Don't actually delete the course, just remove from recently updated
            exam.badge = None
            exam.save()
            return JsonResponse({
                "success": True,
                "message": "Exam removed from recently updated"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except Course.DoesNotExist:
        return JsonResponse({"error": "Exam not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== FAQS ===================
@csrf_exempt
def get_faqs(request):
    """Get all active FAQs"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        faqs = FAQ.objects(is_active=True).order_by('order')
        data = []
        for faq in faqs:
            data.append({
                "id": str(faq.id),
                "question": faq.question,
                "answer": faq.answer,
                "category": faq.category or "General",
                "order": faq.order or 0
            })

        return JsonResponse({"success": True, "data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_faqs(request):
    """Admin: Manage FAQs"""
    if request.method == 'GET':
        try:
            faqs = FAQ.objects.all().order_by('order')
            data = []
            for faq in faqs:
                data.append({
                    "id": str(faq.id),
                    "question": faq.question,
                    "answer": faq.answer,
                    "order": faq.order or 0,
                    "is_active": faq.is_active
                })
            return JsonResponse({"success": True, "data": data})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            faq = FAQ()
            faq.question = data.get('question', '')
            faq.answer = data.get('answer', '')
            faq.order = data.get('order', 0)
            faq.is_active = data.get('is_active', True)
            faq.save()
            
            return JsonResponse({
                "success": True,
                "message": "FAQ created successfully",
                "data": {"id": str(faq.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_faq_by_id(request, faq_id):
    """Admin: Update or delete a specific FAQ by ID"""
    try:
        if not ObjectId.is_valid(faq_id):
            return JsonResponse({"error": "Invalid FAQ ID"}, status=400)
        
        faq = FAQ.objects.get(id=ObjectId(faq_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            faq.question = data.get('question', faq.question)
            faq.answer = data.get('answer', faq.answer)
            faq.order = data.get('order', faq.order)
            faq.is_active = data.get('is_active', faq.is_active)
            faq.updated_at = datetime.utcnow()
            faq.save()
            
            return JsonResponse({
                "success": True,
                "message": "FAQ updated successfully"
            })
        
        elif request.method == 'DELETE':
            faq.delete()
            return JsonResponse({
                "success": True,
                "message": "FAQ deleted successfully"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except FAQ.DoesNotExist:
        return JsonResponse({"error": "FAQ not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== EMAIL SUBSCRIBE SECTION ===================
@csrf_exempt
def get_email_subscribe_section(request):
    """Get email subscribe section data"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        section = EmailSubscribeSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "title": "Get Free Weekly Exam Updates",
                    "subtitle": "Latest dumps, new questions & exam alerts delivered to your inbox",
                    "button_text": "Subscribe",
                    "privacy_text": "No spam. Unsubscribe anytime. Your privacy is protected."
                }
            })

        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "title": getattr(section, 'title', section.heading) or "Get Free Weekly Exam Updates",
                "subtitle": getattr(section, 'subtitle', None) or section.subtitle or "Latest dumps, new questions & exam alerts delivered to your inbox",
                "button_text": section.button_text or "Subscribe",
                "privacy_text": getattr(section, 'privacy_text', None) or "No spam. Unsubscribe anytime. Your privacy is protected."
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_email_subscribe_section(request):
    """Admin: Get/Update email subscribe section"""
    if request.method == 'GET':
        try:
            section = EmailSubscribeSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "title": "",
                        "subtitle": "",
                        "button_text": "",
                        "privacy_text": ""
                    }
                })

            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "title": getattr(section, 'title', section.heading) or "",
                    "subtitle": getattr(section, 'subtitle', None) or section.subtitle or "",
                    "button_text": section.button_text or "",
                    "privacy_text": getattr(section, 'privacy_text', None) or ""
                }
            })
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get or create section
            section = EmailSubscribeSection.objects(is_active=True).first()
            if not section:
                section = EmailSubscribeSection()
            
            # Update fields - support both old (heading) and new (title) field names
            if 'title' in data:
                section.heading = data['title']  # Store in heading for backward compatibility
                section.title = data['title']  # Also store in title field
            if 'subtitle' in data:
                section.subtitle = data['subtitle']
            if 'button_text' in data:
                section.button_text = data['button_text']
            if 'privacy_text' in data:
                section.privacy_text = data['privacy_text']
            
            section.updated_at = datetime.utcnow()
            section.save()

            return JsonResponse({
                "success": True,
                "message": "Email subscribe section updated successfully",
                "data": {
                    "id": str(section.id),
                    "title": getattr(section, 'title', section.heading) or "",
                    "subtitle": section.subtitle or "",
                    "button_text": section.button_text or "",
                    "privacy_text": getattr(section, 'privacy_text', None) or ""
                }
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"success": False, "error": str(e)}, status=500)

    return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_email_subscribers(request):
    """Admin: Get all email subscribers"""
    if request.method != 'GET':
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)

    try:
        subscribers = EmailSubscriber.objects().order_by('-subscribed_at')
        
        subscribers_data = []
        for subscriber in subscribers:
            subscribers_data.append({
                "id": str(subscriber.id),
                "email": subscriber.email,
                "is_active": subscriber.is_active,
                "subscribed_at": subscriber.subscribed_at.isoformat() if subscriber.subscribed_at else None
            })

        return JsonResponse({
            "success": True,
            "subscribers": subscribers_data,
            "total": len(subscribers_data),
            "active": len([s for s in subscribers_data if s['is_active']])
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_email_subscriber_by_id(request, subscriber_id):
    """Admin: Update or delete a specific email subscriber by ID"""
    try:
        if not ObjectId.is_valid(subscriber_id):
            return JsonResponse({"error": "Invalid subscriber ID"}, status=400)
        
        subscriber = EmailSubscriber.objects.get(id=ObjectId(subscriber_id))
        
        if request.method == 'PUT':
            data = json.loads(request.body)
            
            # Check if email is being updated and if it already exists
            if 'email' in data and data['email'] != subscriber.email:
                existing = EmailSubscriber.objects(email=data['email']).first()
                if existing and str(existing.id) != subscriber_id:
                    return JsonResponse({"error": "Email already exists"}, status=400)
                subscriber.email = data['email']
            
            if 'is_active' in data:
                subscriber.is_active = data['is_active']
            
            subscriber.updated_at = datetime.utcnow()
            subscriber.save()
            
            return JsonResponse({
                "success": True,
                "message": "Subscriber updated successfully",
                "data": {
                    "id": str(subscriber.id),
                    "email": subscriber.email,
                    "is_active": subscriber.is_active,
                    "subscribed_at": subscriber.subscribed_at.isoformat() if subscriber.subscribed_at else None
                }
            })
        
        elif request.method == 'DELETE':
            subscriber.delete()
            return JsonResponse({
                "success": True,
                "message": "Subscriber deleted successfully"
            })
        
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)
    
    except EmailSubscriber.DoesNotExist:
        return JsonResponse({"error": "Subscriber not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"error": str(e)}, status=500)


# =================== TOP CATEGORIES SECTION ===================
@csrf_exempt
def get_top_categories_section(request):
    """Get top categories section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)

    try:
        section = TopCategoriesSection.objects(is_active=True).first()

        if not section:
            # Return defaults
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Top Certification Categories",
                    "subtitle": "Explore certifications by category",
                    "heading_font_family": "font-bold",
                    "heading_font_size": "text-4xl",
                    "heading_color": "text-[#0C1A35]",
                    "subtitle_font_size": "text-lg",
                    "subtitle_color": "text-[#0C1A35]/70"
                }
            })

        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle,
                "heading_font_family": section.heading_font_family,
                "heading_font_size": section.heading_font_size,
                "heading_color": section.heading_color,
                "subtitle_font_size": section.subtitle_font_size,
                "subtitle_color": section.subtitle_color,
                "meta_title": section.meta_title,
                "meta_keywords": section.meta_keywords,
                "meta_description": section.meta_description,
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== FEATURED EXAMS SECTION ===================
@csrf_exempt
def get_featured_exams_section(request):
    """Get featured exams section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = FeaturedExamsSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Featured Certification Exams",
                    "subtitle": "Explore our most popular certification exams"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== POPULAR PROVIDERS SECTION ===================
@csrf_exempt
def get_popular_providers_section(request):
    """Get popular providers section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = PopularProvidersSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Popular Certification Providers",
                    "subtitle": "Trusted by professionals worldwide"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== TESTIMONIALS SECTION ===================
@csrf_exempt
def get_testimonials_section(request):
    """Get testimonials section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = TestimonialsSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "What Our Students Say",
                    "subtitle": "Real feedback from successful exam takers"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== BLOG POSTS SECTION ===================
@csrf_exempt
def get_blog_posts_section(request):
    """Get blog posts section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = BlogPostsSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Latest Blog Posts",
                    "subtitle": "Stay updated with certification tips and news"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== RECENTLY UPDATED SECTION ===================
@csrf_exempt
def get_recently_updated_section(request):
    """Get recently updated section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = RecentlyUpdatedSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Recently Updated Exams",
                    "subtitle": "Stay current with the latest exam updates"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# =================== FAQS SECTION ===================
@csrf_exempt
def get_faqs_section(request):
    """Get FAQs section settings"""
    if request.method != 'GET':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    try:
        section = FAQsSection.objects(is_active=True).first()
        if not section:
            return JsonResponse({
                "success": True,
                "data": {
                    "heading": "Frequently Asked Questions",
                    "subtitle": "Find answers to common questions"
                }
            })
        return JsonResponse({
            "success": True,
            "data": {
                "id": str(section.id),
                "heading": section.heading,
                "subtitle": section.subtitle
            }
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_top_categories_section(request):
    """Admin: Create/Update top categories section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            section = TopCategoriesSection.objects(is_active=True).first()
            if not section:
                section = TopCategoriesSection()

            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.heading_font_family = data.get('heading_font_family', section.heading_font_family)
            section.heading_font_size = data.get('heading_font_size', section.heading_font_size)
            section.heading_color = data.get('heading_color', section.heading_color)
            section.subtitle_font_size = data.get('subtitle_font_size', section.subtitle_font_size)
            section.subtitle_color = data.get('subtitle_color', section.subtitle_color)
            section.meta_title = data.get('meta_title', section.meta_title)
            section.meta_keywords = data.get('meta_keywords', section.meta_keywords)
            section.meta_description = data.get('meta_description', section.meta_description)
            section.updated_at = datetime.utcnow()
            section.save()

            return JsonResponse({
                "success": True,
                "message": "Top categories section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    elif request.method == 'GET':
        try:
            section = TopCategoriesSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Top Certification Categories",
                        "subtitle": "Explore certifications by category",
                        "heading_font_family": "font-bold",
                        "heading_font_size": "text-4xl",
                        "heading_color": "text-[#0C1A35]",
                        "subtitle_font_size": "text-lg",
                        "subtitle_color": "text-[#0C1A35]/70",
                        "meta_title": "",
                        "meta_keywords": "",
                        "meta_description": "",
                    }
                })

            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle,
                    "heading_font_family": section.heading_font_family,
                    "heading_font_size": section.heading_font_size,
                    "heading_color": section.heading_color,
                    "subtitle_font_size": section.subtitle_font_size,
                    "subtitle_color": section.subtitle_color,
                    "meta_title": section.meta_title,
                    "meta_keywords": section.meta_keywords,
                    "meta_description": section.meta_description,
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== FEATURED EXAMS SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_featured_exams_section(request):
    """Admin: Create/Update featured exams section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = FeaturedExamsSection.objects(is_active=True).first()
            if not section:
                section = FeaturedExamsSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "Featured exams section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = FeaturedExamsSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Featured Certification Exams",
                        "subtitle": "Explore our most popular certification exams"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== POPULAR PROVIDERS SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_popular_providers_section(request):
    """Admin: Create/Update popular providers section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = PopularProvidersSection.objects(is_active=True).first()
            if not section:
                section = PopularProvidersSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "Popular providers section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = PopularProvidersSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Popular Certification Providers",
                        "subtitle": "Trusted by professionals worldwide"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== TESTIMONIALS SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_testimonials_section(request):
    """Admin: Create/Update testimonials section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = TestimonialsSection.objects(is_active=True).first()
            if not section:
                section = TestimonialsSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "Testimonials section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = TestimonialsSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "What Our Students Say",
                        "subtitle": "Real feedback from successful exam takers"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== BLOG POSTS SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_blog_posts_section(request):
    """Admin: Create/Update blog posts section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = BlogPostsSection.objects(is_active=True).first()
            if not section:
                section = BlogPostsSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "Blog posts section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = BlogPostsSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Latest Blog Posts",
                        "subtitle": "Stay updated with certification tips and news"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== RECENTLY UPDATED SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_recently_updated_section(request):
    """Admin: Create/Update recently updated section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = RecentlyUpdatedSection.objects(is_active=True).first()
            if not section:
                section = RecentlyUpdatedSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "Recently updated section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = RecentlyUpdatedSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Recently Updated Exams",
                        "subtitle": "Stay current with the latest exam updates"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== FAQS SECTION (ADMIN) ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_faqs_section(request):
    """Admin: Create/Update FAQs section settings"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            section = FAQsSection.objects(is_active=True).first()
            if not section:
                section = FAQsSection()
            section.heading = data.get('heading', section.heading)
            section.subtitle = data.get('subtitle', section.subtitle)
            section.updated_at = datetime.utcnow()
            section.save()
            return JsonResponse({
                "success": True,
                "message": "FAQs section updated successfully",
                "data": {"id": str(section.id)}
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            section = FAQsSection.objects(is_active=True).first()
            if not section:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "heading": "Frequently Asked Questions",
                        "subtitle": "Find answers to common questions"
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(section.id),
                    "heading": section.heading,
                    "subtitle": section.subtitle
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== HOME PAGE SEO ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_home_page_seo(request):
    """Admin: Create/Update home page SEO meta information"""
    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)
            seo = HomePageSeo.objects(is_active=True).first()
            if not seo:
                seo = HomePageSeo()
            seo.meta_title = data.get('meta_title', seo.meta_title)
            seo.meta_keywords = data.get('meta_keywords', seo.meta_keywords)
            seo.meta_description = data.get('meta_description', seo.meta_description)
            seo.updated_at = datetime.utcnow()
            seo.save()
            return JsonResponse({
                "success": True,
                "message": "Home page SEO updated successfully",
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            seo = HomePageSeo.objects(is_active=True).first()
            if not seo:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "meta_title": "",
                        "meta_keywords": "",
                        "meta_description": "",
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== EXAM DETAILS SEO ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_exam_details_seo(request):
    """Admin: Create/Update exam details page SEO meta information"""
    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)
            seo = ExamDetailsSeo.objects(is_active=True).first()
            if not seo:
                seo = ExamDetailsSeo()
            seo.meta_title = data.get('meta_title', seo.meta_title)
            seo.meta_keywords = data.get('meta_keywords', seo.meta_keywords)
            seo.meta_description = data.get('meta_description', seo.meta_description)
            seo.updated_at = datetime.utcnow()
            seo.save()
            return JsonResponse({
                "success": True,
                "message": "Exam details SEO updated successfully",
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            seo = ExamDetailsSeo.objects(is_active=True).first()
            if not seo:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "meta_title": "",
                        "meta_keywords": "",
                        "meta_description": "",
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== EXAMS PAGE SEO ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_exams_page_seo(request):
    """Admin: Create/Update exams page SEO meta information"""
    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)
            seo = ExamsPageSeo.objects(is_active=True).first()
            if not seo:
                seo = ExamsPageSeo()
            seo.meta_title = data.get('meta_title', seo.meta_title)
            seo.meta_keywords = data.get('meta_keywords', seo.meta_keywords)
            seo.meta_description = data.get('meta_description', seo.meta_description)
            seo.updated_at = datetime.utcnow()
            seo.save()
            return JsonResponse({
                "success": True,
                "message": "Exams page SEO updated successfully",
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            seo = ExamsPageSeo.objects(is_active=True).first()
            if not seo:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "meta_title": "",
                        "meta_keywords": "",
                        "meta_description": "",
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)


# =================== PRICING PLANS SEO ===================
@csrf_exempt
@authenticate
@restrict(['admin'])
def manage_pricing_plans_seo(request):
    """Admin: Create/Update pricing plans page SEO meta information"""
    if request.method in ['POST', 'PUT']:
        try:
            data = json.loads(request.body)
            seo = PricingPlansSeo.objects(is_active=True).first()
            if not seo:
                seo = PricingPlansSeo()
            seo.meta_title = data.get('meta_title', seo.meta_title)
            seo.meta_keywords = data.get('meta_keywords', seo.meta_keywords)
            seo.meta_description = data.get('meta_description', seo.meta_description)
            seo.updated_at = datetime.utcnow()
            seo.save()
            return JsonResponse({
                "success": True,
                "message": "Pricing plans SEO updated successfully",
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    elif request.method == 'GET':
        try:
            seo = PricingPlansSeo.objects(is_active=True).first()
            if not seo:
                return JsonResponse({
                    "success": True,
                    "data": {
                        "meta_title": "",
                        "meta_keywords": "",
                        "meta_description": "",
                    }
                })
            return JsonResponse({
                "success": True,
                "data": {
                    "id": str(seo.id),
                    "meta_title": seo.meta_title or "",
                    "meta_keywords": seo.meta_keywords or "",
                    "meta_description": seo.meta_description or "",
                }
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
