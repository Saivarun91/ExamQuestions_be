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
import hashlib
import os
import re
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from django.http import HttpResponse
from django.urls import path
from django.utils import timezone
from django.utils.timezone import now
from xml.sax.saxutils import escape

from categories.models import Category
from providers.models import Provider
from courses.models import Course
from home.models import BlogPost

FRONTEND_SITE_ORIGIN = "https://allexamquestions.com"
LOCAL_HOSTNAMES = {"localhost", "127.0.0.1", "0.0.0.0", "[::1]"}
API_HOSTNAMES = {"backendapi.allexamquestions.com"}
SITEMAP_CACHE_TTL_SECONDS = 3600
# Never hold a request longer than this waiting on a cold rebuild (nginx often ~60s).
# Lean exams build is ~5s when Mongo is warm; leave headroom for cold connections.
SITEMAP_COLD_WAIT_SECONDS = 18
_sitemap_response_cache = {}
_warm_lock = threading.Lock()
_warm_thread_started = False
_rebuild_locks = {}
_rebuild_locks_guard = threading.Lock()
_startup_warm_started = False

# Prefer project-local cache so deploys/restarts keep warm files (temp dirs get wiped).
_DEFAULT_SITEMAP_CACHE_DIR = Path(__file__).resolve().parent.parent / ".sitemap_cache"
SITEMAP_DISK_CACHE_DIR = Path(
    os.environ.get(
        "SITEMAP_CACHE_DIR",
        str(_DEFAULT_SITEMAP_CACHE_DIR),
    )
)


def _disk_cache_path(cache_key):
    digest = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()
    return SITEMAP_DISK_CACHE_DIR / f"{digest}.xml"


def _get_disk_sitemap(cache_key):
    path = _disk_cache_path(cache_key)
    try:
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _set_disk_sitemap(cache_key, payload):
    try:
        SITEMAP_DISK_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = _disk_cache_path(cache_key)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(payload, encoding="utf-8")
        tmp.replace(path)
    except Exception:
        pass


def _get_cached_sitemap(cache_key):
    entry = _sitemap_response_cache.get(cache_key)
    if not entry:
        return None
    expires_at, payload = entry
    if time.monotonic() >= expires_at:
        _sitemap_response_cache.pop(cache_key, None)
        return None
    return payload


def _set_cached_sitemap(cache_key, payload):
    _sitemap_response_cache[cache_key] = (
        time.monotonic() + SITEMAP_CACHE_TTL_SECONDS,
        payload,
    )
    _set_disk_sitemap(cache_key, payload)


def _sitemap_xml_response(xml):
    response = HttpResponse(xml, content_type="application/xml")
    response["Cache-Control"] = (
        f"public, max-age={SITEMAP_CACHE_TTL_SECONDS}, stale-while-revalidate=86400"
    )
    return response


def _schedule_background_rebuild(cache_key, builder, base_url):
    """Refresh sitemap off the request path so clients never wait on rebuild."""
    with _rebuild_locks_guard:
        if _rebuild_locks.get(cache_key):
            return
        _rebuild_locks[cache_key] = True

    def _run():
        try:
            # Drop fresh memory entry so builder regenerates instead of no-op.
            _sitemap_response_cache.pop(cache_key, None)
            builder(base_url)
        except Exception:
            pass
        finally:
            with _rebuild_locks_guard:
                _rebuild_locks[cache_key] = False

    threading.Thread(
        target=_run, daemon=True, name=f"sitemap-rebuild-{cache_key}"
    ).start()


def _empty_urlset_xml():
    return render_urlset([])


