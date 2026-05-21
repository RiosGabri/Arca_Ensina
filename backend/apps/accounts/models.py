import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Manager de User com login por e-mail (sem username)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser precisa de is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser precisa de is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    # Login passa a ser por e-mail; username deixa de existir.
    username = None
    email = models.EmailField("e-mail", unique=True, blank=False)

    class Profile(models.TextChoices):
        MEDICO = "medico", "Médico"
        ADMIN = "admin", "Administrador"
        PESQUISADOR = "pesquisador", "Pesquisador"

    class Gender(models.TextChoices):
        MASCULINO = "masculino", "Masculino"
        FEMININO = "feminino", "Feminino"
        OUTRO = "outro", "Outro"
        NAO_INFORMADO = "nao_informado", "Não informado"

    profile = models.CharField(
        max_length=20,
        choices=Profile.choices,
        default=Profile.MEDICO,
        verbose_name="Perfil",
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        default=Gender.NAO_INFORMADO,
        verbose_name="Gênero",
    )
    birth_date = models.DateField("data de nascimento", null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self):
        return f"{self.get_full_name() or self.email} ({self.get_profile_display()})"


def generate_invite_token() -> str:
    return secrets.token_urlsafe(32)


def default_invite_expiry():
    return timezone.now() + timedelta(days=7)


class Invitation(models.Model):
    """Convite que habilita o cadastro de um e-mail com um perfil específico."""

    email = models.EmailField("e-mail")
    profile = models.CharField(
        max_length=20,
        choices=User.Profile.choices,
        verbose_name="Perfil",
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_invite_token,
        editable=False,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_invitations",
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField("criado em", auto_now_add=True)
    expires_at = models.DateTimeField("expira em", default=default_invite_expiry)
    accepted_at = models.DateTimeField("aceito em", null=True, blank=True)

    class Meta:
        verbose_name = "Convite"
        verbose_name_plural = "Convites"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Convite para {self.email} ({self.get_profile_display()})"

    @property
    def is_used(self) -> bool:
        return self.accepted_at is not None

    @property
    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_used and not self.is_expired
