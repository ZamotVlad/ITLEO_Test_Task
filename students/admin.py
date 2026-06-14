from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Course, Student


@admin.register(Course)
class CourseAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Student)
class StudentAdmin(ModelAdmin):
    list_display = ("full_name", "course", "group", "status", "phone")
    list_filter = ("status", "course", "group")
    search_fields = ("full_name", "phone", "telegram_username")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.role == "teacher":
            return qs.filter(group__teacher=request.user)
        return qs
