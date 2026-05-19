from django.core.validators import RegexValidator
from django.db import models


class Alergia(models.Model):
    descricao = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.descricao


class Sintoma(models.Model):
    descricao = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.descricao


class Paciente(models.Model):
    GENDER_CHOICES = [
        ("M", "Masculino"),
        ("F", "Feminino"),
        ("O", "Outro"),
    ]
    nome = models.CharField(max_length=100)
    telefone_validator = RegexValidator(
        regex=r"^\d{11,13}$",
        message=(
            "O telefone deve conter apenas números, incluindo o código do país e "
            "DDD (ex: 5581999999999)."
        ),
    )
    telefone = models.CharField(validators=[telefone_validator], max_length=13)
    data_nascimento = models.DateField(verbose_name="Data de Nascimento")
    genero = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    peso = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Peso em kg", null=True, blank=True
    )
    altura = models.PositiveIntegerField(
        help_text="Altura em centímetros", null=True, blank=True
    )
    sintomas = models.ManyToManyField(Sintoma, blank=True)
    nome_responsavel = models.CharField(max_length=255, blank=True, null=True)
    cidade = models.CharField(max_length=100)
    alergias = models.ManyToManyField(Alergia, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.nome


class CalculadoraMedicamento(models.Model):
    class Meta:
        verbose_name = "Calculadora de Medicamento"
        verbose_name_plural = "Calculadora de Medicamentos"

    def __str__(self):
        return "Acessar Calculadora"
