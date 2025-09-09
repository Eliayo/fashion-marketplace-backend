from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email",
                  "password", "role", "phone", "address"]
        read_only_fields = ["role"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.role = User.Roles.CUSTOMER  # Default role
        user.save()
        return user


class AdminUserSerializer(serializers.ModelSerializer):
    """Serializer that allows admin to set roles"""

    class Meta:
        model = User
        fields = ["id", "username", "email", "role",
                  "phone", "address", "must_change_password"]
