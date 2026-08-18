from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from mongoengine.errors import NotUniqueError
from django.utils.text import slugify
from .models import Provider
from .serializers import ProviderSerializer
from bson import ObjectId
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from common.middleware import authenticate, restrict
from common.duplicate_validation import duplicate_conflict, not_unique_conflict
from common.image_utils import convert_uploaded_image_to_webp
from common.text_limits import clamp_to_word_limit
from common.pagination import (
    apply_allowlisted_ordering,
    paginate_mongoengine_queryset,
    paginated_admin_payload,
    parse_pagination_params,
    regex_search_filter,
)
import json
import re


def _clamp_provider_description(value):
    return clamp_to_word_limit(value)


def _invalidate_public_provider_cache():
    from common.public_cache import cache_delete_prefix, invalidate_public_http_paths
    cache_delete_prefix("provider:")
    invalidate_public_http_paths("/api/providers")


def _provider_name_taken(name, exclude_id=None):
    normalized = (name or "").strip()
    if not normalized:
        return False
    existing = Provider.objects(name__iexact=normalized).first()
    if not existing:
        return False
    if exclude_id and str(existing.id) == str(exclude_id):
        return False
    return True


def _provider_slug_taken(slug, exclude_id=None):
    normalized = (slug or "").strip().lower()
    if not normalized:
        return False
    existing = Provider.objects(slug__iexact=normalized).first()
    if not existing:
        return False
    if exclude_id and str(existing.id) == str(exclude_id):
        return False
    return True

def _parse_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _positive_int_param(request, name, default, maximum=None):
    try:
        value = int(request.GET.get(name, default))
    except (TypeError, ValueError):
        value = default
    value = max(1, value)
    if maximum is not None:
        value = min(value, maximum)
    return value


