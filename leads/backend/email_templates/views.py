from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from bson import ObjectId
from .models import EmailTemplate
from .serializers import EmailTemplateSerializer
from common.middleware import authenticate

# ✅ List all email templates
@api_view(['GET'])
@permission_classes([AllowAny])
def template_list(request):
    try:
        templates = EmailTemplate.objects.all().order_by('-created_at')
        serializer = EmailTemplateSerializer(templates, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Get a single email template by ID
@api_view(['GET'])
@permission_classes([AllowAny])
def template_detail(request, template_id):
    try:
        if not ObjectId.is_valid(template_id):
            return Response({"error": "Invalid template ID format"}, status=status.HTTP_400_BAD_REQUEST)
        
        template = EmailTemplate.objects.get(id=ObjectId(template_id))
        serializer = EmailTemplateSerializer(template)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except EmailTemplate.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Create a new email template
@api_view(['POST'])
@authenticate
def template_create(request):
    try:
        data = request.data.copy()
        allowed_fields = ["name", "subject", "body", "description", "is_active"]
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # Check if template with same name already exists
        if EmailTemplate.objects(name=filtered_data.get("name")).first():
            return Response({"error": "Template with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EmailTemplateSerializer(data=filtered_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Update an existing email template
@api_view(['PUT', 'PATCH'])
@authenticate
def template_update(request, template_id):
    try:
        if not ObjectId.is_valid(template_id):
            return Response({"error": "Invalid template ID format"}, status=status.HTTP_400_BAD_REQUEST)
        
        template = EmailTemplate.objects.get(id=ObjectId(template_id))
        data = request.data.copy()
        allowed_fields = ["name", "subject", "body", "description", "is_active"]
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        # Check if name is being changed and if new name already exists
        if "name" in filtered_data and filtered_data["name"] != template.name:
            if EmailTemplate.objects(name=filtered_data["name"]).first():
                return Response({"error": "Template with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = EmailTemplateSerializer(template, data=filtered_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except EmailTemplate.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Delete an email template
@api_view(['DELETE'])
@authenticate
def template_delete(request, template_id):
    try:
        if not ObjectId.is_valid(template_id):
            return Response({"error": "Invalid template ID format"}, status=status.HTTP_400_BAD_REQUEST)
        
        template = EmailTemplate.objects.get(id=ObjectId(template_id))
        template.delete()
        return Response({"message": "Template deleted successfully"}, status=status.HTTP_200_OK)
    except EmailTemplate.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Bulk delete email templates
@api_view(['POST'])
@authenticate
def template_bulk_delete(request):
    try:
        template_ids = request.data.get("ids", [])
        if not template_ids or not isinstance(template_ids, list):
            return Response({"error": "Invalid IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        valid_ids = [ObjectId(tid) for tid in template_ids if ObjectId.is_valid(tid)]
        if not valid_ids:
            return Response({"error": "No valid template IDs provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        deleted_count = EmailTemplate.objects(id__in=valid_ids).delete()
        return Response({
            "message": f"Successfully deleted {deleted_count} template(s)",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

