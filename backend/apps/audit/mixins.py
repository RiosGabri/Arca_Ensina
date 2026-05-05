from .utils import log_audit


class AuditableMixin:
    audit_resource_type = ""

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def get_resource_id(self, instance):
        return getattr(instance, "pk", "")

    def _log(self, request, action, instance=None):
        resource_type = self.audit_resource_type or getattr(self, "basename", "")
        resource_id = self.get_resource_id(instance) if instance else ""
        payload = {
            "method": request.method,
            "path": request.path,
        }
        log_audit(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip=self.get_client_ip(request),
            payload=payload,
        )

    def perform_create(self, serializer):
        super().perform_create(serializer)
        self._log(self.request, "CREATE", serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        self._log(self.request, "UPDATE", serializer.instance)

    def perform_destroy(self, instance):
        self._log(self.request, "DELETE", instance)
        super().perform_destroy(instance)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        self._log(request, "LIST")
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        self._log(request, "RETRIEVE", instance)
        from rest_framework.response import Response

        return Response(serializer.data)