def _serve_or_build_sitemap(cache_key, builder, base_url):
    """
    Fast path: memory → disk (stale-ok) → cold rebuild off-request.
    Never blocks past SITEMAP_COLD_WAIT_SECONDS (avoids nginx 504).
    """
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return _sitemap_xml_response(cached)

    disk = _get_disk_sitemap(cache_key)
    if disk:
        # Serve stale instantly; refresh cache off-request.
        _sitemap_response_cache[cache_key] = (
            time.monotonic() + SITEMAP_CACHE_TTL_SECONDS,
            disk,
        )
        _schedule_background_rebuild(cache_key, builder, base_url)
        return _sitemap_xml_response(disk)

    # Cold miss: build in background; wait briefly for completion.
    _schedule_background_rebuild(cache_key, builder, base_url)
    deadline = time.monotonic() + SITEMAP_COLD_WAIT_SECONDS
    while time.monotonic() < deadline:
        ready = _get_cached_sitemap(cache_key) or _get_disk_sitemap(cache_key)
        if ready:
            _sitemap_response_cache[cache_key] = (
                time.monotonic() + SITEMAP_CACHE_TTL_SECONDS,
                ready,
            )
            return _sitemap_xml_response(ready)
        with _rebuild_locks_guard:
            still_building = bool(_rebuild_locks.get(cache_key))
        if not still_building:
            # Rebuild finished without producing cache (error) — stop waiting.
            ready = _get_cached_sitemap(cache_key) or _get_disk_sitemap(cache_key)
            if ready:
                return _sitemap_xml_response(ready)
            break
        time.sleep(0.1)

    # Still building or failed — short-lived empty so gateways never 504.
    response = _sitemap_xml_response(_empty_urlset_xml())
    response["Cache-Control"] = "public, max-age=15, stale-while-revalidate=30"
    response["X-Sitemap-Status"] = "building"
    return response


def _schedule_sitemap_cache_warm(base_url):
    """Build section sitemaps in the background so clicks don't hit a cold DB scan."""
    global _warm_thread_started
    with _warm_lock:
        if _warm_thread_started:
            return
        exams_key = f"exams:{base_url}"
        if _get_cached_sitemap(exams_key) is not None:
            return
        disk = _get_disk_sitemap(exams_key)
        if disk:
            # Load disk into memory; still schedule a soft refresh later via TTL.
            _sitemap_response_cache[exams_key] = (
                time.monotonic() + SITEMAP_CACHE_TTL_SECONDS,
                disk,
            )
            return
        _warm_thread_started = True

    def _warm():
        global _warm_thread_started
        try:
            for cache_key, builder in (
                (f"categories:{base_url}", _build_categories_sitemap_xml),
                (f"providers:{base_url}", _build_providers_sitemap_xml),
                (f"blogs:{base_url}", _build_blogs_sitemap_xml),
                (f"exams:{base_url}", _build_exams_sitemap_xml),
            ):
                try:
                    # Share rebuild lock with request path so cold waits see progress.
                    if _get_cached_sitemap(cache_key) is None and _get_disk_sitemap(cache_key) is None:
                        _schedule_background_rebuild(cache_key, builder, base_url)
                    else:
                        builder(base_url)
                except Exception:
                    continue
            # Give background rebuilds time to finish on cold boot.
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if _get_cached_sitemap(f"exams:{base_url}") or _get_disk_sitemap(f"exams:{base_url}"):
                    break
                time.sleep(0.5)
        finally:
            time.sleep(SITEMAP_CACHE_TTL_SECONDS)
            with _warm_lock:
                _warm_thread_started = False

    threading.Thread(target=_warm, daemon=True, name="sitemap-cache-warm").start()


def warm_sitemaps_on_startup(base_url=None):
    """Kick off cache warm once when the Django process boots."""
    global _startup_warm_started
    if _startup_warm_started:
        return
    _startup_warm_started = True
    origin = (base_url or FRONTEND_SITE_ORIGIN).rstrip("/")
    _schedule_sitemap_cache_warm(origin)


def _hostname_from_host(host):
    return (host or "").split(",")[0].strip().split(":")[0].lower()


