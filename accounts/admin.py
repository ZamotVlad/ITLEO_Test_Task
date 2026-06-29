from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from import_export.admin import ExportMixin
from unfold.admin import ModelAdmin

from accounts.models import User
from accounts.roles import OPERATIONAL_ROLES, Roles


@admin.register(User)
class CustomUserAdmin(ExportMixin, ModelAdmin, UserAdmin):
    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("Роль і Telegram", {"fields": ("role", "telegram_chat_id")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def has_export_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES
