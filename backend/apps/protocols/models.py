from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models

class Protocol(models.Model):
    """Protocolo clínico base."""

    title = models.CharField(max_length=255)
    cid = models.CharField(max_length=20, blank=True, verbose_name="CID")
    specialty = models.CharField(
        max_length=100, blank=True, verbose_name="Especialidade"
    )
    author = models.CharField(max_length=255, blank=True, verbose_name="Autor")
    tags = models.JSONField(default=list, blank=True, verbose_name="Tags")
    age_range_min = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Idade mínima (meses)"
    )
    age_range_max = models.PositiveIntegerField(
        null=True, blank=True, verbose_name="Idade máxima (meses)"
    )

    class GenderApplicable(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"

    gender_applicable = models.CharField(
        max_length=1,
        choices=GenderApplicable.choices,
        blank=True,
        null=True,
        default=None,
        verbose_name="Gênero aplicável",
    )
    is_active = models.BooleanField(default=True, verbose_name="Ativo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Protocolo"
        verbose_name_plural = "Protocolos"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and not self.versions.exists():
            ProtocolVersion.objects.create(
                protocol=self,
                version_number=1,
                is_current=True,
            )


class ProtocolVersion(models.Model):
    """Versão de um protocolo clínico."""

    class ProtocolType(models.TextChoices):
        GUIADO = "guiado", "Guiado"
        PAINEL = "painel", "Painel"

    protocol = models.ForeignKey(
        Protocol,
        on_delete=models.CASCADE,
        related_name="versions",
        verbose_name="Protocolo",
    )
    version_number = models.PositiveIntegerField(verbose_name="Número da versão")
    protocol_type = models.CharField(
        max_length=10,
        choices=ProtocolType.choices,
        default=ProtocolType.GUIADO,
        db_index=True,
        verbose_name="Tipo de protocolo",
    )
    steps_data = models.JSONField(
        default=dict, blank=True, verbose_name="Dados de passos (guiado)"
    )
    panel_data = models.JSONField(
        default=dict, blank=True, verbose_name="Dados de painel"
    )
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Metadados")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Criado por",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_current = models.BooleanField(
        default=False, db_index=True, verbose_name="Versão atual"
    )

    class Meta:
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["protocol", "version_number"],
                name="unique_protocol_version",
            ),
        ]
        verbose_name = "Versão do Protocolo"
        verbose_name_plural = "Versões do Protocolo"

    def __str__(self):
        return f"{self.protocol.title} v{self.version_number}"

    def save(self, *args, **kwargs):
        if self.is_current:
            ProtocolVersion.objects.filter(
                protocol=self.protocol, is_current=True
            ).exclude(pk=self.pk).update(is_current=False)
        super().save(*args, **kwargs)

class ProtocolStep(models.Model):

    class StepType(models.TextChoices):
        INFORMATIVO = "info", "Informativo"
        SIM_NAO = "yes_no", "Sim/Não"
        MULTIPLA_ESCOLHA = "multiple_choice", "Múltipla Escolha"
        CHECKLIST = "checklist", "Checklist com Regra de Avanço"
        INPUT_NUMERICO = "numeric_input", "Input Numérico"
        CALCULO_DERIVADO = "derived_calc", "Cálculo Derivado"
        PRESCRICAO = "medication_prescription", "Prescrição de Medicação"
        AGUARDAR_REAVALIAR = "wait_reassess", "Aguardar/Reavaliar"
        LOOP_TITULACAO = "titration_loop", "Loop de Titulação"

    version = models.ForeignKey(
        ProtocolVersion,
        on_delete=models.CASCADE,
        related_name="steps",
        verbose_name="Versão do protocolo",
    )
    
    step_type = models.CharField(
        max_length=25,
        choices=StepType.choices,
        verbose_name="Tipo do passo",
    )
    
    order = models.PositiveIntegerField(verbose_name="Ordem")
    title = models.CharField(max_length=255, verbose_name="Título")
    content = models.TextField(blank=True, verbose_name="Conteúdo / instrução")
    next_step = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="previous_steps",
        verbose_name="Próximo passo padrão",
    )
    config = models.JSONField(default=dict, blank=True, verbose_name="Configuração")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["version", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "order"],
                name="unique_step_order_per_version",
            )
        ]
        verbose_name = "Passo do Protocolo"
        verbose_name_plural = "Passos do Protocolo"

    def __str__(self):
        return f"{self.version} — {self.order}. {self.title}"

class ProtocolExecution(models.Model):

    class Status(models.TextChoices):
        EM_ANDAMENTO = "em_andamento", "Em andamento"
        CONCLUIDO = "concluido", "Concluído"
        ABANDONADO = "abandonado", "Abandonado"

    version = models.ForeignKey(
        ProtocolVersion,
        on_delete=models.PROTECT,
        related_name="executions",
        verbose_name="Versão do protocolo",
    )
    physician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="protocol_executions",
        verbose_name="Médico",
    )
    patient_name = models.CharField(max_length=255, verbose_name="Nome do paciente")
    client_uuid = models.UUIDField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="UUID do cliente para idempotência",
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.EM_ANDAMENTO,
        db_index=True,
        verbose_name="Status",
    )
    current_step = models.ForeignKey(
        ProtocolStep,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="active_executions",
        verbose_name="Passo atual",
    )
    current_step_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID declarativo do passo atual",
    )
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="Finalizado em")

    class Meta:
        ordering = ["-started_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["physician", "client_uuid"],
                condition=models.Q(client_uuid__isnull=False),
                name="unique_protocol_execution_client_uuid_per_physician",
            )
        ]
        verbose_name = "Execução de Protocolo"
        verbose_name_plural = "Execuções de Protocolo"

    def __str__(self):
        return f"{self.version} — {self.patient_name} ({self.get_status_display()})"
    
    def clean(self):
        if self.version and self.version.protocol_type != ProtocolVersion.ProtocolType.GUIADO:
            raise DjangoValidationError("Só é possível executar protocolos do tipo guiado.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class ProtocolExecutionState(models.Model):

    execution = models.ForeignKey(
        ProtocolExecution,
        on_delete=models.CASCADE,
        related_name="states",
        verbose_name="Execução",
    )
    step = models.ForeignKey(
        ProtocolStep,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="execution_states",
        verbose_name="Passo",
    )
    step_key = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        verbose_name="ID declarativo do passo",
    )
    values = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Valores informados / cálculos derivados",
    )
    loop_count = models.PositiveIntegerField(default=0, verbose_name="Contador de loop")
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name="Respondido em")

    class Meta:
        ordering = ["answered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["execution", "step"],
                name="unique_state_per_step_execution",
            )
        ]
        verbose_name = "Estado de Execução"
        verbose_name_plural = "Estados de Execução"

    def __str__(self):
        if self.step:
            return f"{self.execution} — step {self.step.order}"
        return f"{self.execution} — step {self.step_key}"
