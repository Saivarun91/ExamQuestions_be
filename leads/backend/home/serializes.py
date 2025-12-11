from rest_framework_mongoengine.serializers import DocumentSerializer
from .models import TestCategory

class TestCategorySerializer(DocumentSerializer):
    class Meta:
        model = TestCategory
        fields = "__all__"