def _paginated_response(results, count, page, page_size):
    total_pages = max(1, (count + page_size - 1) // page_size)
    return {
        "results": results,
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def _course_listing_projection():
    text_present = lambda field: {
        "$gt": [{"$strLenCP": {"$ifNull": [f"${field}", ""]}}, 0]
    }
    array_present = lambda field: {
        "$gt": [{"$size": {"$ifNull": [f"${field}", []]}}, 0]
    }
    return {
        "$project": {
            "provider": 1,
            "title": 1,
            "code": 1,
            "slug": 1,
            "is_active": 1,
            "created_at": 1,
            "show_in_official_details": 1,
            "official_details_url_slug": 1,
            "has_exam_details": {
                "$or": [
                    text_present("about"),
                    text_present("page_heading"),
                    text_present("exam_details"),
                    text_present("details"),
                    text_present("meta_title"),
                    array_present("topics"),
                    array_present("testimonials"),
                    array_present("faqs"),
                ]
            },
        }
    }


def _course_listing_visibility_match():
    distinct_official_slug = {
        "$and": [
            {"$gt": [{"$strLenCP": {"$ifNull": ["$slug", ""]}}, 0]},
            {"$gt": [{"$strLenCP": {"$ifNull": ["$official_details_url_slug", ""]}}, 0]},
            {"$ne": ["$slug", "$official_details_url_slug"]},
        ]
    }
    return {
        "$or": [
            {"show_in_official_details": {"$ne": True}},
            {"has_exam_details": True},
            {"$expr": distinct_official_slug},
        ]
    }


def _visible_course_pipeline(match):
    return [
        {"$match": match},
        _course_listing_projection(),
        {"$match": _course_listing_visibility_match()},
    ]


def _exam_provider_ids_for_search(search):
    from courses.models import Course

    if not search:
        return []
    regex = {"$regex": re.escape(search), "$options": "i"}
    rows = Course._get_collection().aggregate([
        *_visible_course_pipeline({
            "is_active": True,
            "$or": [
                {"title": regex},
                {"code": regex},
                {"slug": regex},
            ],
        }),
        {"$group": {"_id": "$provider"}},
    ])
    return [row["_id"] for row in rows if row.get("_id")]


def _provider_exam_counts(provider_ids):
    from courses.models import Course

    if not provider_ids:
        return {}
    rows = Course._get_collection().aggregate([
        *_visible_course_pipeline({
            "is_active": True,
            "provider": {"$in": provider_ids},
        }),
        {"$group": {"_id": "$provider", "count": {"$sum": 1}}},
    ])
    return {str(row["_id"]): row.get("count", 0) for row in rows if row.get("_id")}


def _provider_exam_previews(provider_docs, limit):
    from courses.models import Course

    previews = {}
    if not provider_docs or limit <= 0:
        return previews
    for provider in provider_docs:
        provider_id = provider.get("_id")
        if not provider_id:
            continue
        docs = list(Course._get_collection().aggregate([
            *_visible_course_pipeline({
                "is_active": True,
                "provider": provider_id,
            }),
            {"$sort": {"title": 1, "created_at": -1}},
            {"$limit": limit},
        ]))
        previews[str(provider_id)] = [
            {
                "id": str(doc.get("_id")),
                "provider": provider.get("name") or "",
                "provider_id": str(provider_id),
                "provider_slug": provider.get("slug") or "",
                "title": doc.get("title") or "",
                "name": doc.get("title") or "",
                "code": doc.get("code") or "",
                "slug": doc.get("slug") or "",
                "is_active": doc.get("is_active", True),
            }
            for doc in docs
        ]
    return previews


def _provider_lite_row(provider, exam_counts=None, exam_previews=None):
    provider_id = str(provider.get("_id"))
    row = {
        "id": provider_id,
        "name": provider.get("name") or "",
        "icon": provider.get("icon") or "",
        "slug": provider.get("slug") or "",
        "logo_url": provider.get("logo_url"),
        "description": provider.get("description") or "",
        "order": provider.get("order", 0),
        "is_active": provider.get("is_active", True),
        "show_in_popular_providers": provider.get(
            "show_in_popular_providers",
            True,
        ),
    }
    if exam_counts is not None:
        row["exam_count"] = exam_counts.get(provider_id, 0)
    if exam_previews is not None:
        row["exams"] = exam_previews.get(provider_id, [])
    return row


# ✅ List all active providers (Public)
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def provider_list(request):
    lite = request.GET.get("lite", "").lower() in ("1", "true", "yes")
    popular_only = request.GET.get("popular_only", "").lower() in ("1", "true", "yes")
    wants_pagination = (
        "page" in request.GET
        or "page_size" in request.GET
        or "limit" in request.GET
    )
    include_exam_counts = _parse_bool(
        request.GET.get("include_exam_counts"),
        default=False,
    )
    include_exam_preview = _parse_bool(
        request.GET.get("include_exam_preview"),
        default=False,
    )
    search = str(
        request.GET.get("q")
        or request.GET.get("search")
        or ""
    ).strip()
    if lite:
        query = {"is_active": True}
        if popular_only:
            query["show_in_popular_providers"] = True
        if search:
            regex = {"$regex": re.escape(search), "$options": "i"}
            search_or = [
                {"name": regex},
                {"slug": regex},
                {"description": regex},
            ]
            exam_provider_ids = _exam_provider_ids_for_search(search)
            if exam_provider_ids:
                search_or.append({"_id": {"$in": exam_provider_ids}})
            query["$and"] = [
                {"$or": query.pop("$or")} if "$or" in query else {},
                {"$or": search_or},
            ]
            query["$and"] = [item for item in query["$and"] if item]
        projection = {
            "name": 1,
            "icon": 1,
            "slug": 1,
            "logo_url": 1,
            "description": 1,
            "order": 1,
            "is_active": 1,
            "show_in_popular_providers": 1,
        }
        if wants_pagination:
            page = _positive_int_param(request, "page", 1)
            page_size = _positive_int_param(
                request,
                "page_size",
                _positive_int_param(request, "limit", 24, 100),
                100,
            )
            skip = (page - 1) * page_size
            total_count = Provider._get_collection().count_documents(query)
            provider_docs = list(
                Provider._get_collection().find(query, projection)
                .sort("order", 1)
                .skip(skip)
                .limit(page_size)
            )
            provider_ids = [doc["_id"] for doc in provider_docs if doc.get("_id")]
            exam_counts = (
                _provider_exam_counts(provider_ids)
                if include_exam_counts or include_exam_preview
                else None
            )
            exam_previews = (
                _provider_exam_previews(
                    provider_docs,
                    _positive_int_param(request, "exam_preview_limit", 5, 20),
                )
                if include_exam_preview
                else None
            )
            return Response(
                _paginated_response(
                    [
                        _provider_lite_row(doc, exam_counts, exam_previews)
                        for doc in provider_docs
                    ],
                    total_count,
                    page,
                    page_size,
                )
            )
        providers = Provider._get_collection().find(
            query,
            projection,
        ).sort("order", 1)
        provider_docs = list(providers)
        provider_ids = [doc["_id"] for doc in provider_docs if doc.get("_id")]
        exam_counts = (
            _provider_exam_counts(provider_ids)
            if include_exam_counts or include_exam_preview
            else None
        )
        exam_previews = (
            _provider_exam_previews(
                provider_docs,
                _positive_int_param(request, "exam_preview_limit", 5, 20),
            )
            if include_exam_preview
            else None
        )
        return Response([
            _provider_lite_row(provider, exam_counts, exam_previews)
            for provider in provider_docs
        ])

    providers = Provider.objects(is_active=True)
    if popular_only:
        providers = providers.filter(show_in_popular_providers=True)
    providers = providers.order_by('order')
    serializer = ProviderSerializer(
        providers,
        many=True,
        context={"request": request, "lite": lite},
    )
    return Response(serializer.data)


# ✅ Create provider
@api_view(['POST'])
@permission_classes([AllowAny])
def provider_create(request):
    serializer = ProviderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        _invalidate_public_provider_cache()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# ✅ Get single provider by slug
@api_view(['GET'])
@permission_classes([AllowAny])
def provider_detail(request, provider_slug):
    from common.public_cache import cache_get, cache_set, public_json_response

    cache_key = f"provider:detail:{provider_slug}"
    cached = cache_get(cache_key)
    if cached is not None:
        return public_json_response(cached)

    provider = Provider.objects(slug=provider_slug).first()
    if not provider:
        return Response({'error': 'Provider not found'}, status=404)
    serializer = ProviderSerializer(provider, context={'request': request})
    payload = serializer.data
    cache_set(cache_key, payload)
    return public_json_response(payload)


# ✅ Update provider by slug
@api_view(['PUT', 'PATCH'])
@permission_classes([AllowAny])
def provider_update(request, provider_slug):
    provider = Provider.objects(slug=provider_slug).first()
    if not provider:
        return Response({'error': 'Provider not found'}, status=404)
    serializer = ProviderSerializer(provider, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        _invalidate_public_provider_cache()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)


# ✅ Delete provider by slug
@api_view(['DELETE'])
@permission_classes([AllowAny])
def provider_delete(request, provider_slug):
    provider = Provider.objects(slug=provider_slug).first()
    if not provider:
        return Response({'error': 'Provider not found'}, status=404)
    provider.delete()
    _invalidate_public_provider_cache()
    return Response({'message': 'Provider deleted successfully'}, status=200)


# ✅ Bulk delete providers by slugs
@api_view(['POST'])
@permission_classes([AllowAny])
def provider_bulk_delete(request):
    slugs = request.data.get('slugs', [])
    if not isinstance(slugs, list) or not slugs:
        return Response({'error': 'Provide a list of provider slugs'}, status=400)
    deleted_count = Provider.objects(slug__in=slugs).delete()
    return Response({'message': 'Bulk delete completed', 'deleted': deleted_count})


# =================== ADMIN ENDPOINTS ===================

# ✅ Admin: Get all providers (including inactive)
@api_view(['GET'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_provider_list(request):
    """Admin: Get all providers"""
    try:
        page, page_size = parse_pagination_params(request)
        raw_query = regex_search_filter(
            request.GET.get("search") or request.GET.get("q"),
            ["name", "slug", "description"],
        )
        providers = Provider.objects(__raw__=raw_query) if raw_query else Provider.objects.all()
        providers, _ordering = apply_allowlisted_ordering(
            providers,
            request.GET.get("ordering"),
            {"order", "-order", "name", "-name", "created_at", "-created_at"},
            "order",
        )
        page_providers, pagination = paginate_mongoengine_queryset(
            providers,
            page,
            page_size,
        )
        serializer = ProviderSerializer(
            list(page_providers),
            many=True,
            context={'request': request},
        )
        return Response(
            paginated_admin_payload(
                serializer.data,
                pagination["count"],
                pagination["page"],
                pagination["page_size"],
            )
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Admin: Create provider
@api_view(['POST'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_provider_create(request):
    """Admin: Create a new provider"""
    try:
        # DRF request.data handles both JSON and multipart reliably
        data = {}
        for key in request.data:
            data[key] = request.data.get(key)
        
        # Validate required fields
        if not data.get('name') or not data.get('icon'):
            return Response(
                {"error": "Name and icon are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse FAQs payload (supports JSON string from multipart or list from JSON body)
        raw_faqs = data.get('faqs', [])
        if isinstance(raw_faqs, str):
            try:
                raw_faqs = json.loads(raw_faqs)
            except json.JSONDecodeError:
                raw_faqs = []
        if not isinstance(raw_faqs, list):
            raw_faqs = []
        faqs = []
        for faq in raw_faqs:
            if not isinstance(faq, dict):
                continue
            question = str(faq.get('question', '')).strip()
            answer = str(faq.get('answer', '')).strip()
            if question and answer:
                faqs.append({'question': question, 'answer': answer})

        # Convert order to int if it's a string
        order = data.get('order', 0)
        if isinstance(order, str):
            try:
                order = int(order)
            except (ValueError, TypeError):
                order = 0
        
        # Convert is_active to boolean if it's a string
        is_active = _parse_bool(data.get('is_active', True), default=True)
        show_in_popular_providers = _parse_bool(
            data.get('show_in_popular_providers', False),
            default=False,
        )
        
        provider_name = str(data["name"]).strip()
        provider_slug = slugify(data.get("slug") or provider_name)

        if _provider_name_taken(provider_name):
            return duplicate_conflict(
                f'A provider named "{provider_name}" already exists.',
                field="name",
            )
        if _provider_slug_taken(provider_slug):
            return duplicate_conflict(
                f'A provider with slug "{provider_slug}" already exists.',
                field="slug",
            )

        # Create provider
        provider = Provider(
            name=provider_name,
            icon=data['icon'],
            slug=provider_slug,
            logo_url=data.get('logo_url', ''),  # Cloudinary URL from frontend
            page_title=data.get('page_title', ''),
            description=_clamp_provider_description(data.get('description', '')),
            content=data.get('content', ''),
            faqs=faqs,
            meta_title=data.get('meta_title', ''),
            meta_keywords=data.get('meta_keywords', ''),
            meta_description=data.get('meta_description', ''),
            order=order,
            is_active=is_active,
            show_in_popular_providers=show_in_popular_providers,
        )
        
        # Handle logo file upload (legacy support)
        logo_file = request.FILES.get('logo')
        if logo_file:
            logo_file = convert_uploaded_image_to_webp(logo_file)
            provider.logo.put(logo_file, content_type=getattr(logo_file, "content_type", None) or "image/webp")
            provider.logo_url = None
        
        try:
            provider.save()
        except NotUniqueError as exc:
            return not_unique_conflict(exc, field="name")

        serializer = ProviderSerializer(provider, context={'request': request})
        return Response(
            {"success": True, "message": "Provider created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )
    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="name")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict("This provider already exists.", field="name")
        import traceback
        error_msg = str(e)
        if settings.DEBUG:
            error_msg += f"\n{traceback.format_exc()}"
        return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Admin: Update provider by ID
@api_view(['PUT'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_provider_update(request, provider_id):
    """Admin: Update a provider"""
    try:
        if not ObjectId.is_valid(provider_id):
            return Response({"error": "Invalid provider ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        provider = Provider.objects.get(id=ObjectId(provider_id))
        
        # DRF request.data handles both JSON and multipart reliably
        data = {}
        for key in request.data:
            data[key] = request.data.get(key)
        
        # Parse FAQs payload (supports JSON string from multipart or list from JSON body)
        if 'faqs' in data:
            raw_faqs = data.get('faqs', [])
            if isinstance(raw_faqs, str):
                try:
                    raw_faqs = json.loads(raw_faqs)
                except json.JSONDecodeError:
                    raw_faqs = []
            if not isinstance(raw_faqs, list):
                raw_faqs = []
            faqs = []
            for faq in raw_faqs:
                if not isinstance(faq, dict):
                    continue
                question = str(faq.get('question', '')).strip()
                answer = str(faq.get('answer', '')).strip()
                if question and answer:
                    faqs.append({'question': question, 'answer': answer})
            provider.faqs = faqs

        next_name = provider.name
        next_slug = provider.slug

        # Update fields only if provided
        if 'name' in data:
            next_name = str(data['name']).strip()
            provider.name = next_name
        if 'icon' in data:
            provider.icon = data['icon']
        if 'slug' in data:
            next_slug = slugify(data['slug'] or next_name)
            provider.slug = next_slug
        elif 'name' in data and not (data.get('slug') or '').strip():
            next_slug = slugify(next_name)
            provider.slug = next_slug

        if _provider_name_taken(next_name, exclude_id=provider_id):
            return duplicate_conflict(
                f'A provider named "{next_name}" already exists.',
                field="name",
            )
        if _provider_slug_taken(next_slug, exclude_id=provider_id):
            return duplicate_conflict(
                f'A provider with slug "{next_slug}" already exists.',
                field="slug",
            )
        if 'description' in data:
            provider.description = _clamp_provider_description(data['description'])
        if 'website_url' in data:
            provider.website_url = data['website_url']
        if 'logo_url' in data:
            # If logo_url is empty string, clear it (remove logo)
            if data['logo_url'] == '' or data['logo_url'] is None:
                provider.logo_url = None
            else:
                provider.logo_url = data['logo_url']
        if 'meta_title' in data:
            provider.meta_title = data['meta_title']
        if 'meta_keywords' in data:
            provider.meta_keywords = data['meta_keywords']
        if 'meta_description' in data:
            provider.meta_description = data['meta_description']
        if 'page_title' in data:
            provider.page_title = data['page_title']
        if 'content' in data:
            provider.content = data['content']
        
        # Convert order to int if provided
        if 'order' in data:
            order = data['order']
            if isinstance(order, str):
                try:
                    order = int(order)
                except (ValueError, TypeError):
                    order = provider.order
            provider.order = order
        
        # Convert is_active to boolean if provided
        if 'is_active' in data:
            provider.is_active = _parse_bool(data['is_active'], default=provider.is_active)

        if 'show_in_popular_providers' in data:
            provider.show_in_popular_providers = _parse_bool(
                data['show_in_popular_providers'],
                default=getattr(provider, 'show_in_popular_providers', False),
            )
        
        # Handle logo removal
        remove_logo_val = data.get("remove_logo", False)
        if isinstance(remove_logo_val, bool):
            remove_logo = remove_logo_val
        elif remove_logo_val is None:
            remove_logo = False
        else:
            remove_logo = str(remove_logo_val).strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )
        if remove_logo:
            if provider.logo:
                provider.logo.delete()
            provider.logo = None
            # Also clear logo_url when removing logo
            provider.logo_url = None
        
        # Handle logo file upload (only if not removing)
        if not remove_logo:
            logo_file = request.FILES.get('logo')
            if logo_file:
                logo_file = convert_uploaded_image_to_webp(logo_file)
                # Delete old logo if exists
                if provider.logo:
                    provider.logo.delete()
                provider.logo.put(logo_file, content_type=getattr(logo_file, "content_type", None) or "image/webp")
                provider.logo_url = None
        
        try:
            provider.save()
        except NotUniqueError as exc:
            return not_unique_conflict(exc, field="name")

        serializer = ProviderSerializer(provider, context={'request': request})
        return Response({"success": True, "message": "Provider updated successfully", "data": serializer.data})
    except Provider.DoesNotExist:
        return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="name")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict("This provider already exists.", field="name")
        import traceback
        error_msg = str(e)
        if settings.DEBUG:
            error_msg += f"\n{traceback.format_exc()}"
        return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Admin: Delete provider by ID
@api_view(['DELETE'])
@authenticate
@restrict(['admin'])
@csrf_exempt
def admin_provider_delete(request, provider_id):
    """Admin: Delete a provider"""
    try:
        if not ObjectId.is_valid(provider_id):
            return Response({"error": "Invalid provider ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        provider = Provider.objects.get(id=ObjectId(provider_id))
        provider.delete()
        return Response(
            {"success": True, "message": "Provider deleted successfully"},
            status=status.HTTP_200_OK
        )
    except Provider.DoesNotExist:
        return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ✅ Get provider logo image
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def provider_logo(request, provider_id):
    """Serve provider logo image file"""
    try:
        if not ObjectId.is_valid(provider_id):
            return JsonResponse({"error": "Invalid provider ID"}, status=400)
        
        provider = Provider.objects.get(id=ObjectId(provider_id))
        
        if not provider.logo:
            return JsonResponse({"error": "Logo not found"}, status=404)
        
        image_data = provider.logo.read()
        content_type = getattr(provider.logo, 'content_type', 'image/jpeg')
        response = HttpResponse(image_data, content_type=content_type)
        file_ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
        response['Content-Disposition'] = f'inline; filename="provider_{provider_id}_logo.{file_ext}"'
        return response
        
    except Provider.DoesNotExist:
        return JsonResponse({"error": "Provider not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
