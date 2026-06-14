from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ("student", "amount", "date", "status")
    list_filter = ("status",)
    search_fields = ("student__full_name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(student__group__teacher=request.user)
        return qs
