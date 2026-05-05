from .models import AuditLog


def log_audit(user, action, resource_type="", resource_id="", ip=None, payload=None):
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else "",
        ip=ip,
        payload=payload or {},
    )
