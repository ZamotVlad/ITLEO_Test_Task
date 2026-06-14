from rest_framework import serializers

from .models import Group, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    weekday_display = serializers.CharField(source="get_weekday_display", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "group",
            "weekday",
            "weekday_display",
            "start_time",
            "end_time",
            "google_event_id",
        ]


class GroupSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    schedule_entries = ScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ["id", "name", "teacher", "teacher_name", "schedule_entries"]
