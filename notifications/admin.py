from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import NotificationLog


@admin.register(NotificationLog)
class NotificationLogAdmin(ModelAdmin):
    list_display = ("type", "recipient", "status", "sent_at")
    list_filter = ("type", "status")
    search_fields = ("recipient", "message")
    readonly_fields = ("type", "recipient", "message", "status", "sent_at")
