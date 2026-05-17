import django_filters
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import IsAdmin
from apps.audit.mixins import AuditableMixin

from .services import ProtocolExecutionEngine
from .models import Protocol, ProtocolVersion, ProtocolExecution
from .serializers import (
    ProtocolListSerializer,
    ProtocolSerializer,
    ProtocolVersionCreateSerializer,
    ProtocolVersionSerializer,
    ProtocolExecutionSerializer,
    ProtocolExecutionStartSerializer,
    ProtocolExecutionAnswerSerializer
)


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
    
    @action(detail=True, methods=["post"], url_path="start")
    def executar(self, request, pk=None, **kwargs):
        version = self.get_object()
        serializer = ProtocolExecutionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        execution = ProtocolExecution.objects.create(
            version=version,
            physician=request.user,
            patient_name=serializer.validated_data["patient_name"],
        )
        
        execution = ProtocolExecutionEngine().comecar(execution)
        
        return Response(
            ProtocolExecutionSerializer(execution).data,
            status=201,
        )

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

    @action(detail=True, methods=["post"], url_path="answer")
    def answer(self, request, pk=None, **kwargs):
        execution= self.get_object()

        serializer = ProtocolExecutionAnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ProtocolExecutionEngine().resposta_step_atual(
            execution,
            serializer.validated_data["values"],
        )

        execution.refresh_from_db()

        return Response(ProtocolExecutionSerializer(execution).data)

    
