from django.utils import timezone
from rest_framework import serializers

from .models import Invitation, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "profile",
        ]
        read_only_fields = fields


class InvitationCheckSerializer(serializers.ModelSerializer):
    """Dados expostos publicamente ao validar um convite."""

    class Meta:
        model = Invitation
        fields = ["email", "profile"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    token = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    birth_date = serializers.DateField(required=True)
    gender = serializers.ChoiceField(choices=User.Gender.choices, required=True)

    class Meta:
        model = User
        fields = [
            "id",
            "token",
            "email",
            "first_name",
            "last_name",
            "gender",
            "birth_date",
            "password",
            "profile",
        ]
        # E-mail e perfil vêm do convite, não do payload.
        read_only_fields = ["id", "email", "profile"]

    def validate_token(self, value):
        try:
            invitation = Invitation.objects.get(token=value)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError("Convite inválido.")
        if invitation.is_used:
            raise serializers.ValidationError("Este convite já foi utilizado.")
        if invitation.is_expired:
            raise serializers.ValidationError("Este convite expirou.")
        self._invitation = invitation
        return value

    def validate(self, attrs):
        if User.objects.filter(email__iexact=self._invitation.email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return attrs

    def create(self, validated_data):
        validated_data.pop("token")
        invitation = self._invitation
        user = User.objects.create_user(
            email=invitation.email,
            profile=invitation.profile,
            **validated_data,
        )
        invitation.accepted_at = timezone.now()
        invitation.save(update_fields=["accepted_at"])
        return user
