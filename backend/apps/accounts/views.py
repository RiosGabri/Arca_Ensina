from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, **kwargs):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "id": user.id,
                "username": user.username,
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
