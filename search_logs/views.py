from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import SearchLog
from users.models import User
from users.authentication import authenticate
from common.middleware import restrict
from bson import ObjectId
from datetime import datetime

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def log_search(request):
    """Log a search query"""
    try:
        data = request.data if hasattr(request, 'data') else {}
        if not data:
            import json
            data = json.loads(request.body.decode('utf-8'))
        
        query = data.get('query', '').strip()
        if not query:
            return Response({"success": False, "message": "Query is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user if authenticated
        user = None
        user_id = None
        if hasattr(request, 'user') and isinstance(request.user, dict):
            user_id = request.user.get('id')
            if user_id and ObjectId.is_valid(user_id):
                try:
                    user = User.objects.get(id=ObjectId(user_id))
                except User.DoesNotExist:
                    pass
        
        # Get IP address and user agent
        ip_address = request.META.get('REMOTE_ADDR', '')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Create search log
        search_log = SearchLog(
            query=query,
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.utcnow()
        )
        search_log.save()
        
        return Response({"success": True, "message": "Search logged"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@csrf_exempt
@authenticate
@restrict(['admin'])
def get_search_logs(request):
    """Get all search logs (admin only)"""
    if request.method != 'GET':
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)
    
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 50))
        search_query = request.GET.get('search', '').strip()
        
        # Query search logs
        logs_query = SearchLog.objects.all()
        
        # Filter by search query if provided
        if search_query:
            logs_query = logs_query.filter(query__icontains=search_query)
        
        # Order by created_at descending
        logs_query = logs_query.order_by('-created_at')
        
        # Get total count before pagination
        total_count = logs_query.count()
        
        # Calculate pagination
        skip = (page - 1) * limit
        total_pages = (total_count + limit - 1) // limit if total_count > 0 else 1
        
        # Apply pagination
        logs_list = logs_query.skip(skip).limit(limit)
        
        # Serialize logs
        logs_data = []
        for log in logs_list:
            log_dict = {
                "id": str(log.id),
                "query": log.query,
                "user": None,
                "user_name": None,
                "ip_address": log.ip_address or "",
                "user_agent": log.user_agent or "",
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            
            if log.user:
                try:
                    log_dict["user"] = str(log.user.id)
                    log_dict["user_name"] = log.user.fullname or log.user.email or "Unknown"
                except:
                    pass
            
            logs_data.append(log_dict)
        
        return JsonResponse({
            "success": True,
            "logs": logs_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total_count,
                "pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        }, status=200)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "message": str(e)}, status=500)

