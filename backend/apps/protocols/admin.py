from django.contrib import admin

from .models import Protocol, ProtocolVersion


class ProtocolVersionInline(admin.TabularInline):
    model = ProtocolVersion
    extra = 0
    readonly_fields = ["created_at"]
    fields = [
        "version_number",
        "protocol_type",
        "is_current",
        "created_by",
        "created_at",
    ]


@admin.register(Protocol)
class ProtocolAdmin(admin.ModelAdmin):
    list_display = ["title", "cid", "specialty", "is_active", "created_at"]
    list_filter = ["is_active", "gender_applicable", "specialty"]
    search_fields = ["title", "cid", "author"]
    inlines = [ProtocolVersionInline]


@admin.register(ProtocolVersion)
class ProtocolVersionAdmin(admin.ModelAdmin):
    list_display = [
        "protocol",
        "version_number",
        "protocol_type",
        "is_current",
        "created_by",
        "created_at",
    ]
    list_filter = ["protocol_type", "is_current"]
    search_fields = ["protocol__title"]
    raw_id_fields = ["protocol", "created_by"]


