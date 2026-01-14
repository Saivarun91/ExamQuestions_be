from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Provider

# -----------------------------
# Homepage view
# -----------------------------
def home(request):
    providers = Provider.objects(is_active=True).order_by("name")
    context = {"providers": providers}
    return render(request, "home.html", context)


# -----------------------------
# List all active providers (GET)
# -----------------------------
def providers_list(request):
    providers = Provider.objects(is_active=True).order_by("name")
    data = [p.to_json() for p in providers]
    return JsonResponse(data, safe=False)


# -----------------------------
# Create a new provider (POST)
# -----------------------------
@csrf_exempt
def provider_create(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            provider = Provider(
                name=body.get("name"),
                slug=body.get("slug"),
                is_active=body.get("is_active", True),
                meta_title=body.get("meta_title"),
                meta_keywords=body.get("meta_keywords"),
                meta_description=body.get("meta_description")
            )
            provider.save()
            return JsonResponse(provider.to_json(), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


# -----------------------------
# Update provider (PUT)
# -----------------------------
@csrf_exempt
def provider_update(request, provider_id):
    if request.method == "PUT":
        provider = Provider.objects(id=provider_id).first()
        if not provider:
            return JsonResponse({"error": "Provider not found"}, status=404)
        try:
            body = json.loads(request.body)
            provider.name = body.get("name", provider.name)
            provider.slug = body.get("slug", provider.slug)
            provider.is_active = body.get("is_active", provider.is_active)
            provider.meta_title = body.get("meta_title", provider.meta_title)
            provider.meta_keywords = body.get("meta_keywords", provider.meta_keywords)
            provider.meta_description = body.get("meta_description", provider.meta_description)
            provider.save()
            return JsonResponse(provider.to_json(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


# -----------------------------
# Delete provider (DELETE)
# -----------------------------
@csrf_exempt
def provider_delete(request, provider_id):
    if request.method == "DELETE":
        provider = Provider.objects(id=provider_id).first()
        if not provider:
            return JsonResponse({"error": "Provider not found"}, status=404)
        provider.delete()
        return JsonResponse({"message": "Provider deleted successfully", "id": str(provider.id)}, status=200)
    return JsonResponse({"error": "Invalid HTTP method"}, status=405)


# ---------------------------------
# Exams by provider (SEO-friendly)
# ---------------------------------
def exams_by_provider(request, provider_slug, keyword_slug=None):
    """
    Show exams for a specific provider.
    Optional keyword for filtering.
    """
    provider = Provider.objects(slug=provider_slug, is_active=True).first()
    if not provider:
        return render(request, "404.html", status=404)

    context = {
        "provider": provider,
        "keyword": keyword_slug
    }
    return render(request, "exams.html", context)


# ---------------------------------
# Search exams across all providers (SEO-friendly)
# ---------------------------------
def search_exams(request, keyword_slug):
    """
    Search exams across all providers using a keyword
    """
    keyword = keyword_slug
    # In a real app, you would filter exams collection by keyword
    context = {
        "keyword": keyword
    }
    return render(request, "search.html", context)
