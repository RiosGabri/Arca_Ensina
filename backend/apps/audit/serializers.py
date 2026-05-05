from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "user_username",
            "action",
            "resource_type",
            "resource_id",
            "timestamp",
            "ip",
            "payload",
        ]
        read_only_fields = fields
