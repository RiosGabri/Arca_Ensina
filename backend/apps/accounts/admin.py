from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import Invitation, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "profile", "is_staff"]
    list_filter = ["profile", "is_staff", "is_superuser", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Informações pessoais",
            {"fields": ("first_name", "last_name", "gender", "birth_date")},
        ),
        (
            "Perfil e permissões",
            {
                "fields": (
                    "profile",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "profile", "password1", "password2"),
            },
        ),
    )


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["email", "profile", "status", "created_at", "expires_at"]
    list_filter = ["profile", "created_at"]
    search_fields = ["email"]
    readonly_fields = [
        "token",
        "invite_link",
        "created_by",
        "created_at",
        "accepted_at",
    ]
    fields = [
        "email",
        "profile",
        "expires_at",
        "invite_link",
        "token",
        "created_by",
        "created_at",
        "accepted_at",
    ]

    @admin.display(description="Situação")
    def status(self, obj):
        if obj.is_used:
            return "Utilizado"
        if obj.is_expired:
            return "Expirado"
        return "Válido"

    @admin.display(description="Link do convite (copie e envie)")
    def invite_link(self, obj):
        if not obj.pk:
            return "O link aparece após salvar o convite."
        url = f"{settings.SITE_URL}/invite/{obj.token}"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
