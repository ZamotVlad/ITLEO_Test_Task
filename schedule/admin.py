from django.contrib import admin
from unfold.admin import ModelAdmin

from accounts.roles import OPERATIONAL_ROLES, Roles

from .models import Group, Schedule


@admin.register(Group)
class GroupAdmin(ModelAdmin):
    list_display = ("name", "teacher")
    list_filter = ("teacher",)
    search_fields = ("name",)

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(teacher=request.user)
        return qs


@admin.register(Schedule)
class ScheduleAdmin(ModelAdmin):
    list_display = ("group", "weekday", "start_time", "end_time")
    list_filter = ("weekday", "group")

    def has_view_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_add_permission(self, request):
        return request.user.role in OPERATIONAL_ROLES

    def has_change_permission(self, request, obj=None):
        return request.user.role in OPERATIONAL_ROLES

    def has_delete_permission(self, request, obj=None):
        return request.user.role == Roles.OWNER

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(group__teacher=request.user)
        return qs
