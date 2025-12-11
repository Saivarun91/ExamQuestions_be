from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Provider
from .serializers import ProviderSerializer
from bson import ObjectId
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from common.middleware import authenticate, restrict

# ✅ List all active providers (Public)
@api_view(['GET'])
@permission_classes([AllowAny])
@csrf_exempt
def provider_list(request):
    providers = Provider.objects(is_active=True).order_by('order')
    serializer = ProviderSerializer(providers, many=True, context={'request': request})
    return Response(serializer.data)


# ✅ Create provider
@api_view(['POST'])
@permission_classes([AllowAny])
def provider_create(request):
    serializer = ProviderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)


# ✅ Get single provider by slug
@api_view(['GET'])
@permission_classes([AllowAny])
def provider_detail(request, provider_slug):
    provider = Provider.objects(slug=provider_slug).first()
    if not provider:
        return Response({'error': 'Provider not found'}, status=404)
    serializer = ProviderSerializer(provider, context={'request': request})
    return Response(serializer.data)


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
        providers = Provider.objects.all().order_by('order')
        serializer = ProviderSerializer(providers, many=True, context={'request': request})
        return Response({"success": True, "data": serializer.data})
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
        # Check if request is multipart/form-data (file upload) or JSON
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        
        if is_multipart:
            # Handle multipart/form-data (with file uploads)
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
        else:
            # Handle JSON request
            data = request.data
        
        # Validate required fields
        if not data.get('name') or not data.get('icon'):
            return Response(
                {"error": "Name and icon are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert order to int if it's a string
        order = data.get('order', 0)
        if isinstance(order, str):
            try:
                order = int(order)
            except (ValueError, TypeError):
                order = 0
        
        # Convert is_active to boolean if it's a string
        is_active = data.get('is_active', True)
        if isinstance(is_active, str):
            is_active = is_active.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(is_active, (int, float)):
            is_active = bool(is_active)
        
        # Create provider
        provider = Provider(
            name=data['name'],
            icon=data['icon'],
            slug=data.get('slug', ''),  # Will auto-generate if empty
            meta_title=data.get('meta_title', ''),
            meta_keywords=data.get('meta_keywords', ''),
            meta_description=data.get('meta_description', ''),
            order=order,
            is_active=is_active
        )
        
        # Handle logo file upload
        logo_file = request.FILES.get('logo')
        if logo_file:
            provider.logo.put(logo_file, content_type=logo_file.content_type)
        
        provider.save()
        
        serializer = ProviderSerializer(provider, context={'request': request})
        return Response(
            {"success": True, "message": "Provider created successfully", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
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
        
        # Check if request is multipart/form-data (file upload) or JSON
        is_multipart = request.content_type and 'multipart/form-data' in request.content_type
        
        if is_multipart:
            # Handle multipart/form-data (with file uploads)
            data = {}
            for key in request.POST:
                data[key] = request.POST[key]
        else:
            # Handle JSON request
            data = request.data
        
        # Update fields only if provided
        if 'name' in data:
            provider.name = data['name']
        if 'icon' in data:
            provider.icon = data['icon']
        if 'slug' in data:
            provider.slug = data['slug']
        if 'meta_title' in data:
            provider.meta_title = data['meta_title']
        if 'meta_keywords' in data:
            provider.meta_keywords = data['meta_keywords']
        if 'meta_description' in data:
            provider.meta_description = data['meta_description']
        
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
            is_active = data['is_active']
            if isinstance(is_active, str):
                is_active = is_active.lower() in ('true', '1', 'yes', 'on')
            elif isinstance(is_active, (int, float)):
                is_active = bool(is_active)
            provider.is_active = is_active
        
        # Handle logo removal
        remove_logo = data.get('remove_logo', '').lower() in ('true', '1', 'yes', 'on')
        if remove_logo:
            if provider.logo:
                provider.logo.delete()
            provider.logo = None
        
        # Handle logo file upload (only if not removing)
        if not remove_logo:
            logo_file = request.FILES.get('logo')
            if logo_file:
                # Delete old logo if exists
                if provider.logo:
                    provider.logo.delete()
                provider.logo.put(logo_file, content_type=logo_file.content_type)
        
        provider.save()
        
        serializer = ProviderSerializer(provider, context={'request': request})
        return Response({"success": True, "message": "Provider updated successfully", "data": serializer.data})
    except Provider.DoesNotExist:
        return Response({"error": "Provider not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
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
