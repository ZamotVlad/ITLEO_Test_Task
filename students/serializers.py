from rest_framework import serializers

from .models import Course, Student


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name"]


class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source="course.name", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "full_name",
            "phone",
            "telegram_username",
            "telegram_chat_id",
            "email",
            "course",
            "course_name",
            "status",
            "group",
            "group_name",
            "created_at",
        ]
