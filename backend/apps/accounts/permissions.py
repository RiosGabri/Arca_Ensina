from typing import cast

from rest_framework.permissions import BasePermission

from .models import User


class IsProfile(BasePermission):
    profile: str
    message = "Você não tem o perfil necessário para esta ação."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        user = cast(User, request.user)
        return user.is_superuser or user.profile == self.profile


class IsDoctor(IsProfile):
    profile = User.Profile.MEDICO


class IsAdmin(IsProfile):
    profile = User.Profile.ADMIN


class IsResearcher(IsProfile):
    profile = User.Profile.PESQUISADOR
