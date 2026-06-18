from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from bson import ObjectId
from datetime import datetime
from .models import EmailTemplate
from .serializers import EmailTemplateSerializer
from .utils import template_has_uploaded_file, validate_template_upload_file
from common.middleware import authenticate


def _parse_bool(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def _extract_template_data(request):
    """Parse JSON or multipart form data for template create/update."""
    is_multipart = request.content_type and "multipart/form-data" in request.content_type
    data = {}
    if is_multipart:
        for key in request.data:
            data[key] = request.data.get(key)
    else:
        data = dict(request.data) if hasattr(request.data, "items") else request.data.copy()

    filtered = {
        "name": (data.get("name") or "").strip(),
        "subject": (data.get("subject") or "").strip(),
        "body": data.get("body") or "",
        "description": data.get("description") or "",
        "extra_fields": data.get("extra_fields") or "",
        "is_active": _parse_bool(data.get("is_active"), default=True),
    }
    remove_file = _parse_bool(data.get("remove_template_file"), default=False)
    template_file = request.FILES.get("template_file") if is_multipart else None
    return filtered, template_file, remove_file


def _validate_template_file(template_file):
    return validate_template_upload_file(template_file)


def _save_template_file(template, template_file):
    if getattr(template, "template_file", None):
        try:
            template.template_file.delete()
        except Exception:
            pass
    content_type = getattr(template_file, "content_type", None) or "application/octet-stream"
    template.template_file.put(template_file, content_type=content_type)


def _serialize_template(template, request=None):
    serializer = EmailTemplateSerializer(template, context={"has_template_file": template_has_uploaded_file(template)})
    return serializer.data


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
        return Response(_serialize_template(template, request), status=status.HTTP_200_OK)
    except EmailTemplate.DoesNotExist:
        return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ Create a new email template
@api_view(['POST'])
@authenticate
def template_create(request):
    try:
        filtered_data, template_file, _remove_file = _extract_template_data(request)

        file_error = _validate_template_file(template_file)
        if file_error:
            return Response({"error": file_error}, status=status.HTTP_400_BAD_REQUEST)

        if EmailTemplate.objects(name=filtered_data.get("name")).first():
            return Response({"error": "Template with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = EmailTemplateSerializer(
            data=filtered_data,
            context={
                "incoming_template_file": bool(template_file),
                "has_template_file": False,
            },
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        template = serializer.save()
        if template_file:
            _save_template_file(template, template_file)
            template.updated_at = datetime.utcnow()
            template.save()

        return Response(_serialize_template(template, request), status=status.HTTP_201_CREATED)
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
        filtered_data, template_file, remove_file = _extract_template_data(request)

        file_error = _validate_template_file(template_file)
        if file_error:
            return Response({"error": file_error}, status=status.HTTP_400_BAD_REQUEST)

        if "name" in filtered_data and filtered_data["name"] != template.name:
            if EmailTemplate.objects(name=filtered_data["name"]).first():
                return Response({"error": "Template with this name already exists"}, status=status.HTTP_400_BAD_REQUEST)

        has_existing_file = template_has_uploaded_file(template)
        will_have_file = has_existing_file
        if remove_file:
            will_have_file = False
        if template_file:
            will_have_file = True

        serializer = EmailTemplateSerializer(
            template,
            data=filtered_data,
            partial=True,
            context={
                "incoming_template_file": bool(template_file),
                "has_template_file": will_have_file,
            },
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        template = serializer.save()
        template.updated_at = datetime.utcnow()

        if remove_file and getattr(template, "template_file", None):
            try:
                template.template_file.delete()
            except Exception:
                pass

        if template_file:
            _save_template_file(template, template_file)

        template.save()
        return Response(_serialize_template(template, request), status=status.HTTP_200_OK)
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
        if getattr(template, "template_file", None):
            try:
                template.template_file.delete()
            except Exception:
                pass
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

        for template in EmailTemplate.objects(id__in=valid_ids):
            if getattr(template, "template_file", None):
                try:
                    template.template_file.delete()
                except Exception:
                    pass

        deleted_count = EmailTemplate.objects(id__in=valid_ids).delete()
        return Response({
            "message": f"Successfully deleted {deleted_count} template(s)",
            "deleted_count": deleted_count
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
