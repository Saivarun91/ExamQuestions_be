# from django.http import HttpResponse
# from django.utils.timezone import now
# from django.utils.text import slugify

# from courses.models import Course
# from categories.models import Category
# from providers.models import Provider
# from home.models import BlogPost

# def sitemap_view(request):
#     urls = []
#     base_url = "https://allexamquestions.com"

#     # Static pages (frontend routes)
#     static_urls = [
#         {"path": "", "priority": "1.0", "changefreq": "daily"},
#         {"path": "exams", "priority": "0.9", "changefreq": "daily"},
#         {"path": "blog", "priority": "0.8", "changefreq": "daily"},
#         {"path": "faq", "priority": "0.8", "changefreq": "weekly"},
#         {"path": "testimonials", "priority": "0.7", "changefreq": "weekly"},
#     ]

#     for static_url in static_urls:
#         urls.append({
#             "loc": f"{base_url}/{static_url['path']}",
#             "lastmod": now().date(),
#             "changefreq": static_url["changefreq"],
#             "priority": static_url["priority"],
#         })

#     # Blog Posts
#     try:
#         for blog_post in BlogPost.objects(is_active=True):
#             blog_slug = blog_post.slug.replace('_', '-') if blog_post.slug else ""
#             urls.append({
#                 "loc": f"{base_url}/blog/{blog_slug}",
#                 "lastmod": blog_post.updated_at.date() if blog_post.updated_at else blog_post.created_at.date() if blog_post.created_at else now().date(),
#                 "changefreq": "weekly",
#                 "priority": "0.8",
#             })
#     except Exception as e:
#         pass  # Continue if BlogPost model not available

#     # Categories
#     try:
#         for category in Category.objects.all():
#             category_slug = category.slug.replace('_', '-') if category.slug else ""
#             urls.append({
#                 "loc": f"{base_url}/categories/{category_slug}",
#                 "lastmod": now().date(),
#                 "changefreq": "weekly",
#                 "priority": "0.8",
#             })
#     except Exception as e:
#         pass

#     # Courses (Exams) - Multiple URL formats for each course
#     try:
#         for course in Course.objects(is_active=True):
#             # Get provider and code slugs
#             provider_slug = ""
#             code_slug = ""
            
#             try:
#                 if course.provider:
#                     provider_slug = course.provider.slug if hasattr(course.provider, 'slug') else slugify(course.provider.name)
#                 code_slug = slugify(course.code) if course.code else ""
#             except:
#                 # Fallback if provider reference is broken
#                 provider_slug = slugify(str(course.provider)) if course.provider else ""
#                 code_slug = slugify(course.code) if course.code else ""

#             # Replace underscores with hyphens in slugs
#             provider_slug = provider_slug.replace('_', '-') if provider_slug else ""
#             code_slug = code_slug.replace('_', '-') if code_slug else ""

#             lastmod = course.updated_at.date() if hasattr(course, 'updated_at') and course.updated_at else now().date()

#             # Exam page: /exams/[provider]/[code] (primary URL format)
#             if provider_slug and code_slug:
#                 urls.append({
#                     "loc": f"{base_url}/exams/{provider_slug}/{code_slug}",
#                     "lastmod": lastmod,
#                     "changefreq": "weekly",
#                     "priority": "0.9",
#                 })

#                 # Practice page: /exams/[provider]/[code]/practice
#                 urls.append({
#                     "loc": f"{base_url}/exams/{provider_slug}/{code_slug}/practice",
#                     "lastmod": lastmod,
#                     "changefreq": "weekly",
#                     "priority": "0.8",
#                 })

#                 # Pricing page: /exams/[provider]/[code]/practice/pricing
#                 urls.append({
#                     "loc": f"{base_url}/exams/{provider_slug}/{code_slug}/practice/pricing",
#                     "lastmod": lastmod,
#                     "changefreq": "weekly",
#                     "priority": "0.8",
#                 })
#     except Exception as e:
#         pass

#     xml = render_sitemap(urls)
#     return HttpResponse(xml, content_type="application/xml")


# def render_sitemap(urls):
#     xml = '<?xml version="1.0" encoding="UTF-8"?>'
#     xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

