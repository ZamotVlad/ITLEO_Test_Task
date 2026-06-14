from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from unfold.admin import ModelAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(ModelAdmin, UserAdmin):
    list_display = ("username", "email", "role", "is_staff")
    list_filter = ("role",)
