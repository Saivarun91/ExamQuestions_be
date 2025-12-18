from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.text import slugify

from courses.models import Course
from categories.models import Category
from providers.models import Provider
from home.models import BlogPost

def sitemap_view(request):
    urls = []
    base_url = "https://allexamquestions.com"

    # Static pages (frontend routes)
    static_urls = [
        {"path": "", "priority": "1.0", "changefreq": "daily"},
        {"path": "exams", "priority": "0.9", "changefreq": "daily"},
        {"path": "blog", "priority": "0.8", "changefreq": "daily"},
        {"path": "faq", "priority": "0.8", "changefreq": "weekly"},
        {"path": "testimonials", "priority": "0.7", "changefreq": "weekly"},
    ]

    for static_url in static_urls:
        urls.append({
            "loc": f"{base_url}/{static_url['path']}",
            "lastmod": now().date(),
            "changefreq": static_url["changefreq"],
            "priority": static_url["priority"],
        })

    # Blog Posts
    try:
        for blog_post in BlogPost.objects(is_active=True):
            urls.append({
                "loc": f"{base_url}/blog/{blog_post.slug}",
                "lastmod": blog_post.updated_at.date() if blog_post.updated_at else blog_post.created_at.date() if blog_post.created_at else now().date(),
                "changefreq": "weekly",
                "priority": "0.8",
            })
    except Exception as e:
        pass  # Continue if BlogPost model not available

    # Categories
    try:
        for category in Category.objects.all():
            urls.append({
                "loc": f"{base_url}/categories/{category.slug}",
                "lastmod": now().date(),
                "changefreq": "weekly",
                "priority": "0.8",
            })
    except Exception as e:
        pass

    # Courses (Exams) - Multiple URL formats for each course
    try:
        for course in Course.objects(is_active=True):
            # Get provider and code slugs
            provider_slug = ""
            code_slug = ""
            
            try:
                if course.provider:
                    provider_slug = course.provider.slug if hasattr(course.provider, 'slug') else slugify(course.provider.name)
                code_slug = slugify(course.code) if course.code else ""
            except:
                # Fallback if provider reference is broken
                provider_slug = slugify(str(course.provider)) if course.provider else ""
                code_slug = slugify(course.code) if course.code else ""

            lastmod = course.updated_at.date() if hasattr(course, 'updated_at') and course.updated_at else now().date()

            # Exam page: /exams/[provider]/[code] (primary URL format)
            if provider_slug and code_slug:
                urls.append({
                    "loc": f"{base_url}/exams/{provider_slug}/{code_slug}",
                    "lastmod": lastmod,
                    "changefreq": "weekly",
                    "priority": "0.9",
                })

                # Practice page: /exams/[provider]/[code]/practice
                urls.append({
                    "loc": f"{base_url}/exams/{provider_slug}/{code_slug}/practice",
                    "lastmod": lastmod,
                    "changefreq": "weekly",
                    "priority": "0.8",
                })

                # Pricing page: /exams/[provider]/[code]/practice/pricing
                urls.append({
                    "loc": f"{base_url}/exams/{provider_slug}/{code_slug}/practice/pricing",
                    "lastmod": lastmod,
                    "changefreq": "weekly",
                    "priority": "0.8",
                })
    except Exception as e:
        pass

    xml = render_sitemap(urls)
    return HttpResponse(xml, content_type="application/xml")


def render_sitemap(urls):
    xml = '<?xml version="1.0" encoding="UTF-8"?>'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

    for url in urls:
        xml += "<url>"
        xml += f"<loc>{url['loc']}</loc>"
        xml += f"<lastmod>{url['lastmod']}</lastmod>"
        xml += f"<changefreq>{url['changefreq']}</changefreq>"
        xml += f"<priority>{url['priority']}</priority>"
        xml += "</url>"

    xml += "</urlset>"
    return xml
