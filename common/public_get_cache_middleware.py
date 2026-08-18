"""Cache public JSON GET responses so SSR and crawlers reuse work.

Does not change payloads. Admin writes still go through the view; TTL plus
explicit invalidation on course/settings updates keeps data reasonably fresh.
Never caches questions, auth, payments, or binary image routes.
"""

from django.http import HttpResponse

from common.public_cache import DEFAULT_TTL_SECONDS, cache_get, cache_set

_CACHE_PREFIXES = (
    "/api/home/",
    "/api/settings/",
    "/api/categories/",
    "/api/providers/",
    "/api/courses/",
)

_SKIP_SUBSTRINGS = (
    "/admin/",
    "/image",
    "/logo",
    "/upload",
    "/create/",
    "/update/",
    "/delete",
)

_MAX_BODY_BYTES = 800_000


def _cacheable_request(request):
    if getattr(request, "method", "") != "GET":
        return False
    path = request.path or ""
    if not any(path.startswith(prefix) for prefix in _CACHE_PREFIXES):
        return False
    lowered = path.lower()
    if any(token in lowered for token in _SKIP_SUBSTRINGS):
        return False
    return True


def _cache_key(request):
    qs = request.META.get("QUERY_STRING") or ""
    return f"httpGET:{request.path}?{qs}"


class PublicGetCacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not _cacheable_request(request):
            return self.get_response(request)

        key = _cache_key(request)
        cached = cache_get(key)
        if cached is not None:
            body, status_code, content_type = cached
            response = HttpResponse(
                body, status=status_code, content_type=content_type
            )
            ttl = 10 if status_code == 404 else DEFAULT_TTL_SECONDS
            response["Cache-Control"] = (
                f"public, max-age={ttl}, stale-while-revalidate=300"
            )
            response["X-Public-Cache"] = "HIT"
            return response

        response = self.get_response(request)
        try:
            status_code = int(getattr(response, "status_code", 0) or 0)
            content_type = str(response.get("Content-Type") or "")
            body = getattr(response, "content", None)
            if (
                status_code in (200, 404)
                and "json" in content_type.lower()
                and isinstance(body, (bytes, bytearray, memoryview))
                and 0 < len(body) <= _MAX_BODY_BYTES
            ):
                ttl = 10 if status_code == 404 else DEFAULT_TTL_SECONDS
                cache_set(key, (bytes(body), status_code, content_type), ttl)
                if not response.get("Cache-Control"):
                    response["Cache-Control"] = (
                        f"public, max-age={ttl}, stale-while-revalidate=300"
                    )
                response["X-Public-Cache"] = "MISS"
        except Exception:
            pass
        return response
