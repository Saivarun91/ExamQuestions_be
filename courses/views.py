

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import datetime
import re

from bson import ObjectId
from mongoengine.errors import NotUniqueError
from common.middleware import authenticate, restrict
from common.duplicate_validation import duplicate_conflict, not_unique_conflict

from .models import Course
from .serializers import CourseSerializer


def _provider_input_is_empty(provider_input):
    return provider_input is None or (
        isinstance(provider_input, str) and not provider_input.strip()
    )


def _resolve_provider(provider_input):
    """Resolve provider id/name/slug to a Provider, or None when omitted."""
    from providers.models import Provider

    if _provider_input_is_empty(provider_input):
        return None

    try:
        if ObjectId.is_valid(str(provider_input)):
            return Provider.objects.get(id=ObjectId(provider_input))
        try:
            return Provider.objects.get(name=provider_input)
        except Provider.DoesNotExist:
            return Provider.objects.get(slug=provider_input)
    except Provider.DoesNotExist:
        raise ValueError(f"Provider '{provider_input}' not found")


def _strip_html_text(value):
    text = re.sub(r"<[^>]*>", "", str(value or ""))
    return text.replace("&nbsp;", " ").strip()


def _course_field_text(course=None, extra_doc=None, data=None, field_name=""):
    if data and field_name in data:
        return _strip_html_text(data.get(field_name))
    if extra_doc and field_name in extra_doc:
        return _strip_html_text(extra_doc.get(field_name))
    if course is not None:
        return _strip_html_text(getattr(course, field_name, None))
    return ""


def _course_has_exam_details(course=None, extra_doc=None, data=None):
    """Mirror frontend courseHasExamDetails — exam page content, not official-only."""
    for field in ("about", "page_heading", "exam_details", "details", "meta_title"):
        if _course_field_text(course, extra_doc, data, field):
            return True

    topics = (data or {}).get("topics")
    if topics is None and course is not None:
        topics = getattr(course, "topics", None)
    if isinstance(topics, list):
        for topic in topics:
            if isinstance(topic, dict) and _strip_html_text(topic.get("name")):
                return True

    testimonials = (data or {}).get("testimonials")
    if testimonials is None and course is not None:
        testimonials = getattr(course, "testimonials", None)
    if isinstance(testimonials, list):
        for item in testimonials:
            if isinstance(item, dict) and _strip_html_text(item.get("name")):
                return True

    faqs = (data or {}).get("faqs")
    if faqs is None and course is not None:
        faqs = getattr(course, "faqs", None)
    if isinstance(faqs, list):
        for faq in faqs:
            if isinstance(faq, dict) and _strip_html_text(faq.get("question")):
                return True

    return False


def _has_distinct_exam_details_slug(course=None, extra_doc=None, data=None, slug=None):
    exam_slug = str(
        slug
        or (data or {}).get("slug")
        or getattr(course, "slug", None)
        or ""
    ).strip()
    official_slug = str(
        (data or {}).get("official_details_url_slug")
        or (extra_doc or {}).get("official_details_url_slug")
        or getattr(course, "official_details_url_slug", None)
        or ""
    ).strip()
    return bool(exam_slug and official_slug and exam_slug != official_slug)


def _is_official_details_only_course(
    course=None,
    extra_doc=None,
    data=None,
    slug=None,
    show_in_official_details=None,
):
    """Mirror frontend isOfficialDetailsOnlyCourse."""
    if show_in_official_details is None:
        if data and "show_in_official_details" in data:
            show_official = _parse_bool(data.get("show_in_official_details"), default=False)
        elif course is not None:
            show_official = _parse_bool(
                getattr(course, "show_in_official_details", False),
                default=False,
            )
        else:
            show_official = False
    else:
        show_official = _parse_bool(show_in_official_details, default=False)

    if not show_official:
        return False
    if _course_has_exam_details(course, extra_doc, data):
        return False
    if _has_distinct_exam_details_slug(course, extra_doc, data, slug):
        return False
    return True


def _course_duplicate_message(
    provider,
    slug=None,
    code=None,
    title=None,
    exclude_id=None,
    course=None,
    data=None,
    extra_doc=None,
    show_in_official_details=None,
):
    """Return a user-facing duplicate message if an exam/course already exists.

    Official-details-only pages and provider exam listings may share the same
    code/slug/title for one provider (separate Course records).
    """
    if provider:
        queryset = Course.objects(provider=provider)
        scope = " for this provider"
    else:
        queryset = Course.objects(provider=None)
        scope = ""
    if exclude_id and ObjectId.is_valid(str(exclude_id)):
        queryset = queryset.filter(id__ne=ObjectId(str(exclude_id)))

    incoming_official_only = _is_official_details_only_course(
        course=course,
        extra_doc=extra_doc,
        data=data,
        slug=slug or (data or {}).get("slug") or getattr(course, "slug", None),
        show_in_official_details=show_in_official_details,
    )

    def _is_same_listing_bucket(existing):
        extra_doc = _fetch_course_extra_doc(existing.id)
        existing_official_only = _is_official_details_only_course(
            existing, extra_doc=extra_doc
        )
        return existing_official_only == incoming_official_only

    if slug:
        existing = queryset.filter(slug__iexact=(slug or "").strip().lower()).first()
        if existing and _is_same_listing_bucket(existing):
            return (
                f'An exam with slug "{slug}" already exists{scope}.',
                "slug",
            )

    if code:
        existing = queryset.filter(code__iexact=(code or "").strip()).first()
        if existing and _is_same_listing_bucket(existing):
            return (
                f'An exam with code "{code}" already exists{scope}.',
                "code",
            )

    if title:
        existing = queryset.filter(title__iexact=(title or "").strip()).first()
        if existing and _is_same_listing_bucket(existing):
            return (
                f'An exam titled "{title}" already exists{scope}.',
                "title",
            )

    return None, None


