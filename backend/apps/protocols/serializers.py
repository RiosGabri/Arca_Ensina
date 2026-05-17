from rest_framework import serializers

from project.serializers import BaseSerializer

from .engine.interpreter import GuidedProtocolInterpreter
from .models import Protocol, ProtocolVersion, ProtocolStep, ProtocolExecution, ProtocolExecutionState


class ProtocolVersionSerializer(BaseSerializer):
    """Serializer completo para versão de protocolo."""

    protocol_title = serializers.CharField(source="protocol.title", read_only=True)

    class Meta:
        model = ProtocolVersion
        fields = [
            "id",
            "protocol",
            "protocol_title",
            "version_number",
            "protocol_type",
            "steps_data",
            "panel_data",
            "metadata",
            "created_by",
            "is_current",
            "created_at",
            "updated_at",
            "version",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version"]


class ProtocolVersionCreateSerializer(BaseSerializer):
    """Serializer para criação de versão com auto-incremento."""

    class Meta:
        model = ProtocolVersion
        fields = [
            "id",
            "protocol",
            "protocol_type",
            "steps_data",
            "panel_data",
            "metadata",
            "created_by",
            "is_current",
            "created_at",
            "updated_at",
            "version",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version"]

    def validate(self, attrs):
        protocol = attrs.get("protocol")
        if protocol and "version_number" not in attrs:
            last = protocol.versions.order_by("-version_number").first()
            attrs["version_number"] = (last.version_number + 1) if last else 1

        if "version_number" not in attrs:
            attrs["version_number"] = 1

        # Copy data from previous version if not provided
        if not attrs.get("steps_data") and not attrs.get("panel_data"):
            prev = (
                protocol.versions.order_by("-version_number").first()
                if protocol
                else None
            )
            if prev:
                attrs.setdefault("steps_data", prev.steps_data)
                attrs.setdefault("panel_data", prev.panel_data)
                attrs.setdefault("protocol_type", prev.protocol_type)

        return attrs

    def create(self, validated_data):
        return ProtocolVersion.objects.create(**validated_data)


class ProtocolSerializer(BaseSerializer):
    """Serializer completo para protocolo com versão atual."""

    current_version = serializers.SerializerMethodField()
    versions_count = serializers.SerializerMethodField()

    class Meta:
        model = Protocol
        fields = [
            "id",
            "title",
            "cid",
            "specialty",
            "author",
            "tags",
            "age_range_min",
            "age_range_max",
            "gender_applicable",
            "is_active",
            "current_version",
            "versions_count",
            "created_at",
            "updated_at",
            "version",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version"]

    def get_current_version(self, obj):
        current = obj.versions.filter(is_current=True).first()
        if current:
            return ProtocolVersionSerializer(current).data
        return None

    def get_versions_count(self, obj):
        return obj.versions.count()


class ProtocolListSerializer(BaseSerializer):
    """Serializer leve para listagem (sem steps_data/panel_data)."""

    current_version_type = serializers.SerializerMethodField()

    class Meta:
        model = Protocol
        fields = [
            "id",
            "title",
            "cid",
            "specialty",
            "author",
            "tags",
            "gender_applicable",
            "is_active",
            "current_version_type",
            "created_at",
            "updated_at",
            "version",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "version"]

    def get_current_version_type(self, obj):
        current = obj.versions.filter(is_current=True).first()
        return current.protocol_type if current else None

class ProtocolStepSerializer(serializers.ModelSerializer):
    """serializer para passo do protocolo"""

    class Meta:
        model = ProtocolStep
        fields = [
            "id",
            "version",
            "step_type",
            "order",
            "title",
            "content",
            "next_step",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

class ProtocolExecutionSerializer(serializers.ModelSerializer):
    """serializer para execução de protocolo"""

    current_step = ProtocolStepSerializer(read_only=True)
    current_step_data = serializers.SerializerMethodField()

    class Meta:
        model = ProtocolExecution
        fields = [
            "id",
            "version",
            "physician",
            "patient_name",
            "client_uuid",
            "status",
            "current_step",
            "current_step_key",
            "current_step_data",
            "started_at",
            "finished_at",
        ]
        read_only_fields = ["id", "physician", "started_at", "version"]

    def get_current_step_data(self, obj):
        if not obj.current_step_key:
            return None

        interpreter = GuidedProtocolInterpreter(obj.version.steps_data)
        return interpreter.get_step(obj.current_step_key)

class ProtocolExecutionStartSerializer(serializers.Serializer):
    """serializer para iniciar uma execução."""

    patient_name = serializers.CharField(max_length=255)
    client_uuid = serializers.UUIDField(required=False)

class ProtocolExecutionAnswerSerializer(serializers.Serializer):
    """serializer para submeter resposta de um passo"""

    values = serializers.JSONField()

class ProtocolExecutionStateSerializer(serializers.ModelSerializer):
    """serializer para estado de execução"""

    class Meta:
        model = ProtocolExecutionState
        fields = [
            "id",
            "execution",
            "step",
            "values",
            "loop_count",
            "answered_at",
        ]
        read_only_fields = ["id", "answered_at"]