def _is_non_public_sitemap_host(hostname):
    if not hostname:
        return True
    if hostname in LOCAL_HOSTNAMES:
        return True
    if hostname.endswith(".local"):
        return True
    if hostname in API_HOSTNAMES:
        return True
    return False


def _configured_frontend_origin():
    for key in ("SITE_URL", "FRONTEND_URL", "NEXT_PUBLIC_SITE_URL"):
        raw = (os.environ.get(key) or "").strip().rstrip("/")
        if not raw:
            continue
        try:
            parsed = urlparse(raw if "://" in raw else f"https://{raw}")
            hostname = (parsed.hostname or "").lower()
            if hostname and not _is_non_public_sitemap_host(hostname):
                scheme = parsed.scheme or "https"
                netloc = parsed.netloc or hostname
                return f"{scheme}://{netloc}".rstrip("/")
        except Exception:
            continue
    return ""


def get_base_url(request):
    """Public frontend origin for sitemap <loc> URLs (never localhost/API host)."""
    configured = _configured_frontend_origin()
    if configured:
        return configured

    # Sitemap entries are always public frontend routes — never derive from
    # the API request host (localhost, internal IP, or backendapi subdomain).
    return FRONTEND_SITE_ORIGIN


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
    """Fast lastmod: order_by + only(field), never scan full documents."""
    for field in fields:
        try:
            latest_obj = (
                queryset.order_by(f"-{field}")
                .only(field)
                .no_dereference()
                .first()
            )
            dt = getattr(latest_obj, field, None) if latest_obj else None
            if dt:
                return format_lastmod(dt)
        except Exception:
            continue
    return format_lastmod(now())


# Lightweight field sets — never pull large HTML content blobs into sitemap builds.
CATEGORY_SITEMAP_FIELDS = ("slug",)
PROVIDER_SITEMAP_FIELDS = ("slug", "updated_at")
BLOG_SITEMAP_FIELDS = ("slug", "updated_at", "created_at")
EXAM_SITEMAP_FIELDS = (
    "slug",
    "updated_at",
    "official_details_url_slug",
    "show_in_official_details",
    "official_details_stat_exam_code",
    "official_details_stat_duration",
    "official_details_stat_total_questions",
    "official_details_stat_cost",
    "official_details_stat_certification_body",
    "official_details_stat_validity",
)


def _has_official_details_data_lite(exam, has_content=False):
    """Sitemap-safe official-details check without loading full HTML content."""
    if has_content:
        return True

    if getattr(exam, "show_in_official_details", False):
        return True

    stat_fields = (
        "official_details_stat_exam_code",
        "official_details_stat_duration",
        "official_details_stat_total_questions",
        "official_details_stat_cost",
        "official_details_stat_certification_body",
        "official_details_stat_validity",
    )
    if any(
        str(getattr(exam, field, None) or "").strip() for field in stat_fields
    ):
        return True

    custom_slug = _trim_public_path_segment(
        getattr(exam, "official_details_url_slug", None) or ""
    )
    return bool(custom_slug and custom_slug != "official-details")


def _exam_ids_with_official_content():
    """
    IDs whose official_details_content is non-empty, without transferring
    the full HTML over the wire (only _id).
    """
    try:
        collection = Course._get_collection()
        return {
            doc["_id"]
            for doc in collection.find(
                {
                    "is_active": True,
                    "official_details_content": {
                        "$nin": [None, "", "null", "undefined"]
                    },
                },
                {"_id": 1},
            ).batch_size(1000)
        }
    except Exception:
        return set()


def _exam_ids_with_official_faqs():
    """IDs that have at least one FAQ entry — _id only, never FAQ payloads."""
    try:
        collection = Course._get_collection()
        return {
            doc["_id"]
            for doc in collection.find(
                {
                    "is_active": True,
                    "official_details_faqs.0": {"$exists": True},
                },
                {"_id": 1},
            ).batch_size(1000)
        }
    except Exception:
        return set()


