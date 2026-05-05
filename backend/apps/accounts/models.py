from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True, blank=False)

    class Profile(models.TextChoices):
        MEDICO = "medico", "Médico"
        ADMIN = "admin", "Administrador"
        PESQUISADOR = "pesquisador", "Pesquisador"

    profile = models.CharField(
        max_length=20,
        choices=Profile.choices,
        default=Profile.MEDICO,
        verbose_name="Perfil",
    )

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_profile_display()})"
