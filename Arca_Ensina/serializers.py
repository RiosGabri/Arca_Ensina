from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "profile",
        ]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "profile",
        ]
        read_only_fields = ["id"]

    def validate_profile(self, value):
        if value in ("admin", "pesquisador"):
            raise serializers.ValidationError(
                "Auto-cadastro com perfil admin ou pesquisador não é permitido."
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
