from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["action", "resource_type", "resource_id", "user", "timestamp", "ip"]
    list_filter = ["action", "resource_type", "timestamp"]
    search_fields = ["user__username", "resource_id", "ip"]
    readonly_fields = ["id", "timestamp"]
    date_hierarchy = "timestamp"