def _iter_exams_for_sitemap():
    """
    Ultra-lean MongoDB projection for exams sitemap.
    Never transfers about/content/official HTML or FAQ blobs.
    """
    collection = Course._get_collection()
    projection = {
        "slug": 1,
        "updated_at": 1,
        "official_details_url_slug": 1,
        "official_details_stat_exam_code": 1,
        "official_details_stat_duration": 1,
        "official_details_stat_total_questions": 1,
        "official_details_stat_cost": 1,
        "official_details_stat_certification_body": 1,
        "official_details_stat_validity": 1,
        "show_in_official_details": 1,
    }
    return collection.find({"is_active": True}, projection).batch_size(1000)


def _trim_public_path_segment(value=""):
    return str(value or "").strip().strip("/")


def _trim_official_details_path_segment(value=""):
    segment = _trim_public_path_segment(value)
    return segment or "official-details"


def _official_content_is_meaningful(raw_content):
    normalized = str(raw_content or "").strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    if lowered in {"null", "undefined"}:
        return False

    text_only = re.sub(r"<style[\s\S]*?</style>", " ", lowered, flags=re.I)
    text_only = re.sub(r"<script[\s\S]*?</script>", " ", text_only, flags=re.I)
    text_only = re.sub(r"<[^>]*>", " ", text_only)
    text_only = text_only.replace("&nbsp;", " ")
    text_only = re.sub(r"\s+", " ", text_only).strip()
    return len(text_only) > 0


def _has_official_details_data(exam):
    if _official_content_is_meaningful(
        getattr(exam, "official_details_content", None)
    ):
        return True

    faqs = getattr(exam, "official_details_faqs", None) or []
    if any(
        isinstance(faq, dict) and str(faq.get("question", "")).strip()
        for faq in faqs
    ):
        return True

    stat_fields = (
        "official_details_stat_exam_code",
        "official_details_stat_duration",
        "official_details_stat_total_questions",
        "official_details_stat_cost",
        "official_details_stat_certification_body",
        "official_details_stat_validity",
    )
    return any(
        str(getattr(exam, field, None) or "").strip() for field in stat_fields
    )


def _get_official_details_path(exam_slug, url_slug):
    base = _trim_public_path_segment(exam_slug)
    segment = _trim_official_details_path_segment(url_slug)
    if base:
        return f"/{base}/{segment}"
    return f"/{segment}"


def _build_official_details_url(exam):
    """
    Match frontend officialDetailsUrl:
    - custom admin slug -> /{official_details_url_slug}
    - otherwise -> /{exam_slug}/{official_details_url_slug|official-details}
    """
    exam_slug = _trim_public_path_segment(getattr(exam, "slug", None) or "")
    official_public_slug = _trim_public_path_segment(
        getattr(exam, "official_details_url_slug", None) or ""
    )
    if official_public_slug:
        return f"/{official_public_slug}"
    return _get_official_details_path(
        exam_slug,
        getattr(exam, "official_details_url_slug", None) or "official-details",
    )


# =========================================================
# MAIN SITEMAP INDEX
# =========================================================
def sitemap_index(request):
    base_url = get_base_url(request)
    _schedule_sitemap_cache_warm(base_url)

    cache_key = f"index:{base_url}"
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return _sitemap_xml_response(cached)

    # Keep index lastmod cheap — section sitemaps carry precise lastmod values.
    index_lastmod = format_lastmod(now())

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="https://allexamquestions.com/sitemap.xsl"?>

