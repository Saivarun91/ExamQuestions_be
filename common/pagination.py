import math
import re


DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def parse_pagination_params(request, default_size=DEFAULT_PAGE_SIZE, max_size=MAX_PAGE_SIZE):
    """Return safe page/page_size integers for admin list endpoints."""
    page = _positive_int(request.GET.get("page"), 1)
    requested_size = (
        request.GET.get("page_size")
        or request.GET.get("limit")
        or default_size
    )
    page_size = _positive_int(requested_size, default_size)
    page_size = min(page_size, max_size)
    return page, page_size


def pagination_metadata(count, page, page_size):
    total_pages = max(1, math.ceil((count or 0) / page_size))
    page = min(max(1, page), total_pages)
    return {
        "count": count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }


def paginated_admin_payload(data, count, page, page_size):
    metadata = pagination_metadata(count, page, page_size)
    return {
        "success": True,
        "data": data,
        "pagination": metadata,
    }


def paginate_mongoengine_queryset(queryset, page, page_size):
    count = queryset.count()
    metadata = pagination_metadata(count, page, page_size)
    offset = (metadata["page"] - 1) * page_size
    return queryset.skip(offset).limit(page_size), metadata


def apply_allowlisted_ordering(queryset, requested_ordering, allowed_ordering, default_ordering):
    ordering = requested_ordering if requested_ordering in allowed_ordering else default_ordering
    return queryset.order_by(ordering), ordering


def regex_search_filter(search, fields):
    search = str(search or "").strip()
    if not search:
        return None
    regex = {"$regex": re.escape(search), "$options": "i"}
    return {"$or": [{field: regex} for field in fields]}


def _positive_int(value, default):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, parsed)
