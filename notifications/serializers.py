from rest_framework import serializers

from .models import NotificationLog


class NotificationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationLog
        fields = ["id", "type", "recipient", "message", "status", "sent_at"]
        read_only_fields = fields


class BroadcastSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    message = serializers.CharField()
