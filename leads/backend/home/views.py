from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import HeroSection, AboutSection
from categories.models import TestCategory as Category
from django.http import JsonResponse, HttpResponse

# ----------------------------
# CREATE HERO SECTION
# ----------------------------
@csrf_exempt
# def create_hero_section(request):
#     """
#     Admin API: Create a new Hero Section.
#     """
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

#     try:
#         title = request.POST.get("title")
#         subtitle = request.POST.get("subtitle")
#         search_placeholder = request.POST.get("search_placeholder")
#         background_image = request.FILES.get("background_image")

#         if not title:
#             return JsonResponse({"success": False, "message": "Title is required"}, status=400)

#         # Deactivate existing hero sections (only one active at a time)
#         HeroSection.objects.update(is_active=False)

#         hero = HeroSection(
#             title=title,
#             subtitle=subtitle,
#             search_placeholder=search_placeholder,
#             is_active=True,
            
#         )

#         if background_image:
#             hero.background_image.put(background_image, content_type=background_image.content_type)

#         hero.save()
#         return JsonResponse({"success": True, "message": "Hero section created successfully."}, status=201)

#     except Exception as e:
#         return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def create_hero_section(request):
    """
    Admin API: Create or update Hero Section (Cloudinary URL provided from frontend)
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))

        title = data.get("title")
        subtitle = data.get("subtitle")
        search_placeholder = data.get("search_placeholder")
        background_image_url = data.get("background_image_url")

        if not title:
            return JsonResponse({"success": False, "message": "Title is required"}, status=400)

        # deactivate all current hero sections
        HeroSection.objects.update(is_active=False)

        hero = HeroSection(
            title=title,
            subtitle=subtitle,
            search_placeholder=search_placeholder,
            background_image_url=background_image_url,
            is_active=True
        )
        hero.save()

        return JsonResponse({
            "success": True,
            "message": "Hero section created successfully",
            "data": {
                "id": str(hero.id),
                "title": hero.title,
                "subtitle": hero.subtitle,
                "search_placeholder": hero.search_placeholder,
                "background_image_url": hero.background_image_url
            }
        }, status=201)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# @csrf_exempt
# # def get_hero_image(request, hero_id):
# #     """
# #     Serves the background image for a given hero section.
# #     """
# #     try:
# #         hero = HeroSection.objects(id=hero_id).first()
# #         if not hero or not hero.background_image:
# #             return JsonResponse({"success": False, "message": "Image not found"}, status=404)

# #         response = HttpResponse(
# #             hero.background_image.read(),
# #             content_type=hero.background_image.content_type
# #         )
# #         response["Content-Disposition"] = f"inline; filename={hero.background_image.filename}"
# #         return response

# #     except Exception as e:
# #         return JsonResponse({"success": False, "message": str(e)}, status=500)
from django.http import JsonResponse
from .models import HeroSection

