from rest_framework import viewsets

from .models import Course
from .permissions import RoleBasedPermission
from .serializers import CourseSerializer, StudentSerializer
from .services import scope_students


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [RoleBasedPermission]


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [RoleBasedPermission]
    filterset_fields = ["status", "group", "course"]
    search_fields = ["full_name", "phone"]

    def get_queryset(self):
        # Вся складна логіка N+1 і фільтрації тепер під капотом!
        return scope_students(self.request.user)
