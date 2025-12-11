# # users/serializers.py
# from rest_framework import serializers

# class SignupSerializer(serializers.Serializer):
#     full_name = serializers.CharField()
#     email = serializers.EmailField()
#     phone_number = serializers.CharField()
#     location = serializers.CharField(required=False, allow_blank=True)
#     password = serializers.CharField(write_only=True)

# class LoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField(write_only=True)



from rest_framework import serializers
from .models import User, Admin

# ---------------- User Serializer ----------------
class UserSerializer(serializers.Serializer):
    fullname = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    role = serializers.ChoiceField(choices=['student', 'admin'])
    location = serializers.CharField(allow_blank=True, required=False)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)  # ✅ Added here

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # remove before saving
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

# ---------------- Admin Serializer ----------------
class AdminSerializer(serializers.Serializer):
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)  # ✅ Added here

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')  # remove before saving
        admin = Admin(**validated_data)
        admin.set_password(validated_data['password'])
        admin.save()
        return admin
