from rest_framework import status
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Invitation
from .serializers import (
    InvitationCheckSerializer,
    RegisterSerializer,
    UserSerializer,
)


class InvitationCheckView(APIView):
    """Valida um token de convite e devolve e-mail + perfil associados."""

    permission_classes = [AllowAny]

    def get(self, request, token, **kwargs):
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            raise NotFound("Convite não encontrado.")
        if invitation.is_used:
            raise ValidationError("Este convite já foi utilizado.")
        if invitation.is_expired:
            raise ValidationError("Este convite expirou.")
        return Response(InvitationCheckSerializer(invitation).data)


class RegisterView(APIView):
    """Cadastro só é possível com um token de convite válido."""

    permission_classes = [AllowAny]

    def post(self, request, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "id": user.id,
                "email": user.email,
                "profile": user.profile,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, **kwargs):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, **kwargs):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            raise ValidationError("Refresh token is required.")
        try:
            token = RefreshToken(refresh_token)
        except TokenError:
            raise ValidationError("Invalid or expired refresh token.")
        if int(token.get("user_id")) != request.user.id:
            raise PermissionDenied("Token does not belong to user.")
        token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
