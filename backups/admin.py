from django.contrib import admin

from accounts.roles import Roles

from .models import BackupRecord


@admin.register(BackupRecord)
class BackupRecordAdmin(admin.ModelAdmin):
    list_display = (
        "filename",
        "status",
        "size_bytes",
        "duration_seconds",
        "verified_ok",
        "full_verified_ok",
        "created_at",
    )
    list_filter = ("status", "verified_ok", "full_verified_ok")
    readonly_fields = [f.name for f in BackupRecord._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def has_view_permission(self, request, obj=None):
        return request.user.is_staff
