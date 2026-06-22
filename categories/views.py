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


@api_view(['GET'])
@permission_classes([AllowAny])
def category_list(request):
    """List all categories"""
    try:
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
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
            message = title_errors[0] if isinstance(title_errors, list) else str(title_errors)
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
        
        serializer = CategorySerializer(category, data=request.data, partial=True, context={"request": request})
        if serializer.is_valid():
            try:
                serializer.save()
            except NotUniqueError as exc:
                return not_unique_conflict(exc, field="title")
            return Response(serializer.data, status=status.HTTP_200_OK)
        errors = serializer.errors
        title_errors = errors.get("title")
        if title_errors:
            message = title_errors[0] if isinstance(title_errors, list) else str(title_errors)
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