<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

    <sitemap>
        <loc>{base_url}/api/categories-sitemap.xml</loc>
        <lastmod>{index_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/providers-sitemap.xml</loc>
        <lastmod>{index_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/exams-sitemap.xml</loc>
        <lastmod>{index_lastmod}</lastmod>
    </sitemap>

    <sitemap>
        <loc>{base_url}/api/blogs-sitemap.xml</loc>
        <lastmod>{index_lastmod}</lastmod>
    </sitemap>

</sitemapindex>
'''

    _set_cached_sitemap(cache_key, xml)
    return _sitemap_xml_response(xml)


# =========================================================
# CATEGORIES SITEMAP
# =========================================================
def _build_categories_sitemap_xml(base_url):
    cache_key = f"categories:{base_url}"
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return cached

    urls = []
    lastmod = format_lastmod(now())
    collection = Category._get_collection()

    for doc in collection.find({}, {"slug": 1}):
        slug = str(doc.get("slug") or "").strip()
        if not slug:
            continue
        urls.append({
            "loc": f"{base_url}/categories/{slug}",
            "lastmod": lastmod,
            "changefreq": "weekly",
            "priority": "0.8",
        })

    xml = render_urlset(urls)
    _set_cached_sitemap(cache_key, xml)
    return xml


def categories_sitemap(request):
    base_url = get_base_url(request)
    _schedule_sitemap_cache_warm(base_url)
    return _serve_or_build_sitemap(
        f"categories:{base_url}",
        _build_categories_sitemap_xml,
        base_url,
    )


# =========================================================
# PROVIDERS SITEMAP
# =========================================================
def _build_providers_sitemap_xml(base_url):
    cache_key = f"providers:{base_url}"
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return cached

    urls = []
    collection = Provider._get_collection()

    for doc in collection.find({}, {"slug": 1, "updated_at": 1}):
        slug = str(doc.get("slug") or "").strip()
        if not slug:
            continue
        urls.append({
            "loc": f"{base_url}/providers/{slug}",
            "lastmod": format_lastmod(doc.get("updated_at")),
            "changefreq": "weekly",
            "priority": "0.8",
        })

    xml = render_urlset(urls)
    _set_cached_sitemap(cache_key, xml)
    return xml


def providers_sitemap(request):
    base_url = get_base_url(request)
    _schedule_sitemap_cache_warm(base_url)
    return _serve_or_build_sitemap(
        f"providers:{base_url}",
        _build_providers_sitemap_xml,
        base_url,
    )


# =========================================================
# BLOGS SITEMAP
# =========================================================
def _build_blogs_sitemap_xml(base_url):
    cache_key = f"blogs:{base_url}"
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return cached

    urls = []
    collection = BlogPost._get_collection()

    for doc in collection.find(
        {"is_active": True},
        {"slug": 1, "updated_at": 1, "created_at": 1},
    ):
        slug = str(doc.get("slug") or "").strip()
        if not slug:
            continue
        lastmod_dt = doc.get("updated_at") or doc.get("created_at")
        urls.append({
            "loc": f"{base_url}/blog/{slug}",
            "lastmod": format_lastmod(lastmod_dt),
            "changefreq": "weekly",
            "priority": "0.7",
        })

    xml = render_urlset(urls)
    _set_cached_sitemap(cache_key, xml)
    return xml


def blogs_sitemap(request):
    base_url = get_base_url(request)
    _schedule_sitemap_cache_warm(base_url)
    return _serve_or_build_sitemap(
        f"blogs:{base_url}",
        _build_blogs_sitemap_xml,
        base_url,
    )


# =========================================================
# EXAMS SITEMAP (official-details URLs match admin / frontend)
# =========================================================
def _build_official_details_url_from_doc(doc):
    """Same as _build_official_details_url but for raw pymongo docs."""
    exam_slug = _trim_public_path_segment(doc.get("slug") or "")
    official_public_slug = _trim_public_path_segment(
        doc.get("official_details_url_slug") or ""
    )
    if official_public_slug:
        return f"/{official_public_slug}"
    return _get_official_details_path(
        exam_slug,
        doc.get("official_details_url_slug") or "official-details",
    )


def _has_official_details_from_doc(doc, extra_official_ids=None):
    """
    Official-details detection without loading HTML/FAQ payloads.
    Uses admin flag, stats, custom slug, or precomputed content/FAQ id sets.
    """
    if extra_official_ids and doc.get("_id") in extra_official_ids:
        return True

    if doc.get("show_in_official_details"):
        return True

    if any(
        str(doc.get(field) or "").strip()
        for field in (
            "official_details_stat_exam_code",
            "official_details_stat_duration",
            "official_details_stat_total_questions",
            "official_details_stat_cost",
            "official_details_stat_certification_body",
            "official_details_stat_validity",
        )
    ):
        return True

    custom_slug = _trim_public_path_segment(
        doc.get("official_details_url_slug") or ""
    )
    return bool(custom_slug and custom_slug != "official-details")


def _build_exams_sitemap_xml(base_url):
    cache_key = f"exams:{base_url}"
    cached = _get_cached_sitemap(cache_key)
    if cached is not None:
        return cached

    urls = []
    seen_locs = set()

    def add_url(loc, lastmod, changefreq, priority):
        if loc in seen_locs:
            return
        seen_locs.add(loc)
        urls.append({
            "loc": loc,
            "lastmod": lastmod,
            "changefreq": changefreq,
            "priority": priority,
        })

    try:
        # Id-only lookups for content/FAQs (never pull large blobs).
        extra_official_ids = _exam_ids_with_official_content() | _exam_ids_with_official_faqs()
        exam_docs = list(_iter_exams_for_sitemap())
    except Exception:
        exam_docs = None
        extra_official_ids = set()

    if exam_docs is not None:
        for doc in exam_docs:
            exam_slug = _trim_public_path_segment(doc.get("slug") or "")
            if not exam_slug:
                continue

            lastmod = format_lastmod(doc.get("updated_at"))

            add_url(
                f"{base_url}/{exam_slug}",
                lastmod,
                "weekly",
                "0.9",
            )

            if _has_official_details_from_doc(doc, extra_official_ids):
                official_path = _build_official_details_url_from_doc(doc)
                add_url(
                    f"{base_url}{official_path}",
                    lastmod,
                    "weekly",
                    "0.85",
                )
    else:
        content_ids = {str(i) for i in _exam_ids_with_official_content()}
        faq_ids = {str(i) for i in _exam_ids_with_official_faqs()}
        exams = (
            Course.objects.filter(is_active=True)
            .only(*EXAM_SITEMAP_FIELDS)
            .no_dereference()
        )
        for exam in exams:
            exam_slug = _trim_public_path_segment(getattr(exam, "slug", None) or "")
            if not exam_slug:
                continue

            lastmod = resolve_lastmod(exam, "updated_at")
            add_url(
                f"{base_url}/{exam_slug}",
                lastmod,
                "weekly",
                "0.9",
            )

            exam_id = str(getattr(exam, "id", ""))
            has_extra = exam_id in content_ids or exam_id in faq_ids
            if _has_official_details_data_lite(exam, has_content=has_extra):
                official_path = _build_official_details_url(exam)
                add_url(
                    f"{base_url}{official_path}",
                    lastmod,
                    "weekly",
                    "0.85",
                )

    xml = render_urlset(urls)
    _set_cached_sitemap(cache_key, xml)
    return xml


def exams_sitemap(request):
    base_url = get_base_url(request)
    _schedule_sitemap_cache_warm(base_url)
    return _serve_or_build_sitemap(
        f"exams:{base_url}",
        _build_exams_sitemap_xml,
        base_url,
    )


# =========================================================
# COMMON XML RENDERER
# =========================================================
def render_urlset(urls):
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<?xml-stylesheet type="text/xsl" href="{FRONTEND_SITE_ORIGIN}/sitemap.xsl"?>',
        "",
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for url in urls:
        parts.append(
            f'''
    <url>
        <loc>{escape(url["loc"])}</loc>
        <lastmod>{url["lastmod"]}</lastmod>
        <changefreq>{url["changefreq"]}</changefreq>
        <priority>{url["priority"]}</priority>
    </url>'''
        )

    parts.append("</urlset>")
    return "\n".join(parts)