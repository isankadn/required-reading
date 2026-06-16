from django.contrib import admin

from .models import (
    RequiredReadingAcknowledgement,
    RequiredReadingDocument,
    RequiredReadingDocumentAccess,
    RequiredReadingSettings,
)


@admin.register(RequiredReadingSettings)
class RequiredReadingSettingsAdmin(admin.ModelAdmin):
    fields = ("intro_text", "updated_at")
    readonly_fields = ("updated_at",)

    def has_add_permission(self, request):
        return not RequiredReadingSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RequiredReadingDocument)
class RequiredReadingDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "is_active", "display_order", "uploaded_by", "created_at", "updated_at")
    list_filter = ("is_active", "created_at", "updated_at")
    search_fields = ("title", "pdf_file")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("display_order", "title")


@admin.register(RequiredReadingAcknowledgement)
class RequiredReadingAcknowledgementAdmin(admin.ModelAdmin):
    list_display = ("user", "document", "acknowledged", "acknowledged_at", "updated_at")
    list_filter = ("acknowledged", "document", "acknowledged_at", "updated_at")
    search_fields = ("user__username", "user__email", "document__title")
    readonly_fields = ("updated_at",)
    autocomplete_fields = ("user", "document")


@admin.register(RequiredReadingDocumentAccess)
class RequiredReadingDocumentAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "document", "access_count", "first_accessed_at", "last_accessed_at")
    list_filter = ("document", "first_accessed_at", "last_accessed_at")
    search_fields = ("user__username", "user__email", "document__title")
    readonly_fields = ("first_accessed_at", "last_accessed_at", "access_count")
    autocomplete_fields = ("user", "document")
