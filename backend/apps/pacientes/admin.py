from django import forms
from django.contrib import admin

from .models import Alergia, CalculadoraMedicamento, Paciente, Sintoma


class PacienteAdminForm(forms.ModelForm):
    alergias_input = forms.CharField(
        label="Alergias (separadas por vírgula)",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Ex: Dipirona, Pólen, Amendoim"}),
    )
    sintomas_input = forms.CharField(
        label="Sintomas (separados por vírgula)",
        required=False,
        widget=forms.TextInput(
            attrs={"placeholder": "Ex: Febre, Tosse, Dor de cabeça"}
        ),
    )

    class Meta:
        model = Paciente
        fields = [
            "nome",
            "data_nascimento",
            "genero",
            "peso",
            "altura",
            "nome_responsavel",
            "cidade",
            "telefone",
            "alergias_input",
            "sintomas_input",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["alergias_input"].initial = ", ".join(
                [a.descricao for a in self.instance.alergias.all()]
            )
            self.fields["sintomas_input"].initial = ", ".join(
                [s.descricao for s in self.instance.sintomas.all()]
            )


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    form = PacienteAdminForm
    list_display = (
        "nome",
        "data_nascimento",
        "genero",
        "cidade",
        "telefone",
        "nome_responsavel",
        "created_by",
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

        alergias_texto = form.cleaned_data.get("alergias_input")
        if alergias_texto is not None:
            obj.alergias.clear()
            nomes = [n.strip() for n in alergias_texto.split(",") if n.strip()]
            for nome in nomes:
                alergia, _ = Alergia.objects.get_or_create(descricao=nome)
                obj.alergias.add(alergia)

        sintomas_texto = form.cleaned_data.get("sintomas_input")
        if sintomas_texto is not None:
            obj.sintomas.clear()
            nomes = [n.strip() for n in sintomas_texto.split(",") if n.strip()]
            for nome in nomes:
                sintoma, _ = Sintoma.objects.get_or_create(descricao=nome)
                obj.sintomas.add(sintoma)


@admin.register(Alergia)
class AlergiaAdmin(admin.ModelAdmin):
    list_display = ("descricao",)


@admin.register(Sintoma)
class SintomaAdmin(admin.ModelAdmin):
    list_display = ("descricao",)


@admin.register(CalculadoraMedicamento)
class CalculadoraMedicamentoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
