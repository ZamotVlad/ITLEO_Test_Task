from rest_framework import serializers

from .models import Course, Parent, Student


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name"]


class StudentSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()

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

    def get_course_name(self, obj):
        return obj.course.name if obj.course else None

    def get_group_name(self, obj):
        return obj.group.name if obj.group else None


class ParentSerializer(serializers.ModelSerializer):
    student_names = serializers.SerializerMethodField()

    class Meta:
        model = Parent
        fields = [
            "id",
            "full_name",
            "phone",
            "email",
            "user",
            "students",
            "student_names",
        ]

    def get_student_names(self, obj):
        return [s.full_name for s in obj.students.all()]