#     for url in urls:
#         xml += "<url>"
#         xml += f"<loc>{url['loc']}</loc>"
#         xml += f"<lastmod>{url['lastmod']}</lastmod>"
#         xml += f"<changefreq>{url['changefreq']}</changefreq>"
#         xml += f"<priority>{url['priority']}</priority>"
#         xml += "</url>"

#     xml += "</urlset>"
#     return xml



# from django.http import HttpResponse
# from django.utils.timezone import now
# from xml.sax.saxutils import escape

# from categories.models import Category
# from providers.models import Provider
# from courses.models import Course
# from home.models import BlogPost


# def sitemap_view(request):
#     base_url = "https://allexamquestions.com"
#     urls = []

#     # ---------------- STATIC PAGES ----------------
#     static_urls = [
#         ("", "1.0", "daily"),
#         ("exams", "0.95", "daily"),
#         ("categories", "0.9", "weekly"),
#         ("providers", "0.9", "weekly"),
#         ("blog", "0.85", "daily"),
#         # ("faq", "0.7", "weekly"),
#         ("testimonials", "0.7", "weekly"),
#     ]

#     for path, priority, freq in static_urls:
#         urls.append({
#             "loc": f"{base_url}/{path}" if path else base_url,
#             "lastmod": now().date(),
#             "changefreq": freq,
#             "priority": priority,
#         })

#     # ---------------- CATEGORIES ----------------
#     for category in Category.objects.all():
#         urls.append({
#             "loc": f"{base_url}/categories/{category.slug}",
#             "lastmod": getattr(category, "updated_at", now()).date(),
#             "changefreq": "weekly",
#             "priority": "0.8",
#         })

#     # ---------------- PROVIDERS ----------------
#     for provider in Provider.objects.all():
#         urls.append({
#             "loc": f"{base_url}/providers/{provider.slug}",
#             "lastmod": getattr(provider, "updated_at", now()).date(),
#             "changefreq": "weekly",
#             "priority": "0.8",
#         })

#     # ---------------- BLOGS ----------------
#     for blog in BlogPost.objects.filter(is_active=True):
#         urls.append({
#             "loc": f"{base_url}/blog/{blog.slug}",
#             "lastmod": getattr(blog, "updated_at", blog.created_at).date(),
#             "changefreq": "weekly",
#             "priority": "0.7",
#         })

#     # ---------------- EXAMS (YOUR REAL ROUTES) ----------------
#     for exam in Course.objects.filter(is_active=True):

#         exam_slug = exam.slug
#         lastmod = getattr(exam, "updated_at", now()).date()

#         if exam_slug:

#             # Main exam page
#             urls.append({
#                 "loc": f"{base_url}/{exam_slug}",
#                 "lastmod": lastmod,
#                 "changefreq": "weekly",
#                 "priority": "0.9",
#             })

#             # Official details page
#             urls.append({
#                 "loc": f"{base_url}/{exam_slug}/official-details",
#                 "lastmod": lastmod,
#                 "changefreq": "weekly",
#                 "priority": "0.85",
#             })

#     return HttpResponse(render_sitemap(urls), content_type="application/xml")


# def render_sitemap(urls):
#     xml = '<?xml version="1.0" encoding="UTF-8"?>'
#     xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'

#     for url in urls:
#         xml += "<url>"
#         xml += f"<loc>{escape(url['loc'])}</loc>"
#         xml += f"<lastmod>{url['lastmod']}</lastmod>"
#         xml += f"<changefreq>{url['changefreq']}</changefreq>"
#         xml += f"<priority>{url['priority']}</priority>"
#         xml += "</url>"

#     xml += "</urlset>"
#     return xml




import datetime

from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.timezone import now
from xml.sax.saxutils import escape

from categories.models import Category
from providers.models import Provider
from courses.models import Course
from home.models import BlogPost


def get_base_url(request):
    return f"{request.scheme}://{request.get_host()}"


def to_aware_datetime(dt):
    if dt is None:
        return None
    if isinstance(dt, datetime.date) and not isinstance(dt, datetime.datetime):
        dt = datetime.datetime.combine(dt, datetime.time.min)
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, datetime.timezone.utc)
    return dt


def format_lastmod(dt):
    if dt is None:
        dt = now()
    return to_aware_datetime(dt).isoformat(timespec="seconds")


def resolve_lastmod(obj, *fields):
    for field in fields:
        dt = getattr(obj, field, None)
        if dt:
            return format_lastmod(dt)
    return format_lastmod(now())


def max_lastmod_from_queryset(queryset, *fields):
    latest = None
    for obj in queryset:
        for field in fields:
            dt = getattr(obj, field, None)
            if dt:
                aware = to_aware_datetime(dt)
                if latest is None or aware > latest:
                    latest = aware
    return format_lastmod(latest)


# =========================================================
# MAIN SITEMAP INDEX
# =========================================================
def sitemap_index(request):

    base_url = get_base_url(request)

    categories_lastmod = max_lastmod_from_queryset(Category.objects.all(), "updated_at")
    providers_lastmod = max_lastmod_from_queryset(Provider.objects.all(), "updated_at")
    exams_lastmod = max_lastmod_from_queryset(Course.objects.filter(is_active=True), "updated_at")
    blogs_lastmod = max_lastmod_from_queryset(
        BlogPost.objects.filter(is_active=True),
        "updated_at",
        "created_at",
    )

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="https://allexamquestions.com/sitemap.xsl"?>

<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

    <sitemap>
        <loc>{base_url}/api/categories-sitemap.xml</loc>
        <lastmod>{categories_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/providers-sitemap.xml</loc>
        <lastmod>{providers_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/exams-sitemap.xml</loc>
        <lastmod>{exams_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/blogs-sitemap.xml</loc>
        <lastmod>{blogs_lastmod}</lastmod>
    </sitemap>

</sitemapindex>
'''

    return HttpResponse(xml, content_type="application/xml")


# =========================================================
# CATEGORIES SITEMAP
# =========================================================
def categories_sitemap(request):

    urls = []
    base_url = get_base_url(request)

    for category in Category.objects.all():

        urls.append({
            "loc": f"{base_url}/categories/{category.slug}",
            "lastmod": resolve_lastmod(category, "updated_at"),
            "changefreq": "weekly",
            "priority": "0.8",
        })

    return HttpResponse(render_urlset(urls), content_type="application/xml")


# =========================================================
# PROVIDERS SITEMAP
# =========================================================
def providers_sitemap(request):

    urls = []
    base_url = get_base_url(request)

    for provider in Provider.objects.all():

        urls.append({
            "loc": f"{base_url}/providers/{provider.slug}",
            "lastmod": resolve_lastmod(provider, "updated_at"),
            "changefreq": "weekly",
            "priority": "0.8",
        })

    return HttpResponse(render_urlset(urls), content_type="application/xml")


# =========================================================
# BLOGS SITEMAP
# =========================================================
def blogs_sitemap(request):

    urls = []
    base_url = get_base_url(request)

    for blog in BlogPost.objects.filter(is_active=True):

        urls.append({
            "loc": f"{base_url}/blog/{blog.slug}",
            "lastmod": resolve_lastmod(blog, "updated_at", "created_at"),
            "changefreq": "weekly",
            "priority": "0.7",
        })

    return HttpResponse(render_urlset(urls), content_type="application/xml")


# =========================================================
# EXAMS SITEMAP
# =========================================================
def exams_sitemap(request):

    urls = []
    base_url = get_base_url(request)

    for exam in Course.objects.filter(is_active=True):

        exam_slug = exam.slug
        lastmod = resolve_lastmod(exam, "updated_at")

        if exam_slug:

            # Main exam page
            urls.append({
                "loc": f"{base_url}/{exam_slug}",
                "lastmod": lastmod,
                "changefreq": "weekly",
                "priority": "0.9",
            })

            # Official details page
            urls.append({
                "loc": f"{base_url}/{exam_slug}/official-details",
                "lastmod": lastmod,
                "changefreq": "weekly",
                "priority": "0.85",
            })

    return HttpResponse(render_urlset(urls), content_type="application/xml")


# =========================================================
# COMMON XML RENDERER
# =========================================================
def render_urlset(urls):

    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="/sitemap.xsl"?>

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
'''

    for url in urls:

        xml += f'''
    <url>
        <loc>{escape(url["loc"])}</loc>
        <lastmod>{url["lastmod"]}</lastmod>
        <changefreq>{url["changefreq"]}</changefreq>
        <priority>{url["priority"]}</priority>
    </url>
'''

    xml += "</urlset>"

    return xml