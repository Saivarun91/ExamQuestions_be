import mimetypes

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from mongoengine.errors import NotUniqueError
from .models import Category
from .serializers import CategorySerializer
from bson import ObjectId
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from common.duplicate_validation import duplicate_conflict, not_unique_conflict
from common.image_utils import convert_uploaded_image_to_webp
from common.pagination import (
    apply_allowlisted_ordering,
    paginate_mongoengine_queryset,
    paginated_admin_payload,
    parse_pagination_params,
    regex_search_filter,
)


def _positive_int_param(value, default, max_value=None):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default

    parsed = max(1, parsed)
    if max_value is not None:
        parsed = min(parsed, max_value)
    return parsed


def _category_course_counts(category_ids):
    if not category_ids:
        return {}
    from courses.models import Course

    rows = Course._get_collection().aggregate([
        {"$match": {"category": {"$in": category_ids}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
    ])
    return {str(row["_id"]): row.get("count", 0) for row in rows if row.get("_id")}


def _category_paginated_payload(request):
    page, page_size = parse_pagination_params(request)
    raw_query = {}
    search_query = regex_search_filter(
        request.GET.get("search") or request.GET.get("q"),
        ["title", "slug", "description", "main_category"],
    )
    if search_query:
        raw_query.update(search_query)

    is_top = request.GET.get("is_top_certification")
    if is_top is not None and str(is_top).strip() != "":
        raw_query["is_top_certification"] = str(is_top).lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

    queryset = Category.objects(__raw__=raw_query) if raw_query else Category.objects.all()
    queryset, _ordering = apply_allowlisted_ordering(
        queryset,
        request.GET.get("ordering"),
        {"title", "-title", "slug", "-slug", "main_category", "-main_category"},
        "title",
    )
    page_categories, pagination = paginate_mongoengine_queryset(queryset, page, page_size)
    page_categories = list(page_categories)
    course_counts = _category_course_counts([category.id for category in page_categories])
    serializer = CategorySerializer(
        page_categories,
        many=True,
        context={"request": request},
    )
    data = [
        {
            **item,
            "course_count": course_counts.get(str(item.get("id")), 0),
        }
        for item in serializer.data
    ]
    return paginated_admin_payload(
        data,
        pagination["count"],
        pagination["page"],
        pagination["page_size"],
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """List all categories"""
    try:
        wants_pagination = (
            "page" in request.GET
            or "page_size" in request.GET
            or "search" in request.GET
            or "q" in request.GET
        )
        if wants_pagination:
            return Response(_category_paginated_payload(request), status=status.HTTP_200_OK)

        lite = request.GET.get("lite", "").lower() in ("1", "true", "yes")
        if lite:
            categories = Category._get_collection().find(
                {},
                {
                    "title": 1,
                    "slug": 1,
                    "main_category": 1,
                    "icon": 1,
                    "is_top_certification": 1,
                    "is_active": 1,
                },
            ).sort("title", 1)
            return Response(
                [
                    {
                        "id": str(category.get("_id")),
                        "title": category.get("title") or "",
                        "name": category.get("title") or "",
                        "slug": category.get("slug") or "",
                        "main_category": category.get("main_category") or "",
                        "icon": category.get("icon") or "",
                        "is_top_certification": category.get(
                            "is_top_certification",
                            False,
                        ),
                        "is_active": category.get("is_active", True),
                    }
                    for category in categories
                ],
                status=status.HTTP_200_OK,
            )

        categories = Category.objects.all()
        serializer = CategorySerializer(
            categories, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def category_top_certifications(request):
    """List paginated top certification categories."""
    try:
        page = _positive_int_param(request.GET.get("page"), 1)
        page_size = _positive_int_param(request.GET.get("page_size"), 8, 100)
        offset = (page - 1) * page_size

        categories = Category.objects(
            __raw__={
                "is_top_certification": True,
                "is_active": {"$ne": False},
            }
        ).order_by("title")
        total_items = categories.count()
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        page = min(page, total_pages)
        offset = (page - 1) * page_size

        serializer = CategorySerializer(
            categories.skip(offset).limit(page_size),
            many=True,
            context={"request": request},
        )

        return Response(
            {
                "results": serializer.data,
                "count": total_items,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def category_create(request):
    """Create a new category"""
    try:
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
            except NotUniqueError as exc:
                return not_unique_conflict(exc, field="title")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        errors = serializer.errors
        title_errors = errors.get("title")
        if title_errors:
            message = title_errors[0] if isinstance(
                title_errors, list) else str(title_errors)
            if "already exists" in str(message).lower():
                return duplicate_conflict(str(message), field="title")
        return Response(
            {"success": False, "errors": errors, "error": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="title")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict("This category already exists.", field="title")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def category_detail(request, slug):
    """Get a single category by slug"""
    try:
        category = Category.objects(slug=slug).first()
        if not category:
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([AllowAny])
def category_update(request, slug):
    """Update a category"""
    try:
        category = Category.objects(slug=slug).first()
        if not category:
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        remove_image = request.data.get("remove_image")
        if isinstance(remove_image, bool):
            should_remove_image = remove_image
        elif remove_image is None:
            should_remove_image = False
        else:
            should_remove_image = str(remove_image).strip().lower() in (
                "true",
                "1",
                "yes",
                "on",
            )

        if should_remove_image:
            try:
                if getattr(category, "image", None):
                    category.image.delete()
            except Exception:
                pass
            category.image = None
            category.image_url = None
            category.save()

        serializer = CategorySerializer(
            category, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
            except NotUniqueError as exc:
                return not_unique_conflict(exc, field="title")
            return Response(serializer.data, status=status.HTTP_200_OK)
        errors = serializer.errors
        title_errors = errors.get("title")
        if title_errors:
            message = title_errors[0] if isinstance(
                title_errors, list) else str(title_errors)
            if "already exists" in str(message).lower():
                return duplicate_conflict(str(message), field="title")
        return Response(
            {"success": False, "errors": errors, "error": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except NotUniqueError as exc:
        return not_unique_conflict(exc, field="title")
    except Exception as e:
        if "duplicate key" in str(e).lower() or "E11000" in str(e):
            return duplicate_conflict("This category already exists.", field="title")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])
def category_delete(request, slug):
    """Delete a category"""
    try:
        category = Category.objects(slug=slug).first()
        if not category:
            return Response(
                {"error": "Category not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        category.delete()
        return Response(
            {"message": "Category deleted successfully"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser])
@csrf_exempt
def category_upload_image(request, slug):
    """Upload category image file (stores in GridFS via MongoEngine FileField)."""
    try:
        category = Category.objects(slug=slug).first()
        if not category:
            return Response({"error": "Category not found"}, status=404)

        file_obj = request.FILES.get("image")
        if not file_obj:
            return Response({"error": "No image file provided"}, status=400)

        file_obj = convert_uploaded_image_to_webp(file_obj)

        # Replace existing uploaded image if any
        try:
            if getattr(category, "image", None):
                category.image.delete()
        except Exception:
            pass

        content_type = getattr(file_obj, "content_type", None) or mimetypes.guess_type(
            getattr(file_obj, "name", "") or ""
        )[0] or "image/webp"
        category.image.put(file_obj, content_type=content_type)
        # Clear explicit image_url so serializer serves uploaded image
        category.image_url = None
        category.save()

        serializer = CategorySerializer(category, context={"request": request})
        return Response(serializer.data, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
@csrf_exempt
def category_image(request, category_id):
    """Serve uploaded category image file."""
    try:
        if not ObjectId.is_valid(str(category_id)):
            return Response({"error": "Invalid category id"}, status=400)
        category = Category.objects(id=ObjectId(category_id)).first()
        if not category or not getattr(category, "image", None):
            return Response({"error": "Image not found"}, status=404)

        image_data = category.image.read()
        content_type = getattr(category.image, "content_type", "image/jpeg")
        return HttpResponse(image_data, content_type=content_type)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
