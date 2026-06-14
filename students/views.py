from rest_framework import viewsets

from .models import Course, Student
from .permissions import IsAdminOrOwnTeacher
from .serializers import CourseSerializer, StudentSerializer


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAdminOrOwnTeacher]


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [IsAdminOrOwnTeacher]
    filterset_fields = ["status", "group", "course"]
    search_fields = ["full_name", "phone"]

    def get_queryset(self):
        qs = Student.objects.select_related("group", "course")
        if self.request.user.role.lower() == "teacher":
            qs = qs.filter(group__teacher=self.request.user)
        return qs