def get_active_hero_section(request):
    """
    Public API: Fetch currently active hero section
    """
    try:
        hero = HeroSection.objects(is_active=True).first()
        if not hero:
            return JsonResponse({"success": False, "message": "No active hero section found"}, status=404)

        data = {
            "id": str(hero.id),
            "title": hero.title,
            "subtitle": hero.subtitle,
            "search_placeholder": hero.search_placeholder,
            "background_image_url": hero.background_image_url,
        }
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def get_hero_image(request, hero_id):
    """
    Return the Cloudinary image URL for a given hero section.
    """
    try:
        hero = HeroSection.objects(id=hero_id).first()
        if not hero or not hero.background_image_url:
            return JsonResponse({"success": False, "message": "Image not found"}, status=404)

        return JsonResponse({
            "success": True,
            "background_image_url": hero.background_image_url
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

# ----------------------------
# UPDATE HERO SECTION
# ----------------------------
@csrf_exempt
def update_hero_section(request, hero_id):
    """
    Admin API: Update an existing Hero Section by ID.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        hero = HeroSection.objects(id=hero_id).first()
        if not hero:
            return JsonResponse({"success": False, "message": "Hero section not found"}, status=404)

        # Update fields dynamically if provided
        hero.title = request.POST.get("title", hero.title)
        hero.subtitle = request.POST.get("subtitle", hero.subtitle)
        hero.search_placeholder = request.POST.get("search_placeholder", hero.search_placeholder)

        background_image = request.FILES.get("background_image")
        if background_image:
            hero.background_image.replace(background_image, content_type=background_image.content_type)

        hero.save()
        return JsonResponse({"success": True, "message": "Hero section updated successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def get_hero_section(request):
    """
    Public API: Fetch the active Hero Section content.
    Controlled entirely by the Admin via Admin Panel.
    """
    try:
        hero = HeroSection.objects(is_active=True).first()

        if not hero:
            return JsonResponse(
                {"success": False, "message": "No active hero section found."},
                status=404
            )

        # Build proper image URL (since GridFS FileField has no .url)
        image_url = (
            request.build_absolute_uri(f"/api/home/hero/image/{hero.id}/")
            if hero.background_image
            else None
        )

        data = {
            "id": str(hero.id),
            "title": hero.title,
            "subtitle": hero.subtitle,
            "search_placeholder": hero.search_placeholder,
            "background_image": image_url,
        }

        return JsonResponse({"success": True, "data": data}, status=200)

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error fetching hero section: {str(e)}"},
            status=500
        )



@csrf_exempt
def search_courses(request):
    """
    Public API: Search for courses/categories by name.
    Example: /api/hero/search/?q=python
    """
    try:
        query = request.GET.get("q", "").strip()
        if not query:
            return JsonResponse({"success": True, "results": []}, status=200)

        # Case-insensitive name search
        results = Category.objects(name__icontains=query)

        data = [
            {"id": str(cat.id), "name": cat.name}
            for cat in results
        ]

        return JsonResponse({"success": True, "results": data}, status=200)

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Error searching courses: {str(e)}"},
            status=500
        )


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AnalyticsStat


@csrf_exempt
def create_analytics_stat(request):
    """Admin API: Create a new analytics stat."""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # ✅ Detect JSON or form-data automatically
        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        title = data.get("title")
        value = data.get("value")
        icon = data.get("icon")
        gradient = data.get("gradient")

        if not title or value is None:
            return JsonResponse({"success": False, "message": "Title and value are required."}, status=400)

        # ✅ Support strings, floats, and percentages safely
        if isinstance(value, str):
            value = value.strip()
            if value.endswith("%"):
                try:
                    value = float(value.strip("%"))
                except ValueError:
                    pass
            else:
                try:
                    value = float(value)
                except ValueError:
                    pass

        stat = AnalyticsStat(
            title=title,
            value=value,
            icon=icon or "BarChart2",
            gradient=gradient or "from-blue-500 to-cyan-600",
            is_active=True
        )
        stat.save()

        return JsonResponse({"success": True, "message": "Analytics stat created successfully."}, status=201)

    except Exception as e:
        import traceback
        print("❌ Error in create_analytics_stat:", traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def update_analytics_stat(request, stat_id):
    """Update existing analytics stat."""
    if request.method not in ["PUT", "POST"]:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(stat_id):
            return JsonResponse({"success": False, "message": "Invalid ID"}, status=400)

        stat = AnalyticsStat.objects(id=stat_id).first()
        if not stat:
            return JsonResponse({"success": False, "message": "Stat not found"}, status=404)

        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body.decode("utf-8"))
        else:
            data = request.POST

        title = data.get("title")
        value = data.get("value")
        icon = data.get("icon")
        gradient = data.get("gradient")

        if title:
            stat.title = title
        if value is not None:
            stat.value = value
        if icon:
            stat.icon = icon
        if gradient:
            stat.gradient = gradient

        stat.save()
        return JsonResponse({"success": True, "message": "Analytics stat updated successfully."}, status=200)

    except Exception as e:
        import traceback
        print("❌ Error in update_analytics_stat:", traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def delete_analytics_stat(request, stat_id):
    """Delete analytics stat."""
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(stat_id):
            return JsonResponse({"success": False, "message": "Invalid ID"}, status=400)

        stat = AnalyticsStat.objects(id=stat_id).first()
        if not stat:
            return JsonResponse({"success": False, "message": "Stat not found"}, status=404)

        stat.delete()
        return JsonResponse({"success": True, "message": "Analytics stat deleted successfully."}, status=200)

    except Exception as e:
        import traceback
        print("❌ Error in delete_analytics_stat:", traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def get_analytics_stats(request):
    """Public API: Fetch analytics stats."""
    try:
        stats = AnalyticsStat.objects(is_active=True)
        data = [
            {
                "id": str(s.id),
                "title": s.title,
                "value": s.value,
                "icon": s.icon,
                "gradient": s.gradient,
            }
            for s in stats
        ]
        return JsonResponse({"success": True, "stats": data}, status=200)
    except Exception as e:
        import traceback
        print("❌ Error in get_analytics_stats:", traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Feature

@csrf_exempt
def get_features(request):
    """
    Public API: Fetch active feature cards for homepage (dynamic).
    Controlled by Admin in backend.
    """
    try:
        features = Feature.objects(is_active=True)
        data = [
            {
                "id": str(f.id),
                "title": f.title,
                "description": f.description,
                "icon": f.icon,  # e.g. "BarChart3"
                "gradient": f.gradient,
            }
            for f in features
        ]
        return JsonResponse({"success": True, "features": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# -------------------------------------
# ✅ CREATE FEATURE (Admin)
# -------------------------------------
@csrf_exempt
def create_feature(request):
    """
    Admin API: Create a new feature card
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        data = json.loads(request.body)
        title = data.get("title")
        description = data.get("description")
        icon = data.get("icon")
        gradient = data.get("gradient")

        if not title or not description:
            return JsonResponse({"success": False, "message": "Title and description are required."}, status=400)

        feature = Feature(
            title=title,
            description=description,
            icon=icon or "Star",
            gradient=gradient or "from-blue-500 to-indigo-500",
            is_active=True,
        )
        feature.save()

        return JsonResponse({"success": True, "message": "Feature created successfully.", "id": str(feature.id)}, status=201)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# -------------------------------------
# ✏️ UPDATE FEATURE (Admin)
# -------------------------------------
@csrf_exempt
def update_feature(request, feature_id):
    """
    Admin API: Update a feature card by ID
    """
    if request.method not in ["PUT", "POST"]:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(feature_id):
            return JsonResponse({"success": False, "message": "Invalid Feature ID"}, status=400)

        feature = Feature.objects(id=feature_id).first()
        if not feature:
            return JsonResponse({"success": False, "message": "Feature not found"}, status=404)

        data = json.loads(request.body)

        # Update fields if provided
        feature.title = data.get("title", feature.title)
        feature.description = data.get("description", feature.description)
        feature.icon = data.get("icon", feature.icon)
        feature.gradient = data.get("gradient", feature.gradient)
        feature.is_active = data.get("is_active", feature.is_active)

        feature.save()
        return JsonResponse({"success": True, "message": "Feature updated successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# -------------------------------------
# ❌ DELETE FEATURE (Admin)
# -------------------------------------
@csrf_exempt
def delete_feature(request, feature_id):
    """
    Admin API: Delete a feature card by ID
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        if not ObjectId.is_valid(feature_id):
            return JsonResponse({"success": False, "message": "Invalid Feature ID"}, status=400)

        feature = Feature.objects.get(id=feature_id)
        print("feature", feature)
        if not feature:
            return JsonResponse({"success": False, "message": "Feature not found"}, status=404)

        feature.delete()
        return JsonResponse({"success": True, "message": "Feature deleted successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Testimonial

# @csrf_exempt
# def create_testimonial(request):
#     """
#     Admin API: Create a new testimonial (with image upload).
#     """
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

#     try:
#         name = request.POST.get("name")
#         role = request.POST.get("role")
#         text = request.POST.get("text")
#         rating = request.POST.get("rating")
#         image = request.FILES.get("image")

#         if not all([name, text]):
#             return JsonResponse({"success": False, "message": "Name and text are required."}, status=400)

#         testimonial = Testimonial(
#             name=name,
#             role=role,
#             text=text,
#             rating=float(rating) if rating else 5.0,
#             is_active=True
            
#         )

#         if image:
#             testimonial.image.put(image, content_type=image.content_type)

#         testimonial.save()
#         return JsonResponse({"success": True, "message": "Testimonial created successfully."}, status=201)

#     except Exception as e:
#         return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def create_testimonial(request):
    """
    Admin API: Create a new testimonial (image URL from Cloudinary)
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        from categories.models import TestCategory
        from bson import ObjectId
        
        data = json.loads(request.body)

        name = data.get("name")
        role = data.get("role")
        text = data.get("text")
        rating = data.get("rating", 5)
        image_url = data.get("image_url")
        category_id = data.get("category_id")
        is_featured = data.get("is_featured", False)

        if not all([name, text]):
            return JsonResponse({"success": False, "message": "Name and text are required."}, status=400)

        testimonial = Testimonial(
            name=name,
            role=role,
            text=text,
            rating=float(rating),
            image_url=image_url,
            is_featured=bool(is_featured),
            is_active=True,
        )
        
        # Link category if provided
        if category_id:
            if ObjectId.is_valid(category_id):
                try:
                    category = TestCategory.objects.get(id=ObjectId(category_id))
                    testimonial.category = category
                except TestCategory.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Category not found"}, status=404)
            else:
                return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)
        
        testimonial.save()

        return JsonResponse({"success": True, "message": "Testimonial created successfully."}, status=201)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def update_testimonial(request, testimonial_id):
    """
    Admin API: Update an existing testimonial (supports image upload).
    """
    if request.method not in ["PUT", "POST"]:
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        from categories.models import TestCategory
        
        # ✅ Validate ID
        if not ObjectId.is_valid(testimonial_id):
            return JsonResponse({"success": False, "message": "Invalid testimonial ID"}, status=400)

        testimonial = Testimonial.objects(id=testimonial_id).first()
        if not testimonial:
            return JsonResponse({"success": False, "message": "Testimonial not found"}, status=404)

        # ✅ Handle form-data or JSON
        if request.content_type and "application/json" in request.content_type:
            data = json.loads(request.body.decode("utf-8"))
            name = data.get("name")
            role = data.get("role")
            text = data.get("text")
            rating = data.get("rating")
            category_id = data.get("category_id")
            is_featured = data.get("is_featured")
            image = None  # JSON cannot contain image files
        else:
            name = request.POST.get("name")
            role = request.POST.get("role")
            text = request.POST.get("text")
            rating = request.POST.get("rating")
            category_id = request.POST.get("category_id")
            is_featured = request.POST.get("is_featured")
            image = request.FILES.get("image")

        # ✅ Update only provided fields
        if name:
            testimonial.name = name
        if role is not None:
            testimonial.role = role
        if text:
            testimonial.text = text
        if rating:
            testimonial.rating = float(rating)
        if is_featured is not None:
            testimonial.is_featured = bool(is_featured)
        
        # ✅ Handle category update
        if category_id is not None:
            if category_id == "":
                testimonial.category = None
            elif ObjectId.is_valid(category_id):
                try:
                    category = TestCategory.objects.get(id=ObjectId(category_id))
                    testimonial.category = category
                except TestCategory.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Category not found"}, status=404)
            else:
                return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

        # ✅ Handle image replacement
        if image:
            if testimonial.image:
                testimonial.image.delete()  # remove old image from GridFS
            testimonial.image.put(image, content_type=image.content_type)

        testimonial.save()
        return JsonResponse({"success": True, "message": "Testimonial updated successfully."}, status=200)

    except Exception as e:
        import traceback
        print("❌ Error in update_testimonial:", traceback.format_exc())
        return JsonResponse({"success": False, "message": str(e)}, status=500)



from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Testimonial


@csrf_exempt
def get_top_testimonials(request):
    """
    Public API: Fetch all testimonials for home page.
    Returns all active testimonials (admin-created) and reviews marked as testimonials.
    Deduplicates based on text content to avoid showing same testimonials.
    """
    try:
        from reviews.models import Review

        data = []
        seen_texts = set()  # Track seen testimonial text to avoid duplicates
        
        # Get ALL active testimonials from Testimonial model (admin-created testimonials)
        testimonials = Testimonial.objects(is_active=True).order_by("-rating", "-created_at")
        for t in testimonials:
            # Check if we've already seen this testimonial text
            testimonial_text = t.text.strip().lower()
            if testimonial_text in seen_texts:
                continue  # Skip duplicate
            seen_texts.add(testimonial_text)
            
            testimonial_data = {
                "id": str(t.id),
                "name": t.name,
                "role": t.role,
                "text": t.text,
                "rating": t.rating,
                "image_url": t.image_url if t.image_url else None,
            }
            try:
                if t.category:
                    testimonial_data["category"] = {
                        "id": str(t.category.id),
                        "name": getattr(t.category, "name", "Unknown Category")
                    }
            except Exception as e:
                print(f"Error accessing category for testimonial {t.id}: {e}")
                pass
            data.append(testimonial_data)
        
        # Also include reviews marked as testimonials
        review_testimonials = Review.objects(is_approved=True, is_active=True, is_testimonial=True).order_by("-rating", "-created_at")
        for review in review_testimonials:
            # Check if we've already seen this review text
            review_text = review.comment.strip().lower()
            if review_text in seen_texts:
                continue  # Skip duplicate
            seen_texts.add(review_text)
            
            try:
                user_name = review.user.fullname if hasattr(review.user, 'fullname') else (
                    review.user.email if hasattr(review.user, 'email') else "Anonymous"
                )
            except:
                user_name = "Anonymous"
            
            review_data = {
                "id": f"review_{review.id}",
                "name": user_name,
                "role": "Student",
                "text": review.comment,
                "rating": review.rating,
                "image_url": None,
            }
            try:
                if review.category:
                    review_data["category"] = {
                        "id": str(review.category.id),
                        "name": review.category.name
                    }
            except Exception as e:
                print(f"Error accessing category for review {review.id}: {e}")
                pass
            data.append(review_data)

        return JsonResponse({"success": True, "testimonials": data}, status=200)

    except Exception as e:
        import traceback
        print(f"Error in get_top_testimonials: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def get_testimonial_image(request, testimonial_id):
    """
    Return the Cloudinary image URL for a testimonial.
    """
    try:
        testimonial = Testimonial.objects(id=testimonial_id).first()
        if not testimonial:
            return JsonResponse(
                {"success": False, "message": "Testimonial not found"},
                status=404,
            )

        # If image field stores the Cloudinary URL
        if testimonial.image:
            return JsonResponse(
                {
                    "success": True,
                    "image_url": testimonial.image  # Cloudinary URL
                },
                status=200,
            )
        else:
            return JsonResponse(
                {"success": False, "message": "No image found"},
                status=404,
            )

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


from django.http import HttpResponse

@csrf_exempt
def get_testimonials(request):
    """
    Public API: Fetch active testimonials dynamically managed by Admin.
    Returns testimonials from Testimonial model AND reviews marked as testimonials.
    Query params: category_id (optional) - filter by category
    """
    try:
        from categories.models import TestCategory
        from reviews.models import Review
        from bson import ObjectId
        
        category_id = request.GET.get("category_id")
        category = None
        
        # Get category if provided
        if category_id:
            if ObjectId.is_valid(category_id):
                try:
                    category = TestCategory.objects.get(id=ObjectId(category_id))
                except TestCategory.DoesNotExist:
                    return JsonResponse({"success": False, "message": "Category not found"}, status=404)
            else:
                return JsonResponse({"success": False, "message": "Invalid category ID"}, status=400)

        data = []
        
        # Get testimonials from Testimonial model
        testimonials_query = Testimonial.objects(is_active=True)
        if category:
            testimonials_query = testimonials_query.filter(category=category)
        
        for t in testimonials_query:
            testimonial_data = {
                "id": str(t.id),
                "name": t.name,
                "role": t.role,
                "text": t.text,
                "rating": t.rating,
                "image_url": t.image_url if t.image_url else None,
            }
            try:
                if t.category:
                    testimonial_data["category"] = {
                        "id": str(t.category.id),
                        "name": getattr(t.category, "name", "Unknown Category")
                    }
            except Exception as e:
                print(f"Error accessing category for testimonial {t.id}: {e}")
                pass
            data.append(testimonial_data)
        
        # Get reviews marked as testimonials
        reviews_query = Review.objects(is_approved=True, is_active=True, is_testimonial=True)
        if category:
            reviews_query = reviews_query.filter(category=category)
        
        for review in reviews_query:
            try:
                user_name = review.user.fullname if hasattr(review.user, 'fullname') else (
                    review.user.email if hasattr(review.user, 'email') else "Anonymous"
                )
            except:
                user_name = "Anonymous"
            
            review_data = {
                "id": f"review_{review.id}",
                "name": user_name,
                "role": "Student",
                "text": review.comment,
                "rating": review.rating,
                "image_url": None,
            }
            try:
                if review.category:
                    review_data["category"] = {
                        "id": str(review.category.id),
                        "name": review.category.name
                    }
            except Exception as e:
                print(f"Error accessing category for review {review.id}: {e}")
                pass
            data.append(review_data)

        return JsonResponse({"success": True, "testimonials": data}, status=200)

    except Exception as e:
        import traceback
        print(f"Error in get_testimonials: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)



from bson import ObjectId

@csrf_exempt
def delete_testimonial(request, testimonial_id):
    """
    Admin API: Delete a testimonial by ID.
    Method: DELETE
    URL: /api/home/testimonials/delete/<testimonial_id>/
    """
    if request.method != "DELETE":
        return JsonResponse(
            {"success": False, "message": "Method Not Allowed"},
            status=405
        )

    try:
        # ✅ Validate ObjectId format
        if not ObjectId.is_valid(testimonial_id):
            return JsonResponse(
                {"success": False, "message": "Invalid testimonial ID"},
                status=400
            )

        # ✅ Check if testimonial exists
        testimonial = Testimonial.objects(id=ObjectId(testimonial_id)).first()
        if not testimonial:
            return JsonResponse(
                {"success": False, "message": "Testimonial not found"},
                status=404
            )

        # ✅ Delete image (if stored)
        if getattr(testimonial, "image", None):
            try:
                testimonial.image.delete()
            except Exception:
                pass  # safely ignore if image not in GridFS

        # ✅ Delete testimonial document
        testimonial.delete()

        return JsonResponse(
            {"success": True, "message": "Testimonial deleted successfully."},
            status=200
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": str(e)},
            status=500
        )



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mongoengine.errors import DoesNotExist, ValidationError
from .models import FAQ
import json
import datetime


# --------------------------------------
# Get All FAQs (Public Endpoint)
# --------------------------------------
def get_faqs(request):
    """
    Public endpoint: fetch all FAQs
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        faqs = FAQ.objects.order_by('-created_at')
        data = [
            {
                "id": str(faq.id),
                "question": faq.question,
                "answer": faq.answer,
                "created_at": faq.created_at,
                "updated_at": faq.updated_at,
            }
            for faq in faqs
        ]
        return JsonResponse({"success": True, "faqs": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# --------------------------------------
# Admin: Create a new FAQ
# --------------------------------------
@csrf_exempt
def create_faq(request):
    """
    Admin endpoint: create a new FAQ
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        data = json.loads(request.body)
        question = data.get("question")
        answer = data.get("answer")

        if not question or not answer:
            return JsonResponse({"success": False, "message": "Question and answer are required."}, status=400)

        faq = FAQ(question=question, answer=answer)
        faq.save()

        return JsonResponse({"success": True, "message": "FAQ created successfully.", "id": str(faq.id)}, status=201)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# --------------------------------------
# Admin: Update an FAQ
# --------------------------------------
@csrf_exempt
def update_faq(request, faq_id):
    """
    Admin endpoint: update an existing FAQ
    """
    if request.method != "PUT":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        data = json.loads(request.body)
        faq = FAQ.objects.get(id=faq_id)

        faq.question = data.get("question", faq.question)
        faq.answer = data.get("answer", faq.answer)
        faq.updated_at = datetime.datetime.utcnow()
        faq.save()

        return JsonResponse({"success": True, "message": "FAQ updated successfully."}, status=200)

    except DoesNotExist:
        return JsonResponse({"success": False, "message": "FAQ not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# --------------------------------------
# Admin: Delete an FAQ
# --------------------------------------
@csrf_exempt
def delete_faq(request, faq_id):
    """
    Admin endpoint: delete an FAQ
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method Not Allowed"}, status=405)

    try:
        faq = FAQ.objects.get(id=faq_id)
        faq.delete()
        return JsonResponse({"success": True, "message": "FAQ deleted successfully."}, status=200)

    except DoesNotExist:
        return JsonResponse({"success": False, "message": "FAQ not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


from django.http import JsonResponse
from .models import CTASection
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def get_cta_section(request):
    """
    Public API — Fetch CTA section content dynamically
    """
    try:
        cta = CTASection.objects(is_active=True).first()
        if not cta:
            return JsonResponse({"success": False, "message": "No active CTA section found."}, status=404)

        data = {
            "title": cta.title,
            "subtitle": cta.subtitle,
            "description": cta.description,
            "primary_button_text": cta.primary_button_text,
            "primary_button_link": cta.primary_button_link,
            "secondary_button_text": cta.secondary_button_text,
            "secondary_button_link": cta.secondary_button_link,
        }
        return JsonResponse({"success": True, "cta": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mongoengine.errors import ValidationError, DoesNotExist
from .models import CTASection

@csrf_exempt
def create_cta_section(request):
    """
    Admin API: Create or update a CTA section.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        heading = request.POST.get("heading")
        subheading = request.POST.get("subheading")
        button_text_primary = request.POST.get("button_text_primary")
        button_link_primary = request.POST.get("button_link_primary")
        button_text_secondary = request.POST.get("button_text_secondary")
        button_link_secondary = request.POST.get("button_link_secondary")
        footer_note = request.POST.get("footer_note")
        background_image = request.FILES.get("background_image")

        if not heading:
            return JsonResponse({"success": False, "message": "Heading is required"}, status=400)

        # Deactivate previous active CTA sections
        CTASection.objects.update(is_active=False)

        # Create new section
        cta = CTASection(
            heading=heading,
            subheading=subheading,
            button_text_primary=button_text_primary,
            button_link_primary=button_link_primary,
            button_text_secondary=button_text_secondary,
            button_link_secondary=button_link_secondary,
            footer_note=footer_note,
            is_active=True
        )

        if background_image:
            cta.background_image.put(background_image, content_type=background_image.content_type)

        cta.save()
        return JsonResponse({"success": True, "message": "CTA section created successfully."}, status=201)

    except ValidationError as e:
        return JsonResponse({"success": False, "message": str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def get_active_cta_section(request):
    """
    Public API: Fetch the currently active CTA section.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        cta = CTASection.objects(is_active=True).order_by('-created_at').first()
        if not cta:
            return JsonResponse({"success": False, "message": "No active CTA section found."}, status=404)

        data = {
            "heading": cta.heading,
            "subheading": cta.subheading,
            "button_text_primary": cta.button_text_primary,
            "button_link_primary": cta.button_link_primary,
            "button_text_secondary": cta.button_text_secondary,
            "button_link_secondary": cta.button_link_secondary,
            "footer_note": cta.footer_note,
            "background_image": cta.background_image.url if cta.background_image else None,
        }

        return JsonResponse({"success": True, "data": data}, status=200)

    except DoesNotExist:
        return JsonResponse({"success": False, "message": "CTA section not found."}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from bson import ObjectId
from .models import CTASection


@csrf_exempt
def update_cta_section(request, cta_id):
    """
    Admin API: Update an existing CTA section by ID.
    """
    if request.method != "PUT" and request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Validate CTA ID
        if not ObjectId.is_valid(cta_id):
            return JsonResponse({"success": False, "message": "Invalid CTA ID"}, status=400)

        cta = CTASection.objects(id=cta_id).first()
        if not cta:
            return JsonResponse({"success": False, "message": "CTA section not found"}, status=404)

        # Get form data
        heading = request.POST.get("heading")
        subheading = request.POST.get("subheading")
        button_text_primary = request.POST.get("button_text_primary")
        button_link_primary = request.POST.get("button_link_primary")
        button_text_secondary = request.POST.get("button_text_secondary")
        button_link_secondary = request.POST.get("button_link_secondary")
        footer_note = request.POST.get("footer_note")
        background_image = request.FILES.get("background_image")

        # Update fields if provided
        if heading is not None:
            cta.heading = heading
        if subheading is not None:
            cta.subheading = subheading
        if button_text_primary is not None:
            cta.button_text_primary = button_text_primary
        if button_link_primary is not None:
            cta.button_link_primary = button_link_primary
        if button_text_secondary is not None:
            cta.button_text_secondary = button_text_secondary
        if button_link_secondary is not None:
            cta.button_link_secondary = button_link_secondary
        if footer_note is not None:
            cta.footer_note = footer_note

        if background_image:
            # Delete old image first if exists
            if cta.background_image:
                cta.background_image.delete()
            cta.background_image.put(background_image, content_type=background_image.content_type)

        cta.save()
        return JsonResponse({"success": True, "message": "CTA section updated successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def delete_cta_section(request, cta_id):
    """
    Admin API: Delete a CTA section by ID.
    """
    if request.method != "DELETE":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        # Validate CTA ID
        if not ObjectId.is_valid(cta_id):
            return JsonResponse({"success": False, "message": "Invalid CTA ID"}, status=400)

        cta = CTASection.objects(id=cta_id).first()
        if not cta:
            return JsonResponse({"success": False, "message": "CTA section not found"}, status=404)

        # Delete background image if present
        if cta.background_image:
            cta.background_image.delete()

        # Delete the document
        cta.delete()
        return JsonResponse({"success": True, "message": "CTA section deleted successfully."}, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


# ----------------------------
# ABOUT SECTION
# ----------------------------
@csrf_exempt
def get_about_section(request):
    """
    Public API: Get active about section content
    """
    try:
        about = AboutSection.objects(is_active=True).first()
        if not about:
            # Return default content if no active section
            about = AboutSection()
        
        data = {
            "id": str(about.id) if about.id else None,
            "hero_title": about.hero_title,
            "hero_subtitle": about.hero_subtitle,
            "mission_title": about.mission_title,
            "mission_description": about.mission_description,
            "vision_title": about.vision_title,
            "vision_description": about.vision_description,
            "stats": about.stats,
            "values_title": about.values_title,
            "values_subtitle": about.values_subtitle,
            "values": about.values,
            "story_title": about.story_title,
            "story_paragraphs": about.story_paragraphs,
            "story_image_url": about.story_image_url,
            "quote_text": about.quote_text,
            "quote_author": about.quote_author,
        }
        return JsonResponse({"success": True, "data": data}, status=200)
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
def create_or_update_about_section(request):
    """
    Admin API: Create or update about section
    """
    if request.method not in ["POST", "PUT"]:
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        import json
        import datetime
        data = json.loads(request.body) if request.body else {}
        
        # Deactivate previous active sections
        AboutSection.objects.update(is_active=False)
        
        # Get or create about section
        about_id = data.get("id")
        if about_id:
            about = AboutSection.objects(id=about_id).first()
            if not about:
                about = AboutSection()
        else:
            about = AboutSection()
        
        # Update fields
        about.hero_title = data.get("hero_title", about.hero_title)
        about.hero_subtitle = data.get("hero_subtitle", about.hero_subtitle)
        about.mission_title = data.get("mission_title", about.mission_title)
        about.mission_description = data.get("mission_description", about.mission_description)
        about.vision_title = data.get("vision_title", about.vision_title)
        about.vision_description = data.get("vision_description", about.vision_description)
        about.stats = data.get("stats", about.stats)
        about.values_title = data.get("values_title", about.values_title)
        about.values_subtitle = data.get("values_subtitle", about.values_subtitle)
        about.values = data.get("values", about.values)
        about.story_title = data.get("story_title", about.story_title)
        about.story_paragraphs = data.get("story_paragraphs", about.story_paragraphs)
        about.story_image_url = data.get("story_image_url", about.story_image_url)
        about.quote_text = data.get("quote_text", about.quote_text)
        about.quote_author = data.get("quote_author", about.quote_author)
        about.is_active = True
        about.updated_at = datetime.datetime.utcnow()
        
        about.save()
        
        return JsonResponse({
            "success": True,
            "message": "About section saved successfully",
            "id": str(about.id)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)