def _parse_bool(value, default=False):
    """Parse booleans from JSON/form values reliably (avoids bool('false') == True)."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("true", "1", "yes", "on")
    return bool(value)


def _course_is_featured(course):
    return _parse_bool(getattr(course, "is_featured", False), default=False)


def _get_admin_featured_courses(limit=None):
    """Active courses explicitly marked featured in admin (Popular/Featured checkbox)."""
    candidates = Course.objects(is_active=True).order_by("-updated_at", "-created_at")
    featured = [c for c in candidates if _course_is_featured(c)]
    if limit is not None:
        return featured[:limit]
    return featured


# Stored in MongoDB for exam-details pages but not declared on Course — MongoEngine
# does not include these keys in save(), so they must be written via raw update.
_COURSE_EXTRA_MONGO_FIELDS = (
    "page_heading",
    "about_heading",
    "exam_details_heading",
    "exam_details",
    "details",
    "why_matters_heading",
    "whats_included_heading",
    "topics_heading",
    "practice_tests_heading",
    "testimonials_heading",
    "faqs_heading",
    "test_instructions_heading",
    "practice_page_section_1_heading",
    "practice_page_section_1_content",
    "practice_page_section_2_heading",
    "practice_page_section_2_content",
    "official_details_content",
    "official_details_meta_title",
    "official_details_meta_keywords",
    "official_details_meta_description",
    "official_details_page_title",
    "official_details_url_slug",
    "official_details_stat_exam_code",
    "official_details_stat_duration",
    "official_details_stat_total_questions",
    "official_details_stat_cost",
    "official_details_stat_certification_body",
    "official_details_stat_validity",
    "official_details_faqs",
)

_OFFICIAL_DETAILS_FIELD_KEYS = (
    "official_details_content",
    "official_details_meta_title",
    "official_details_meta_keywords",
    "official_details_meta_description",
    "official_details_page_title",
    "official_details_url_slug",
    "official_details_stat_exam_code",
    "official_details_stat_duration",
    "official_details_stat_total_questions",
    "official_details_stat_cost",
    "official_details_stat_certification_body",
    "official_details_stat_validity",
    "official_details_faqs",
)

_EXAM_DETAILS_FIELD_KEYS = (
    "short_description",
    "about",
    "eligibility",
    "exam_pattern",
    "pass_rate",
    "rating",
    "difficulty",
    "duration",
    "passing_score",
    "whats_included",
    "why_matters",
    "topics",
    "testimonials",
    "faqs",
    "test_instructions",
    "test_description",
    "hero_title",
    "hero_subtitle",
    "pricing_plans",
    "pricing_features",
    "pricing_testimonials",
    "pricing_faqs",
    "pricing_comparison",
    "meta_title",
    "meta_keywords",
    "meta_description",
    "page_heading",
    "about_heading",
    "exam_details_heading",
    "exam_details",
    "details",
    "why_matters_heading",
    "whats_included_heading",
    "topics_heading",
    "practice_tests_heading",
    "testimonials_heading",
    "faqs_heading",
    "test_instructions_heading",
    "practice_page_section_1_heading",
    "practice_page_section_1_content",
    "practice_page_section_2_heading",
    "practice_page_section_2_content",
)


def _course_extra_projection():
    return ["_id"] + list(_COURSE_EXTRA_MONGO_FIELDS)


def _merge_course_extra_from_doc(serialized, mongo_doc):
    """Overlay exam-details-related keys from the raw course document onto API output."""
    if not mongo_doc:
        return serialized
    out = dict(serialized)
    for k in _COURSE_EXTRA_MONGO_FIELDS:
        if k in mongo_doc:
            out[k] = mongo_doc[k]
    return out


def _fetch_course_extra_doc(course_oid):
    return Course._get_collection().find_one(
        {"_id": course_oid},
        projection=_course_extra_projection(),
    )


def _persist_course_extra_fields(course_oid, data):
    extra_set = {k: data[k] for k in _COURSE_EXTRA_MONGO_FIELDS if k in data}
    if not extra_set:
        return
    Course._get_collection().update_one({"_id": course_oid}, {"$set": extra_set})


def _official_content_is_meaningful(raw_content):
    normalized = str(raw_content or "").strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if lowered in ("null", "undefined"):
        return False
    text_only = re.sub(r"<style[\s\S]*?</style>", " ", lowered, flags=re.I)
    text_only = re.sub(r"<script[\s\S]*?</script>", " ", text_only, flags=re.I)
    text_only = re.sub(r"<[^>]*>", " ", text_only)
    text_only = text_only.replace("&nbsp;", " ")
    text_only = re.sub(r"\s+", " ", text_only).strip()
    return len(text_only) > 0


def _has_official_details_data(course, extra_doc=None):
    """Mirror frontend hasOfficialDetailsData."""
    content = ""
    if extra_doc and "official_details_content" in extra_doc:
        content = extra_doc.get("official_details_content") or ""
    elif course is not None:
        content = getattr(course, "official_details_content", "") or ""

    faqs = []
    if extra_doc and extra_doc.get("official_details_faqs"):
        faqs = extra_doc.get("official_details_faqs") or []
    elif course is not None:
        faqs = getattr(course, "official_details_faqs", None) or []
    if not isinstance(faqs, list):
        faqs = []
    faqs = [
        f for f in faqs
        if isinstance(f, dict) and str(f.get("question") or "").strip()
    ]

    stat_fields = (
        "official_details_stat_exam_code",
        "official_details_stat_duration",
        "official_details_stat_total_questions",
        "official_details_stat_cost",
        "official_details_stat_certification_body",
        "official_details_stat_validity",
    )
    has_stat = False
    for field in stat_fields:
        val = ""
        if extra_doc and field in extra_doc:
            val = extra_doc.get(field)
        elif course is not None:
            val = getattr(course, field, None)
        if str(val or "").strip():
            has_stat = True
            break

    return _official_content_is_meaningful(content) or len(faqs) > 0 or has_stat


def _find_official_details_sibling(course):
    """Find another course (same provider + code) that holds official details."""
    if not course or not course.code:
        return None, None

    code = str(course.code).strip()
    if not code:
        return None, None

    query = Course.objects(
        code__iexact=code,
        id__ne=course.id,
        is_active=True,
    )
    if course.provider:
        query = query.filter(provider=course.provider)

    for sibling in query:
        sibling_raw = _fetch_course_extra_doc(sibling.id)
        if _has_official_details_data(sibling, sibling_raw):
            return sibling, sibling_raw
    return None, None


def _merge_linked_official_details_response(serialized, raw, course):
    """Attach official-details fields from a sibling course when this record has none."""
    if _has_official_details_data(course, raw):
        return serialized, raw

    sibling, sibling_raw = _find_official_details_sibling(course)
    if not sibling:
        return serialized, raw

    out = dict(serialized)
    merged_raw = dict(raw or {})

    for field in _OFFICIAL_DETAILS_FIELD_KEYS:
        val = None
        if sibling_raw and field in sibling_raw:
            val = sibling_raw[field]
        elif hasattr(sibling, field):
            val = getattr(sibling, field, None)
        if val is None:
            continue
        if field in _COURSE_EXTRA_MONGO_FIELDS:
            merged_raw[field] = val
        out[field] = val

    sibling_slug = str(getattr(sibling, "slug", "") or "").strip()
    url_slug = str(
        merged_raw.get("official_details_url_slug")
        or getattr(sibling, "official_details_url_slug", None)
        or ""
    ).strip()
    if (not url_slug or url_slug.lower() == "official-details") and sibling_slug:
        merged_raw["official_details_url_slug"] = sibling_slug
        out["official_details_url_slug"] = sibling_slug

    if _parse_bool(getattr(sibling, "show_in_official_details", False), default=False):
        out["show_in_official_details"] = True

    return out, merged_raw


def _bulk_fetch_course_extra_docs(courses):
    ids = [c.id for c in courses]
    if not ids:
        return {}
    by_id = {}
    for doc in Course._get_collection().find(
        {"_id": {"$in": ids}},
        projection=_course_extra_projection(),
    ):
        by_id[str(doc["_id"])] = doc
    return by_id


# ------------------------------------------------------------
# ✅ PUBLIC: Get all active courses
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def course_list(request):
    """Get all active courses for public display"""
    try:
        from practice_tests.models import PracticeTest
        
        courses = Course.objects(is_active=True).order_by('-created_at')
        
        # ✅ AUTO-SYNC: Ensure practice_exams and questions counts are accurate for each course
        from questions.models import Question
        for course in courses:
            practice_test_count = PracticeTest.objects(course=course).count()
            question_count = Question.objects(course=course).count()
            if course.practice_exams != practice_test_count or course.questions != question_count:
                course.practice_exams = practice_test_count
                course.questions = question_count
                course.save()
        
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Get all courses
# ------------------------------------------------------------
@api_view(['GET'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_course_list(request):
    try:
        courses = Course.objects.all().order_by('-created_at')

        serializer = CourseSerializer(courses, many=True)
        extras = _bulk_fetch_course_extra_docs(courses)
        merged = [
            _merge_course_extra_from_doc(item, extras.get(item.get("id")))
            for item in serializer.data
        ]
        return Response({"success": True, "data": merged})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Get one course by ID (full serializer — exam manager, etc.)
# ------------------------------------------------------------
@api_view(["GET"])
@authenticate
@restrict(["admin"])
@csrf_exempt
def admin_course_detail(request, course_id):
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))
        serializer = CourseSerializer(course)
        raw = _fetch_course_extra_doc(course.id)
        return Response(
            {"success": True, "data": _merge_course_extra_from_doc(serializer.data, raw)}
        )
    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ ADMIN: Create Course
# ------------------------------------------------------------
@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_create(request):
    """Admin: Create new course"""
    try:
        from categories.models import Category

        data = request.data

        # Required fields
        required_fields = ['title', 'code', 'slug']
        for field in required_fields:
            if field not in data:
                return Response({"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Provider (optional — id, name, or slug)
        try:
            provider = _resolve_provider(data.get('provider'))
        except ValueError as exc:
            return Response({"error": str(exc)}, status=400)

        # Category (optional)
        category = None
        if data.get('category'):
            category_input = data['category']
            try:
                if ObjectId.is_valid(category_input):
                    category = Category.objects.get(id=ObjectId(category_input))
                else:
                    try:
                        category = Category.objects.get(title=category_input)
                    except Category.DoesNotExist:
                        category = Category.objects.get(slug=category_input)
            except Category.DoesNotExist:
                return Response({"error": f"Category '{category_input}' not found"}, status=400)

        # "is_featured" controls "Popular/Featured exams" shown on Home + sidebar.
        # Do NOT auto-enable it based on category; it must be explicitly chosen in admin.
        is_featured = _parse_bool(data.get("is_featured"), default=False)

        # ✅ AUTO-CALCULATE: Get actual counts from related documents
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        # Store slug exactly as entered in admin (trim whitespace only)
        slug = str(data['slug']).strip()
        code = str(data.get('code') or '').strip() or slug
        title = str(data['title']).strip()

        duplicate_message, duplicate_field = _course_duplicate_message(
            provider,
            slug=slug,
            code=code,
            title=title,
            data=data,
            show_in_official_details=_parse_bool(
                data.get("show_in_official_details"),
                default=False,
            ),
        )
        if duplicate_message:
            return duplicate_conflict(duplicate_message, field=duplicate_field)

        # Create course first (with 0 counts, will be updated)
        course = Course(
            provider=provider,
            title=title,
            code=code,
            slug=slug,  # Use normalized slug
            exam_name=data.get('exam_name') or None,
            practice_exams=0,  # Will be auto-calculated
            questions=0,  # Will be auto-calculated
            badge=data.get('badge'),
            category=category,
            actual_price=float(data.get('actual_price', 0)),
            offer_price=float(data.get('offer_price', 0)),
            currency=data.get('currency', 'INR'),
            is_featured=is_featured,
            show_in_official_details=_parse_bool(
                data.get('show_in_official_details'),
                default=False
            ),
            meta_title=data.get('meta_title'),
            meta_keywords=data.get('meta_keywords'),
            meta_description=data.get('meta_description'),
        )

        try:
            course.save()
        except NotUniqueError as exc:
            return not_unique_conflict(exc, field="slug")

        # ✅ AUTO-SYNC: Calculate and update counts from related documents
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        course.practice_exams = practice_test_count
        course.questions = question_count
        course.save()

        serializer = CourseSerializer(course)
        return Response({"success": True, "message": "Course created successfully", "data": serializer.data}, status=201)

    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="slug")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict("This exam already exists for this provider.", field="slug")
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get course by ID or slug
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def course_detail(request, course_identifier):
    """Get course by ID or slug - SEO-friendly URL support"""
    try:
        from urllib.parse import unquote
        from providers.models import Provider

        course_identifier = unquote(course_identifier).strip()

        course = None
        if ObjectId.is_valid(course_identifier):
            course = Course.objects.get(id=ObjectId(course_identifier))
        else:
            try:
                course = Course.objects.get(slug=course_identifier)
            except Course.DoesNotExist:
                try:
                    course = Course.objects.get(slug__iexact=course_identifier)
                except Course.DoesNotExist:
                    try:
                        # Official details public URL can be independent from exam slug.
                        course = Course.objects.get(
                            official_details_url_slug=course_identifier
                        )
                    except Course.DoesNotExist:
                        try:
                            course = Course.objects.get(
                                official_details_url_slug__iexact=course_identifier
                            )
                        except Course.DoesNotExist:
                            course = None

        if course is None:
            # Legacy SEO lookup (normalized lowercase slug + provider/code probing)
            course_identifier = course_identifier.lower().replace('_', '-')

            try:
                course = Course.objects.get(slug=course_identifier)
            except Course.DoesNotExist:
                try:
                    course = Course.objects.get(slug__iexact=course_identifier)
                except Course.DoesNotExist:
                    normalized_identifier = course_identifier.replace('_', '-')

                    if '-' in normalized_identifier:
                        all_parts = normalized_identifier.split('-')
                        provider = None
                        provider_slug = None
                        code_part = None
                        
                        # Strategy 1: Try two-word provider first (e.g., "sap-se")
                        if len(all_parts) >= 3:
                            provider_slug_alt = f"{all_parts[0]}-{all_parts[1]}"
                            code_part_alt = '-'.join(all_parts[2:])
                            
                            # Try to find provider with two-word slug
                            provider_variants_alt = [
                                provider_slug_alt,
                                provider_slug_alt.upper(),
                                provider_slug_alt.capitalize(),
                                provider_slug_alt.replace('-', ' '),
                                provider_slug_alt.replace('-', ' ').title(),
                            ]
                            
                            for variant in provider_variants_alt:
                                try:
                                    provider = Provider.objects.get(slug=variant)
                                    provider_slug = provider_slug_alt
                                    code_part = code_part_alt
                                    break
                                except Provider.DoesNotExist:
                                    try:
                                        provider = Provider.objects.get(name__iexact=variant)
                                        provider_slug = provider_slug_alt
                                        code_part = code_part_alt
                                        break
                                    except Provider.DoesNotExist:
                                        continue
                        
                        # Strategy 2: Try single-word provider (e.g., "sap")
                        if not provider and len(all_parts) >= 2:
                            provider_slug = all_parts[0]
                            code_part = '-'.join(all_parts[1:])
                            
                            provider_variants = [
                                provider_slug,
                                provider_slug.upper(),
                                provider_slug.capitalize(),
                                provider_slug.replace('-', ' '),
                                provider_slug.replace('-', ' ').title(),
                            ]
                            
                            for variant in provider_variants:
                                try:
                                    provider = Provider.objects.get(slug=variant)
                                    break
                                except Provider.DoesNotExist:
                                    try:
                                        provider = Provider.objects.get(name__iexact=variant)
                                        break
                                    except Provider.DoesNotExist:
                                        continue
                            
                            # If still not found, try partial match
                            if not provider:
                                try:
                                    providers = Provider.objects.filter(slug__icontains=provider_slug)
                                    if providers.count() == 1:
                                        provider = providers.first()
                                except Exception:
                                    pass
                        
                        # Now try to find course with the found provider
                        if provider and code_part:
                            # Try multiple code format variations
                            # The code might be stored as: SE-C_BW4H_2505, SE-C-BW4H-2505, SE-C-BW4H_2505, etc.
                            code_variants = [
                                code_part.upper(),  # se-c-bw4h-2505 -> SE-C-BW4H-2505
                                code_part.upper().replace('-', '_'),  # SE-C_BW4H_2505
                                code_part.upper().replace('_', '-'),  # SE-C-BW4H-2505
                                code_part,  # se-c-bw4h-2505
                                code_part.replace('-', '_').upper(),  # SE_C_BW4H_2505
                            ]
                            
                            # If code_part has no separators, try adding them in common patterns
                            # Example: cs4cs2508 -> C-S4CS-2508, C_S4CS_2508
                            if '-' not in code_part and '_' not in code_part:
                                code_upper = code_part.upper()
                                
                                # Pattern 1: Single letter prefix (e.g., C in CS4CS2508)
                                # Match: single letter, then letters/numbers, then numbers at end
                                if re.match(r'^[A-Z][A-Z0-9]*[0-9]+$', code_upper):
                                    match = re.match(r'^([A-Z])(.+?)([0-9]+)$', code_upper)
                                    if match:
                                        first_letter, middle, numbers = match.groups()
                                        # Try with hyphens
                                        code_variants.append(f"{first_letter}-{middle}-{numbers}")
                                        # Try with underscores
                                        code_variants.append(f"{first_letter}_{middle}_{numbers}")
                                        # Try splitting middle part if it has numbers
                                        if re.search(r'\d', middle):
                                            middle_split = re.sub(r'([A-Z])([0-9])', r'\1-\2', middle)
                                            code_variants.append(f"{first_letter}-{middle_split}-{numbers}")
                                            middle_split_underscore = re.sub(r'([A-Z])([0-9])', r'\1_\2', middle)
                                            code_variants.append(f"{first_letter}_{middle_split_underscore}_{numbers}")
                                
                                # Pattern 2: Add hyphens before any number (general case)
                                code_with_hyphens = re.sub(r'([A-Z])([0-9])', r'\1-\2', code_upper)
                                if code_with_hyphens != code_upper:
                                    code_variants.append(code_with_hyphens)
                                    code_variants.append(code_with_hyphens.replace('-', '_'))
                                
                                # Pattern 3: Add hyphens after any number
                                code_after_numbers = re.sub(r'([0-9])([A-Z])', r'\1-\2', code_upper)
                                if code_after_numbers != code_upper:
                                    code_variants.append(code_after_numbers)
                                    code_variants.append(code_after_numbers.replace('-', '_'))
                                
                                # Pattern 4: Try common SAP patterns (e.g., C_S4CS_2508)
                                # If it starts with C and has S4CS pattern
                                if code_upper.startswith('C') and 'S' in code_upper:
                                    # Try: C-S4CS-2508, C_S4CS_2508
                                    sap_match = re.match(r'^(C)(S?[0-9]*[A-Z]*)([0-9]+)$', code_upper)
                                    if sap_match:
                                        c_part, middle_part, num_part = sap_match.groups()
                                        code_variants.append(f"{c_part}-{middle_part}-{num_part}")
                                        code_variants.append(f"{c_part}_{middle_part}_{num_part}")
                            
                            # Remove duplicates while preserving order
                            seen = set()
                            unique_code_variants = []
                            for variant in code_variants:
                                if variant and variant not in seen:
                                    seen.add(variant)
                                    unique_code_variants.append(variant)
                            code_variants = unique_code_variants
                            
                            # Try to find course by provider and code (try all variants)
                            for code_variant in code_variants:
                                try:
                                    course = Course.objects.get(provider=provider, code__iexact=code_variant)
                                    break
                                except Course.DoesNotExist:
                                    continue
                            
                            # If not found by code, try by slug variations
                            if not course:
                                slug_variants = [
                                    f"{provider_slug}-{code_part.lower()}",  # sap-se-c-bw4h-2505
                                    f"{provider_slug}-{code_part.lower().replace('_', '-')}",  # normalize underscores
                                    course_identifier,  # original identifier
                                    normalized_identifier,  # normalized identifier
                                ]
                                
                                # If code_part has no separators, generate slug variants with separators
                                if '-' not in code_part and '_' not in code_part:
                                    code_lower = code_part.lower()
                                    
                                    # Generate slug variants similar to code variants
                                    # Pattern: single letter prefix
                                    if re.match(r'^[a-z][a-z0-9]*[0-9]+$', code_lower):
                                        match = re.match(r'^([a-z])(.+?)([0-9]+)$', code_lower)
                                        if match:
                                            first_letter, middle, numbers = match.groups()
                                            slug_variants.append(f"{provider_slug}-{first_letter}-{middle}-{numbers}")
                                            # Try splitting middle if it has numbers
                                            if re.search(r'\d', middle):
                                                middle_split = re.sub(r'([a-z])([0-9])', r'\1-\2', middle)
                                                slug_variants.append(f"{provider_slug}-{first_letter}-{middle_split}-{numbers}")
                                    
                                    # Add hyphens before numbers
                                    code_with_hyphens = re.sub(r'([a-z])([0-9])', r'\1-\2', code_lower)
                                    if code_with_hyphens != code_lower:
                                        slug_variants.append(f"{provider_slug}-{code_with_hyphens}")
                                
                                # Remove duplicates
                                seen_slugs = set()
                                unique_slug_variants = []
                                for variant in slug_variants:
                                    if variant and variant not in seen_slugs:
                                        seen_slugs.add(variant)
                                        unique_slug_variants.append(variant)
                                slug_variants = unique_slug_variants
                                
                                for slug_variant in slug_variants:
                                    try:
                                        course = Course.objects.get(provider=provider, slug=slug_variant)
                                        break
                                    except Course.DoesNotExist:
                                        try:
                                            course = Course.objects.get(provider=provider, slug__iexact=slug_variant)
                                            break
                                        except Course.DoesNotExist:
                                            continue
                            
                            # Last resort: try to find any course with this provider and matching slug pattern
                            if not course:
                                try:
                                    # Try partial slug match
                                    courses = Course.objects.filter(provider=provider, slug__icontains=code_part.lower())
                                    if courses.count() == 1:
                                        course = courses.first()
                                except Exception:
                                    pass
                    
                    # Final fallback: Try to find by slug pattern (case-insensitive, partial match)
                    if not course:
                        try:
                            # Try exact slug match (case-insensitive)
                            course = Course.objects.get(slug__iexact=course_identifier)
                        except Course.DoesNotExist:
                            try:
                                # Try normalized slug match
                                course = Course.objects.get(slug__iexact=normalized_identifier)
                            except Course.DoesNotExist:
                                try:
                                    # Try slug containing the identifier
                                    courses = Course.objects.filter(slug__icontains=course_identifier.lower())
                                    if courses.count() == 1:
                                        course = courses.first()
                                except Exception:
                                    pass
                    
                    # Ultimate fallback: Search all courses by code pattern
                    if not course and '-' in normalized_identifier:
                        # Extract potential code from the identifier
                        # For "sap-se-c-bw4h-2505", try to find course with code containing "se-c" or "bw4h"
                        code_parts = normalized_identifier.split('-')
                        if len(code_parts) >= 2:
                            # Try to find by code pattern (e.g., "SE-C" or "BW4H")
                            # Build code variations: "se-c-bw4h-2505" -> ["SE-C-BW4H-2505", "SE-C", "BW4H", "2505"]
                            code_variations = []
                            
                            # Full code (uppercase)
                            full_code = '-'.join(code_parts[1:]).upper()
                            code_variations.append(full_code)
                            
                            # Code with underscores
                            code_variations.append(full_code.replace('-', '_'))
                            
                            # Individual meaningful parts
                            for part in code_parts[1:]:
                                if len(part) >= 2 and part.isalnum():
                                    code_variations.append(part.upper())
                            
                            # Try each variation
                            for code_var in code_variations:
                                try:
                                    courses = Course.objects.filter(code__icontains=code_var)
                                    if courses.count() == 1:
                                        course = courses.first()
                                        break
                                    elif courses.count() > 1:
                                        # If multiple matches, try to find one with matching slug pattern
                                        for c in courses:
                                            c_slug_lower = c.slug.lower()
                                            identifier_lower = normalized_identifier.lower()
                                            if identifier_lower in c_slug_lower or c_slug_lower in identifier_lower:
                                                course = c
                                                break
                                        if course:
                                            break
                                except Exception:
                                    continue
                            
                            # Last resort: search by slug containing any part of the code
                            if not course:
                                for code_var in code_variations[:3]:  # Try first 3 variations
                                    try:
                                        courses = Course.objects.filter(slug__icontains=code_var.lower())
                                        if courses.count() == 1:
                                            course = courses.first()
                                            break
                                    except Exception:
                                        continue
                    
                    # Legacy public URLs: old slug is often a prefix of the current canonical slug.
                    if not course:
                        try:
                            identifier_lower = normalized_identifier.lower()
                            prefix_matches = list(
                                Course.objects.filter(
                                    slug__istartswith=identifier_lower,
                                    is_active=True,
                                )
                            )
                            if len(prefix_matches) == 1:
                                course = prefix_matches[0]
                            elif len(prefix_matches) > 1:
                                continued = [
                                    c
                                    for c in prefix_matches
                                    if c.slug.lower() == identifier_lower
                                    or c.slug.lower().startswith(
                                        identifier_lower + "-"
                                    )
                                ]
                                if len(continued) == 1:
                                    course = continued[0]
                        except Exception:
                            pass

                    # If still not found, raise DoesNotExist
                    if not course:
                        # Log for debugging
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"Course not found for identifier: {course_identifier}")
                        raise Course.DoesNotExist()

        # Ensure course was found
        if not course:
                    raise Course.DoesNotExist()

        # ✅ AUTO-SYNC: Ensure counts are accurate
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        if course.practice_exams != practice_test_count or course.questions != question_count:
            course.practice_exams = practice_test_count
            course.questions = question_count
            course.save()

        serializer = CourseSerializer(course)
        raw = _fetch_course_extra_doc(course.id)
        merged_data, merged_raw = _merge_linked_official_details_response(
            serializer.data, raw, course
        )
        return Response(_merge_course_extra_from_doc(merged_data, merged_raw))

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ ADMIN: Update Course
# ------------------------------------------------------------
@api_view(['PUT'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_update(request, course_id):
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))
        data = request.data

        # Update category if provided
        if 'category' in data:
            from categories.models import Category
            category_input = data['category']
            try:
                if ObjectId.is_valid(category_input):
                    category = Category.objects.get(id=ObjectId(category_input))
                else:
                    try:
                        category = Category.objects.get(title=category_input)
                    except Category.DoesNotExist:
                        category = Category.objects.get(slug=category_input)
                course.category = category
            except Category.DoesNotExist:
                return Response({"error": f"Category '{category_input}' not found"}, status=400)

        # Update provider if provided (optional — omit or send null/empty to clear)
        if "provider" in data:
            try:
                course.provider = _resolve_provider(data["provider"])
            except ValueError as exc:
                return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Update fields
        if 'title' in data:
            course.title = data['title']
        if 'code' in data:
            new_code = str(data.get('code') or '').strip()
            if new_code:
                course.code = new_code
            elif not getattr(course, 'code', None):
                course.code = str(course.slug or '').strip() or 'exam'
        if 'slug' in data:
            course.slug = str(data['slug']).strip()
        if 'exam_name' in data:
            course.exam_name = data.get('exam_name') or None
        if "show_in_official_details" in data:
            course.show_in_official_details = _parse_bool(
                data.get("show_in_official_details"),
                default=course.show_in_official_details
            )
        if 'questions' in data:
            course.questions = int(data['questions'])
        if 'practice_exams' in data:
            course.practice_exams = int(data['practice_exams'])
        if 'badge' in data:
            course.badge = data['badge']
        
        # Update pricing fields
        if 'actual_price' in data:
            course.actual_price = float(data['actual_price']) if data['actual_price'] else 0.0
        if 'offer_price' in data:
            course.offer_price = float(data['offer_price']) if data['offer_price'] else 0.0
        if 'currency' in data:
            course.currency = data['currency']
        if "is_featured" in data:
            course.is_featured = _parse_bool(data["is_featured"], default=False)
        if "show_in_official_details" in data:
            course.show_in_official_details = str(
                data["show_in_official_details"]
            ).lower() in ["true", "1", "yes", "on"]
        if 'is_active' in data:
            course.is_active = bool(data['is_active'])
        

        # Update metadata (only when explicitly sent — partial updates must not clear)
        if 'meta_title' in data:
            course.meta_title = data.get('meta_title')
        if 'meta_keywords' in data:
            course.meta_keywords = data.get('meta_keywords')
        if 'meta_description' in data:
            course.meta_description = data.get('meta_description')

        # Update extra details
        for field in [
            "page_heading",
            "about",
            "about_heading",
            "exam_details_heading",
            "exam_details",
            "details",
            "why_matters_heading",
            "whats_included_heading",
            "topics_heading",
            "practice_tests_heading",
            "testimonials_heading",
            "faqs_heading",
            "test_instructions_heading",
            "eligibility",
            "exam_pattern",
            "difficulty",
            "duration",
            "passing_score",
            "why_matters",
            "pass_rate",
            "rating",
        ]:
            if field in data:
                # Handle pass_rate and rating - allow null values
                if field in ["pass_rate", "rating"]:
                    if data[field] is not None and data[field] != "":
                        if field == "pass_rate":
                            setattr(course, field, int(data[field]))
                        else:  # rating
                            setattr(course, field, float(data[field]))
                    else:
                        setattr(course, field, None)
                else:
                    setattr(course, field, data[field])

        # List fields (excluding practice_tests_list - handled separately)
        for field in ["whats_included", "topics", "testimonials", "faqs", "test_instructions"]:
            if field in data and isinstance(data[field], list):
                setattr(course, field, data[field])

        # ✅ AUTO-SYNC: Sync practice_tests_list to PracticeTest collection and update references
        if 'practice_tests_list' in data and isinstance(data['practice_tests_list'], list):
            from practice_tests.models import PracticeTest
            from django.utils.text import slugify
            import datetime
            from pymongo.errors import DuplicateKeyError
            
            synced_tests = []
            for test_data in data['practice_tests_list']:
                if not test_data.get('name'):
                    continue  # Skip tests without a name
                
                try:
                    # Generate slug from test name
                    test_name = test_data.get('name', '')
                    base_slug = slugify(test_name)
                    
                    # Try to find existing test by ID first (if provided), then by name AND course
                    existing_test = None
                    test_id = test_data.get('id')
                    
                    # If ID is provided and looks like a MongoDB ObjectId, try to find by ID
                    if test_id and ObjectId.is_valid(str(test_id)):
                        try:
                            existing_test = PracticeTest.objects(id=ObjectId(test_id), course=course).first()
                        except:
                            pass  # If lookup fails, continue to name-based lookup
                    
                    # If not found by ID, try by name AND course (ensures course-specific lookup)
                    if not existing_test:
                        existing_test = PracticeTest.objects(title=test_name, course=course).first()
                    
                    if existing_test:
                        # Update existing test for this course
                        practice_test = existing_test
                        print(f"   📝 Updating existing test '{test_name}' for course '{course.title}'")
                    else:
                        # Create new test with unique slug for this course
                        # First try with simple slug (relying on composite index for uniqueness per course)
                        slug = base_slug
                        counter = 1
                        max_checks = 100
                        
                        # Ensure slug is unique for this specific course
                        while counter <= max_checks:
                            existing_by_slug = PracticeTest.objects(slug=slug, course=course).first()
                            if not existing_by_slug:
                                # Also check if slug exists globally (in case of single-field index)
                                # If it exists in another course, we can still use it (composite index allows this)
                                # But if there's a single-field index issue, we'll handle it in the save retry
                                break
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        if counter > max_checks:
                            # Use counter for uniqueness if needed
                            slug = f"{base_slug}-{counter}"
                        
                        practice_test = PracticeTest(
                            slug=slug,
                            title=test_name,
                            course=course,
                            category=course.category if hasattr(course, 'category') and course.category else None
                        )
                        print(f"   ✨ Creating new test '{test_name}' for course '{course.title}' (slug: {slug})")
                    
                    # Update test fields (including title to ensure it matches the sent data)
                    # Always update title with the value from the request
                    if test_name:
                        practice_test.title = test_name
                    
                    # Parse duration string (e.g., "90 minutes" -> 90)
                    duration_str = str(test_data.get('duration', '0'))
                    duration_int = 0
                    if duration_str:
                        # Extract numbers from duration string
                        import re
                        numbers = re.findall(r'\d+', duration_str)
                        if numbers:
                            duration_int = int(numbers[0])
                    
                    practice_test.questions = int(test_data.get('questions', 0))
                    practice_test.duration = duration_int
                    practice_test.difficulty_level = test_data.get('difficulty', 'Intermediate')
                    practice_test.overview = test_data.get('description', '')
                    
                    # Save the practice test with retry logic for duplicate key errors
                    practice_test.updated_at = datetime.datetime.utcnow()
                    
                    # Retry logic to handle any duplicate key errors (e.g., if single-field index exists on slug)
                    max_retries = 3
                    retry_count = 0
                    saved = False
                    
                    while retry_count < max_retries and not saved:
                        try:
                            practice_test.save()
                            saved = True
                        except DuplicateKeyError as dke:
                            retry_count += 1
                            if retry_count < max_retries:
                                # Generate a new unique slug using counter
                                practice_test.slug = f"{base_slug}-{retry_count}"
                                print(f"   🔄 Retry {retry_count}: Generated slug due to duplicate key: {practice_test.slug}")
                            else:
                                # Last resort: use counter for uniqueness
                                practice_test.slug = f"{base_slug}-{retry_count}"
                                print(f"   🔄 Final retry: Using counter for slug: {practice_test.slug}")
                                try:
                                    practice_test.save()
                                    saved = True
                                except:
                                    raise  # Re-raise if still fails
                        except Exception as save_error:
                            # Check if it's a duplicate key error (might be wrapped)
                            if "duplicate key" in str(save_error).lower() or "E11000" in str(save_error):
                                retry_count += 1
                                if retry_count < max_retries:
                                    # Generate a new unique slug using counter
                                    practice_test.slug = f"{base_slug}-{retry_count}"
                                    print(f"   🔄 Retry {retry_count}: Generated slug: {practice_test.slug}")
                                    continue
                            # For other errors, re-raise immediately
                            raise
                    
                    synced_tests.append({
                        'name': practice_test.title,
                        'slug': practice_test.slug,
                        'id': str(practice_test.id)
                    })
                    
                except Exception as e:
                    print(f"   ⚠️  Error syncing test '{test_data.get('name')}': {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Continue with other tests even if one fails
                    continue
            
            # ✅ Update practice_tests reference field in course document
            if synced_tests:
                # Get all synced PracticeTest objects
                synced_practice_test_ids = [st['id'] for st in synced_tests]
                synced_practice_tests = []
                for pt_id in synced_practice_test_ids:
                    try:
                        pt = PracticeTest.objects.get(id=ObjectId(pt_id))
                        synced_practice_tests.append(pt)
                    except PracticeTest.DoesNotExist:
                        continue
                
                # Update course's practice_tests reference field
                course.practice_tests = synced_practice_tests

        # ✅ AUTO-SYNC: Calculate and update counts from related documents
        from practice_tests.models import PracticeTest
        from questions.models import Question
        
        practice_test_count = PracticeTest.objects(course=course).count()
        question_count = Question.objects(course=course).count()
        course.practice_exams = practice_test_count
        course.questions = question_count
        
        import datetime
        course.updated_at = datetime.datetime.utcnow()

        extra_doc = _fetch_course_extra_doc(course.id)
        duplicate_message, duplicate_field = _course_duplicate_message(
            course.provider,
            slug=course.slug,
            code=course.code,
            title=course.title,
            exclude_id=course_id,
            course=course,
            data=data,
            extra_doc=extra_doc,
        )
        if duplicate_message:
            return duplicate_conflict(duplicate_message, field=duplicate_field)

        try:
            course.save()
        except NotUniqueError as exc:
            return not_unique_conflict(exc, field="slug")

        if _parse_bool(data.get("clear_official_details"), default=False):
            Course._get_collection().update_one(
                {"_id": course.id},
                {"$unset": {k: "" for k in _OFFICIAL_DETAILS_FIELD_KEYS}},
            )

        if _parse_bool(data.get("clear_exam_details"), default=False):
            Course._get_collection().update_one(
                {"_id": course.id},
                {"$unset": {k: "" for k in _EXAM_DETAILS_FIELD_KEYS}},
            )

        _persist_course_extra_fields(course.id, data)
        course.reload()

        serializer = CourseSerializer(course)
        raw = _fetch_course_extra_doc(course.id)
        return Response(
            {
                "success": True,
                "message": "Course updated successfully",
                "data": _merge_course_extra_from_doc(serializer.data, raw),
            }
        )

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="slug")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict(
                "This exam already exists for this provider.",
                field="slug",
            )
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ ADMIN: Delete Course
# ------------------------------------------------------------
@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def course_delete(request, course_id):
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))
        course.delete()

        return Response({"success": True, "message": "Course deleted successfully"})

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get courses by category
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def courses_by_category(request, category_slug):
    try:
        from categories.models import Category
        from practice_tests.models import PracticeTest

        category = Category.objects.get(slug=category_slug)
        courses = Course.objects(category=category, is_active=True).order_by('-created_at')

        limit_param = request.GET.get('limit')
        if limit_param:
            try:
                limit_n = max(1, min(50, int(limit_param)))
                courses = courses[:limit_n]
            except (TypeError, ValueError):
                pass

        # ✅ AUTO-SYNC: Ensure practice_exams count is accurate for each course
        for course in courses:
            actual_count = PracticeTest.objects(course=course).count()
            if course.practice_exams != actual_count:
                course.practice_exams = actual_count
                course.save()

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    except Category.DoesNotExist:
        return Response({"error": "Category not found"}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get courses by provider
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def courses_by_provider(request, provider_slug):
    try:
        from providers.models import Provider
        from practice_tests.models import PracticeTest
        from urllib.parse import unquote

        provider_slug = unquote(provider_slug).strip()
        provider = Provider.objects(slug=provider_slug).first()
        if not provider:
            provider = Provider.objects(slug__iexact=provider_slug).first()
        if not provider:
            return Response({"error": "Provider not found"}, status=404)

        courses = Course.objects(provider=provider, is_active=True).order_by('-created_at')

        limit_param = request.GET.get('limit')
        if limit_param:
            try:
                limit_n = max(1, min(50, int(limit_param)))
                courses = courses[:limit_n]
            except (TypeError, ValueError):
                pass

        for course in courses:
            actual_count = PracticeTest.objects(course=course).count()
            if course.practice_exams != actual_count:
                course.practice_exams = actual_count
                course.save()

        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get featured courses for homepage
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def featured_courses(request):
    """Featured courses for homepage Featured Exams and exam-page Popular Exams.

    Returns only courses marked is_featured in admin (Popular Exam / Featured checkbox).
    Optional ?fallback=1 restores legacy top-category picks when none are featured.
    """
    try:
        from practice_tests.models import PracticeTest
        from categories.models import Category

        featured = _get_admin_featured_courses()

        if featured:
            for course in featured:
                try:
                    actual_count = PracticeTest.objects(course=course).count()
                    if course.practice_exams != actual_count:
                        course.practice_exams = actual_count
                        course.save()
                except Exception:
                    pass

            serializer = CourseSerializer(featured, many=True)
            raw_by_id = _bulk_fetch_course_extra_docs(featured)
            merged = [
                _merge_course_extra_from_doc(item, raw_by_id.get(item.get("id")))
                for item in serializer.data
            ]
            return Response(merged)

        use_fallback = str(request.GET.get("fallback", "")).lower() in (
            "1",
            "true",
            "yes",
        )
        if not use_fallback:
            return Response([])

        def _is_top_certification_category(category):
            value = getattr(category, 'is_top_certification', False)
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return value != 0
            if isinstance(value, str):
                return value.strip().lower() in {'true', '1', 'yes', 'y', 'on'}
            return bool(value)

        top_categories = [
            category
            for category in Category.objects.all()
            if _is_top_certification_category(category)
        ]
        courses = []

        for category in top_categories:
            latest_course = (
                Course.objects(category=category, is_active=True)
                .order_by('-created_at')
                .first()
            )
            if latest_course:
                courses.append(latest_course)

        # ✅ AUTO-SYNC: Ensure practice_exams count is accurate for each course
        for course in courses:
            try:
                actual_count = PracticeTest.objects(course=course).count()
                if course.practice_exams != actual_count:
                    course.practice_exams = actual_count
                    course.save()
            except Exception:
                pass  # Skip sync if it fails, continue with existing count
        
        serializer = CourseSerializer(courses, many=True)
        raw_by_id = _bulk_fetch_course_extra_docs(courses)
        merged = [
            _merge_course_extra_from_doc(item, raw_by_id.get(item.get("id")))
            for item in serializer.data
        ]
        return Response(merged)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ------------------------------------------------------------
# ✅ ADMIN: Manage Pricing Data for a Course
# ------------------------------------------------------------
@api_view(['GET', 'PUT'])
@csrf_exempt
def manage_course_pricing(request, course_id):
    """
    GET: Fetch pricing data for a course
    PUT: Update pricing data for a course (Admin only)
    """
    try:
        if not ObjectId.is_valid(course_id):
            return Response({"error": "Invalid course ID"}, status=400)

        course = Course.objects.get(id=ObjectId(course_id))

        if request.method == 'GET':
            # Public can view pricing
            pricing_data = {
                "course_id": str(course.id),
                "course_title": course.title,
                "course_code": course.code,
                "currency": getattr(course, 'currency', 'INR') or 'INR',
                "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
                "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
                "pricing_plans": course.pricing_plans or [],
                "pricing_features": course.pricing_features or [],
                "pricing_testimonials": course.pricing_testimonials or [],
                "pricing_faqs": course.pricing_faqs or [],
                "pricing_comparison": course.pricing_comparison or [],
                "gst_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
                "tax_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
                "pricing_access_type": getattr(course, 'pricing_access_type', None) or 'paid',
            }
            return Response(pricing_data)

        elif request.method == 'PUT':
            # Admin only for updates
            authenticate(lambda req: req)(request)
            restrict(['admin'])(lambda req: req)(request)
            
            data = request.data
            
            # Update hero section
            if 'hero_title' in data:
                course.hero_title = data['hero_title']
            if 'hero_subtitle' in data:
                course.hero_subtitle = data['hero_subtitle']
            
            # Update pricing fields
            if 'pricing_plans' in data:
                course.pricing_plans = data['pricing_plans']
            if 'pricing_features' in data:
                course.pricing_features = data['pricing_features']
            if 'pricing_testimonials' in data:
                course.pricing_testimonials = data['pricing_testimonials']
            if 'pricing_faqs' in data:
                course.pricing_faqs = data['pricing_faqs']
            if 'pricing_comparison' in data:
                course.pricing_comparison = data['pricing_comparison']
            if 'gst_percentage' in data:
                course.gst_percentage = float(data['gst_percentage'] or 0)
            elif 'tax_percentage' in data:
                course.gst_percentage = float(data['tax_percentage'] or 0)
            if 'pricing_access_type' in data:
                access_type = str(data.get('pricing_access_type') or 'paid').strip().lower()
                course.pricing_access_type = 'free' if access_type == 'free' else 'paid'
            
            course.updated_at = datetime.datetime.utcnow()
            course.save()
            course.reload()

            return Response({
                "success": True,
                "message": "Pricing data updated successfully",
                "data": {
                    "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
                    "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
                    "pricing_plans": course.pricing_plans,
                    "pricing_features": course.pricing_features,
                    "pricing_testimonials": course.pricing_testimonials,
                    "pricing_faqs": course.pricing_faqs,
                    "pricing_comparison": course.pricing_comparison,
                    "gst_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
                    "tax_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
                    "pricing_access_type": getattr(course, 'pricing_access_type', None) or 'paid',
                }
            })

    except Course.DoesNotExist:
        return Response({"error": "Course not found"}, status=404)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)


# ------------------------------------------------------------
# ✅ PUBLIC: Get Pricing by Course Slug (SEO-Friendly)
# ------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def get_pricing_by_slug(request, provider, exam_code):
    """Get pricing data using provider and exam code (e.g., /api/pricing/azure/az-104/)"""
    try:
        from providers.models import Provider
        
        # Normalize inputs
        provider_normalized = provider.lower().replace('_', '-')
        exam_code_normalized = exam_code.lower().replace('_', '-')
        course_identifier = f"{provider_normalized}-{exam_code_normalized}"
        
        print(f"[DEBUG] Looking for course with identifier: {course_identifier}")
        
        course = None
        
        # 1️⃣ Try exact slug match first
        try:
            course = Course.objects.get(slug=course_identifier, is_active=True)
        except Course.DoesNotExist:
            # 2️⃣ Try case-insensitive slug match
            try:
                course = Course.objects.get(slug__iexact=course_identifier, is_active=True)
            except Course.DoesNotExist:
                # 3️⃣ Try provider-code format lookup (same logic as course_detail)
                all_parts = course_identifier.split('-')
                provider_obj = None
                provider_slug = None
                code_part = None
                
                # Strategy 1: Try two-word provider first (e.g., "sap-se")
                if len(all_parts) >= 3:
                    provider_slug_alt = f"{all_parts[0]}-{all_parts[1]}"
                    code_part_alt = '-'.join(all_parts[2:])
                    
                    provider_variants_alt = [
                        provider_slug_alt,
                        provider_slug_alt.upper(),
                        provider_slug_alt.capitalize(),
                        provider_slug_alt.replace('-', ' '),
                        provider_slug_alt.replace('-', ' ').title(),
                    ]
                    
                    for variant in provider_variants_alt:
                        try:
                            provider_obj = Provider.objects.get(slug=variant)
                            provider_slug = provider_slug_alt
                            code_part = code_part_alt
                            break
                        except Provider.DoesNotExist:
                            try:
                                provider_obj = Provider.objects.get(name__iexact=variant)
                                provider_slug = provider_slug_alt
                                code_part = code_part_alt
                                break
                            except Provider.DoesNotExist:
                                continue
                
                # Strategy 2: Try single-word provider (e.g., "sap")
                if not provider_obj and len(all_parts) >= 2:
                    provider_slug = all_parts[0]
                    code_part = '-'.join(all_parts[1:])
                    
                    provider_variants = [
                        provider_slug,
                        provider_slug.upper(),
                        provider_slug.capitalize(),
                        provider_slug.replace('-', ' '),
                        provider_slug.replace('-', ' ').title(),
                    ]
                    
                    for variant in provider_variants:
                        try:
                            provider_obj = Provider.objects.get(slug=variant)
                            break
                        except Provider.DoesNotExist:
                            try:
                                provider_obj = Provider.objects.get(name__iexact=variant)
                                break
                            except Provider.DoesNotExist:
                                continue
                    
                    # If still not found, try partial match
                    if not provider_obj:
                        try:
                            providers = Provider.objects.filter(slug__icontains=provider_slug)
                            if providers.count() == 1:
                                provider_obj = providers.first()
                        except Exception:
                            pass
                
                # Now try to find course with the found provider
                if provider_obj and code_part:
                    # Try multiple code format variations
                    code_variants = [
                        code_part.upper(),
                        code_part.upper().replace('-', '_'),
                        code_part.upper().replace('_', '-'),
                        code_part,
                        code_part.replace('-', '_').upper(),
                    ]
                    
                    # Try to find course by provider and code (try all variants)
                    for code_variant in code_variants:
                        try:
                            course = Course.objects.get(provider=provider_obj, code__iexact=code_variant, is_active=True)
                            break
                        except Course.DoesNotExist:
                            continue
                    
                    # If not found by code, try by slug variations
                    if not course:
                        slug_variants = [
                            f"{provider_slug}-{code_part.lower()}",
                            f"{provider_slug}-{code_part.lower().replace('_', '-')}",
                            course_identifier,
                        ]
                        
                        for slug_variant in slug_variants:
                            try:
                                course = Course.objects.get(provider=provider_obj, slug=slug_variant, is_active=True)
                                break
                            except Course.DoesNotExist:
                                try:
                                    course = Course.objects.get(provider=provider_obj, slug__iexact=slug_variant, is_active=True)
                                    break
                                except Course.DoesNotExist:
                                    continue
                    
                    # Last resort: try partial slug match
                    if not course:
                        try:
                            courses = Course.objects.filter(provider=provider_obj, slug__icontains=code_part.lower(), is_active=True)
                            if courses.count() == 1:
                                course = courses.first()
                        except Exception:
                            pass
                
                # Additional fallback: Try to find by code only (if provider matches)
                if not course and provider_obj and code_part:
                    try:
                        code_upper = code_part.upper()
                        courses = Course.objects.filter(provider=provider_obj, code__iexact=code_upper, is_active=True)
                        if courses.count() == 1:
                            course = courses.first()
                    except Exception:
                        pass
                
                # Final fallback: Try to find by exam code in any course (regardless of provider)
                # This handles cases where provider name in URL doesn't match database provider name
                if not course:
                    # Try by code in all courses (case-insensitive) - handles cases where provider name doesn't match
                    try:
                        code_to_match = code_part.upper() if code_part else exam_code_normalized.upper()
                        # Try multiple code format variations (including variations with/without hyphens)
                        code_variants = [
                            code_to_match,
                            code_to_match.replace('-', '_'),
                            code_to_match.replace('_', '-'),
                            code_to_match.replace('-', ''),  # Remove all hyphens
                            exam_code_normalized.upper(),
                            exam_code_normalized.upper().replace('-', '_'),
                            exam_code_normalized.upper().replace('_', '-'),
                            exam_code_normalized.upper().replace('-', ''),  # Remove all hyphens
                        ]
                        for code_var in code_variants:
                            courses = Course.objects.filter(code__iexact=code_var, is_active=True)
                            if courses.count() == 1:
                                course = courses.first()
                                print(f"[DEBUG] Found course by code variant '{code_var}': {course.title}")
                                break
                            elif courses.count() > 1:
                                # If multiple courses found, try to match by provider if we have one
                                if provider_obj:
                                    matched = courses.filter(provider=provider_obj).first()
                                    if matched:
                                        course = matched
                                        print(f"[DEBUG] Found course by code variant '{code_var}' with provider match: {course.title}")
                                        break
                    except Exception as e:
                        print(f"[DEBUG] Error in code variant lookup: {str(e)}")
                        pass
                    
                    # Try by partial slug match with exam code
                    if not course:
                        try:
                            search_term = code_part.lower() if code_part else exam_code_normalized.lower()
                            # Try with and without hyphens
                            search_terms = [
                                search_term,
                                search_term.replace('-', ''),
                                search_term.replace('-', '_'),
                            ]
                            for term in search_terms:
                                courses = Course.objects.filter(slug__icontains=term, is_active=True)
                                if courses.count() == 1:
                                    course = courses.first()
                                    print(f"[DEBUG] Found course by slug search term '{term}': {course.title}")
                                    break
                                elif courses.count() > 1 and provider_obj:
                                    matched = courses.filter(provider=provider_obj).first()
                                    if matched:
                                        course = matched
                                        print(f"[DEBUG] Found course by slug search term '{term}' with provider match: {course.title}")
                                        break
                        except Exception as e:
                            print(f"[DEBUG] Error in slug search: {str(e)}")
                            pass
        
        if not course:
            # Return 404 so frontend can fallback to course API
            return Response({
                "success": False,
                "error": "Course not found",
                "message": "Course not found for the given provider and exam code"
            }, status=404)
        
        # Ensure pricing_plans is properly loaded - reload course to get latest data
        course.reload()
        
        # Get pricing plans - ensure it's a list and filter out None/empty values
        pricing_plans = course.pricing_plans or []
        if pricing_plans:
            # Filter out any None or invalid entries and ensure status field exists
            pricing_plans = [plan for plan in pricing_plans if plan and isinstance(plan, dict)]
            # Ensure each plan has a status field (default to 'active' if missing)
            for plan in pricing_plans:
                if 'status' not in plan:
                    plan['status'] = 'active'
        
        # Ensure each plan carries course-level GST for checkout clients
        course_gst = float(getattr(course, 'gst_percentage', 0) or 0)
        for plan in pricing_plans:
            plan_gst = plan.get('gst_percentage')
            if plan_gst is None or plan_gst == '':
                plan_gst = plan.get('tax_percentage')
            if plan_gst is None or plan_gst == '':
                plan_gst = course_gst
            plan['gst_percentage'] = float(plan_gst or 0)
            plan['tax_percentage'] = float(plan_gst or 0)
        
        pricing_data = {
            "success": True,
            "course_id": str(course.id),
            "course_title": course.title or "",
            "course_code": course.code or "",
            "provider": course.provider.name if course.provider else "",
            "currency": getattr(course, 'currency', 'INR') or 'INR',
            "hero_title": getattr(course, 'hero_title', 'Choose Your Access Plan'),
            "hero_subtitle": getattr(course, 'hero_subtitle', 'Unlock full access for this exam — all questions, explanations, analytics, and unlimited attempts.'),
            "pricing_plans": pricing_plans,
            "pricing_features": course.pricing_features or [],
            "pricing_testimonials": course.pricing_testimonials or [],
            "pricing_faqs": course.pricing_faqs or [],
            "pricing_comparison": course.pricing_comparison or [],
            # GST % configured in admin pricing section
            "gst_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
            "tax_percentage": float(getattr(course, 'gst_percentage', 0) or 0),
            "pricing_access_type": getattr(course, 'pricing_access_type', None) or 'paid',
        }
        print(f"[DEBUG] Found course: {course.title} (ID: {course.id}, Slug: {course.slug}) with {len(pricing_plans)} pricing plans")
        return Response(pricing_data, status=200)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            "success": False,
            "error": str(e),
            "message": "An error occurred while fetching pricing data"
        }, status=500)


