import django_filters
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsAdmin
from apps.audit.mixins import AuditableMixin

from .engine.interpreter import GuidedProtocolInterpreter
from .models import Protocol, ProtocolExecution, ProtocolVersion
from .serializers import (
    ProtocolExecutionAnswerSerializer,
    ProtocolExecutionSerializer,
    ProtocolExecutionStartSerializer,
    ProtocolListSerializer,
    ProtocolSerializer,
    ProtocolVersionCreateSerializer,
    ProtocolVersionSerializer,
)
from .services import ProtocolExecutionEngine


class ProtocolFilter(django_filters.FilterSet):
    gender_applicable = django_filters.CharFilter(method="filter_gender")

    class Meta:
        model = Protocol
        fields = ["is_active", "specialty"]

    def filter_gender(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(gender_applicable=value) | Q(gender_applicable__isnull=True)
        )


class ProtocolViewSet(AuditableMixin, ModelViewSet):
    """ViewSet para protocolos clínicos."""

    audit_resource_type = "protocol"
    permission_classes = [IsAuthenticated]
    filterset_class = ProtocolFilter
    search_fields = ["title", "cid", "author", "tags"]
    ordering_fields = ["title", "created_at", "updated_at"]

    def get_queryset(self):
        return Protocol.objects.prefetch_related("versions").all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProtocolListSerializer
        return ProtocolSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["get"], url_path="versions")
    def list_versions(self, request, pk=None, **kwargs):
        """Lista todas as versões do protocolo."""
        protocol = self.get_object()
        versions = protocol.versions.select_related("created_by").all()
        serializer = ProtocolVersionSerializer(versions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"], url_path="diff")
    def version_diff(self, request, pk=None, **kwargs):
        """Retorna diff entre duas versões do protocolo."""
        protocol = self.get_object()
        from_version = request.query_params.get("from")
        to_version = request.query_params.get("to")

        if not from_version or not to_version:
            raise ValidationError("Parâmetros 'from' e 'to' são obrigatórios.")

        try:
            v_from = protocol.versions.get(version_number=int(from_version))
            v_to = protocol.versions.get(version_number=int(to_version))
        except ProtocolVersion.DoesNotExist:
            raise NotFound("Versão não encontrada.")

        return Response(
            {
                "from": ProtocolVersionSerializer(v_from).data,
                "to": ProtocolVersionSerializer(v_to).data,
            }
        )

    def _get_active_execution(self, protocol, user):
        return ProtocolExecution.objects.filter(
            version__protocol=protocol,
            physician=user,
            status=ProtocolExecution.Status.EM_ANDAMENTO,
        ).order_by("-started_at").first()

    @action(detail=True, methods=["post"], url_path="execute")
    def execute_start(self, request, pk=None, **kwargs):
        protocol = self.get_object()
        version = protocol.versions.filter(is_current=True).first()
        if not version:
            raise NotFound("Nenhuma versão atual para este protocolo.")

        serializer = ProtocolExecutionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        client_uuid = serializer.validated_data.get("client_uuid")
        context = serializer.validated_data.get("context", {})

        # Idempotência
        if client_uuid:
            existing = ProtocolExecution.objects.filter(
                physician=request.user,
                client_uuid=client_uuid,
            ).first()
            if existing:
                return Response(
                    ProtocolExecutionSerializer(existing).data,
                    status=200,
                )

        execution = ProtocolExecution.objects.create(
            version=version,
            physician=request.user,
            patient_name=serializer.validated_data["patient_name"],
            client_uuid=client_uuid,
        )

        execution = ProtocolExecutionEngine().comecar(execution, context)

        return Response(
            ProtocolExecutionSerializer(execution).data,
            status=201,
        )

    @action(detail=True, methods=["get"], url_path="execute/step")
    def execute_step(self, request, pk=None, **kwargs):
        protocol = self.get_object()
        execution = self._get_active_execution(protocol, request.user)
        if not execution:
            raise NotFound("Nenhuma execução ativa para este protocolo.")

        interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
        step = interpreter.get_step(execution.current_step_key) if execution.current_step_key else None

        # Evaluate gates fresh
        history = [
            {"step_key": s.step_key, "values": s.values}
            for s in execution.states.filter(step_key__isnull=False).order_by("answered_at")
        ]
        context = interpreter.build_context(history)
        warnings = interpreter.evaluate_step_gates(execution.current_step_key, context) if execution.current_step_key else []

        return Response({
            "step": step,
            "gate_warnings": warnings,
        })

    @action(detail=True, methods=["post"], url_path="execute/answer")
    def execute_answer(self, request, pk=None, **kwargs):
        protocol = self.get_object()
        execution = self._get_active_execution(protocol, request.user)
        if not execution:
            raise NotFound("Nenhuma execução ativa para este protocolo.")

        serializer = ProtocolExecutionAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ProtocolExecutionEngine().resposta_step_atual(
            execution,
            serializer.validated_data["values"],
        )

        execution.refresh_from_db()
        return Response(ProtocolExecutionSerializer(execution).data)

    @action(detail=True, methods=["post"], url_path="execute/next")
    def execute_next(self, request, pk=None, **kwargs):
        protocol = self.get_object()
        execution = self._get_active_execution(protocol, request.user)
        if not execution:
            raise NotFound("Nenhuma execução ativa para este protocolo.")

        engine = ProtocolExecutionEngine()
        engine.avancar_step(execution)
        execution.refresh_from_db()

        # Evaluate gates for new step
        interpreter = GuidedProtocolInterpreter(execution.version.steps_data)
        step = interpreter.get_step(execution.current_step_key) if execution.current_step_key else None
        history = [
            {"step_key": s.step_key, "values": s.values}
            for s in execution.states.filter(step_key__isnull=False).order_by("answered_at")
        ]
        context = interpreter.build_context(history)
        warnings = interpreter.evaluate_step_gates(execution.current_step_key, context) if execution.current_step_key else []

        if execution.status == execution.Status.CONCLUIDO:
            return Response({
                "step": None,
                "gate_warnings": [],
                "status": "concluido",
            })

        return Response({
            "step": step,
            "gate_warnings": warnings,
        })

    @action(detail=True, methods=["get"], url_path="execute/reminders")
    def execute_reminders(self, request, pk=None, **kwargs):
        protocol = self.get_object()
        execution = self._get_active_execution(protocol, request.user)
        if not execution:
            raise NotFound("Nenhuma execução ativa para este protocolo.")

        engine = ProtocolExecutionEngine()
        reminders = engine.get_reminders(execution)

        return Response({"reminders": reminders})


class ProtocolVersionViewSet(AuditableMixin, ModelViewSet):
    """ViewSet para versões de protocolo."""

    audit_resource_type = "protocol_version"
    permission_classes = [IsAuthenticated]
    serializer_class = ProtocolVersionSerializer
    http_method_names = ["get", "post", "head", "options"]
    filterset_fields = ["protocol_type", "is_current", "protocol"]
    ordering_fields = ["version_number", "created_at"]

    def get_queryset(self):
        return ProtocolVersion.objects.select_related("protocol", "created_by").all()

    def get_serializer_class(self):
        if self.action == "create":
            return ProtocolVersionCreateSerializer
        return ProtocolVersionSerializer

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "set_current",
        ):
            return [IsAuthenticated(), IsAdmin()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="set-current")
    def set_current(self, request, pk=None, **kwargs):
        """Marca esta versão como atual."""
        version = self.get_object()
        version.is_current = True
        version.save()
        return Response(ProtocolVersionSerializer(version).data)


class ProtocolExecutionViewSet(AuditableMixin, ModelViewSet):
    audit_resource_type = "protocol_execution"
    permission_classes = [IsAuthenticated]
    serializer_class = ProtocolExecutionSerializer

    def get_queryset(self):
        return ProtocolExecution.objects.select_related(
            "version",
            "version__protocol",
            "physician",
            "current_step",
        ).filter(physician=self.request.user)

