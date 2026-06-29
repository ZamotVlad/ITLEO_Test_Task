from django.contrib import admin
from unfold.admin import ModelAdmin

from accounts.roles import OPERATIONAL_ROLES, Roles

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("type", "recipient", "status", "sent_at")
    list_filter = ("type", "status")
    search_fields = ("recipient", "message")
    readonly_fields = ("type", "recipient", "message", "status", "sent_at")

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return False  # логи не створюються вручну

    def has_change_permission(self, request, obj=None):
        return False  # логи не редагуються

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER
