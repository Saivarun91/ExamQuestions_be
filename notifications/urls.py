from django.urls import path
from .views import get_notifications, mark_notification_read, mark_all_read, check_coupon_expirations

urlpatterns = [
    path('', get_notifications, name='get_notifications'),
    path('<str:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('mark-all-read/', mark_all_read, name='mark_all_read'),
    path('check-expirations/', check_coupon_expirations, name='check_coupon_expirations'),
]

