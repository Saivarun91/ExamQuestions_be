# from mongoengine import Document, StringField, IntField, FloatField, DateTimeField
# from django.utils import timezone

# class DashboardStats(Document):
#     user_id = StringField(required=True, unique=True)  # store Django user ID as string
#     username = StringField(required=True)
#     total_tests = IntField(default=0)
#     average_score = FloatField(default=0)
#     best_score = FloatField(default=0)
#     unlocked_courses = IntField(default=0)
#     last_updated = DateTimeField(default=timezone.now)

#     meta = {
#         'collection': 'dashboard_stats',
#         'ordering': ['-last_updated']
#     }

#     def __str__(self):
#         return f"Dashboard stats for {self.username}"
