from rest_framework import viewsets

from accounts.roles import OPERATIONAL_ROLES, Roles
from students.models import Course, Parent
from students.permissions import RoleBasedPermission
from students.serializers import CourseSerializer, ParentSerializer, StudentSerializer
from students.services import scope_students


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [RoleBasedPermission]

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [RoleBasedPermission]
    filterset_fields = ["status", "group", "course"]
    search_fields = ["full_name", "phone"]

    def get_queryset(self):
        return scope_students(self.request.user)

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class ParentViewSet(viewsets.ModelViewSet):
    serializer_class = ParentSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        qs = Parent.objects.prefetch_related(
            "students",
            "students__user",
            "students__group",
        ).select_related("user")
        if self.request.user.role in OPERATIONAL_ROLES:
            return qs
        if self.request.user.role == Roles.PARENT:
            return qs.filter(user=self.request.user)
        return qs.none()

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)
