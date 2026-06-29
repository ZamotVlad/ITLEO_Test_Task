from django.contrib import admin
from unfold.admin import ModelAdmin

from accounts.roles import OPERATIONAL_ROLES, Roles

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("student", "amount", "date", "status")
    list_filter = ("status",)
    search_fields = ("student__full_name",)

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
            return qs.filter(student__group__teacher=request.user)
        return qs
