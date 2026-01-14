import json
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from bson import ObjectId
from .models import Notification
from users.models import User
from common.middleware import authenticate


@csrf_exempt
@authenticate
def get_notifications(request):
    """
    Get all notifications for the logged-in user.
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        # Get query parameters
        unread_only = request.GET.get("unread_only", "false").lower() == "true"
        limit = int(request.GET.get("limit", 50))

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        # Build query - get all notifications for the user
        query = {"user": user}
        if unread_only:
            query["is_read"] = False

        # Get notifications ordered by created_at (newest first)
        notifications = Notification.objects(**query).order_by('-created_at').limit(limit)

        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                "id": str(notification.id),
                "type": notification.type,
                "title": notification.title,
                "message": notification.message,
                "is_read": notification.is_read,
                "read_at": str(notification.read_at) if notification.read_at else None,
                "link": notification.link or None,
                "metadata": json.loads(notification.metadata) if notification.metadata else None,
                "created_at": str(notification.created_at),
            })

        unread_count = Notification.objects(user=user, is_read=False).count()

        return JsonResponse({
            "success": True,
            "notifications": notifications_data,
            "unread_count": unread_count,
            "total": len(notifications_data)
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in get_notifications: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def mark_notification_read(request, notification_id):
    """
    Mark a notification as read.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        if not ObjectId.is_valid(notification_id):
            return JsonResponse({"success": False, "message": "Invalid notification ID"}, status=400)

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        notification = Notification.objects.get(pk=ObjectId(notification_id), user=user)
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        notification.save()

        return JsonResponse({
            "success": True,
            "message": "Notification marked as read"
        }, status=200)

    except Notification.DoesNotExist:
        return JsonResponse({"success": False, "message": "Notification not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in mark_notification_read: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


@csrf_exempt
@authenticate
def mark_all_read(request):
    """
    Mark all notifications as read for the logged-in user.
    """
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        Notification.objects(user=user, is_read=False).update(
            is_read=True,
            read_at=datetime.utcnow()
        )

        return JsonResponse({
            "success": True,
            "message": "All notifications marked as read"
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in mark_all_read: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)


def create_notification(user, notification_type, title, message, link=None, metadata=None):
    """
    Helper function to create a notification.
    """
    try:
        metadata_str = json.dumps(metadata) if metadata else None
        notification = Notification(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            link=link,
            metadata=metadata_str,
            is_read=False
        )
        notification.save()
        return notification
    except Exception as e:
        print(f"Error creating notification: {e}")
        import traceback
        traceback.print_exc()
        return None


@csrf_exempt
@authenticate
def check_coupon_expirations(request):
    """
    Check for expiring/expired coupons and create notifications.
    This should be called periodically (e.g., daily cron job or on user login).
    """
    if request.method != "GET":
        return JsonResponse({"success": False, "message": "Method not allowed"}, status=405)

    try:
        user_id = request.user.get("id")
        if not user_id:
            return JsonResponse({"success": False, "message": "User not authenticated"}, status=401)

        # Get user
        if ObjectId.is_valid(user_id):
            user = User.objects.get(id=ObjectId(user_id))
        else:
            user = User.objects.get(id=user_id)

        from reviews.models import Coupon
        from datetime import timedelta
        
        now = datetime.utcnow()
        three_days_later = now + timedelta(days=3)
        
        notifications_created = 0
        
        # Get user's active coupons
        user_coupons = Coupon.objects(
            user=user,
            is_active=True
        )
        
        for coupon in user_coupons:
            coupon_id_str = str(coupon.id)
            
            # Check if coupon is expired
            if coupon.valid_until < now:
                # Check if we already created an expiration notification for this coupon
                # Search in all notifications and check metadata
                existing_notifications = Notification.objects(
                    user=user,
                    type='coupon_expired'
                )
                existing_notification = None
                for notif in existing_notifications:
                    if notif.metadata:
                        try:
                            metadata = json.loads(notif.metadata)
                            if metadata.get('coupon_id') == coupon_id_str:
                                existing_notification = notif
                                break
                        except:
                            pass
                
                if not existing_notification:
                    create_notification(
                        user=user,
                        notification_type='coupon_expired',
                        title='Coupon Expired ⏰',
                        message=f'Your coupon code {coupon.code} has expired. Valid until {coupon.valid_until.strftime("%Y-%m-%d")}.',
                        link='/dashboard',
                        metadata={'coupon_id': coupon_id_str, 'coupon_code': coupon.code}
                    )
                    notifications_created += 1
            
            # Check if coupon is expiring soon (within 3 days)
            elif coupon.valid_until <= three_days_later and coupon.valid_until > now:
                # Check if we already created an expiring notification for this coupon
                existing_notifications = Notification.objects(
                    user=user,
                    type='coupon_expiring'
                )
                existing_notification = None
                for notif in existing_notifications:
                    if notif.metadata:
                        try:
                            metadata = json.loads(notif.metadata)
                            if metadata.get('coupon_id') == coupon_id_str:
                                existing_notification = notif
                                break
                        except:
                            pass
                
                if not existing_notification:
                    days_left = (coupon.valid_until - now).days
                    create_notification(
                        user=user,
                        notification_type='coupon_expiring',
                        title='Coupon Expiring Soon! ⚠️',
                        message=f'Your coupon code {coupon.code} expires in {days_left} day(s). Use it before {coupon.valid_until.strftime("%Y-%m-%d")}!',
                        link='/dashboard',
                        metadata={'coupon_id': coupon_id_str, 'coupon_code': coupon.code, 'days_left': days_left}
                    )
                    notifications_created += 1

        return JsonResponse({
            "success": True,
            "notifications_created": notifications_created,
            "message": f"Checked coupon expirations. Created {notifications_created} notification(s)."
        }, status=200)

    except User.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found"}, status=404)
    except Exception as e:
        import traceback
        print(f"Error in check_coupon_expirations: {traceback.format_exc()}")
        return JsonResponse({"success": False, "message": str(e)}, status=500)

