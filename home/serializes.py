from rest_framework_mongoengine.serializers import DocumentSerializer
from categories.models import Category

class CategorySerializer(DocumentSerializer):
    class Meta:
        model = Category
        fields = "__all__"
