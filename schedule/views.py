from rest_framework import viewsets

from students.permissions import RoleBasedPermission
from students.services import scope_groups, scope_schedule

from .serializers import GroupSerializer, ScheduleSerializer


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        return scope_groups(self.request.user)


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        return scope_schedule(self.request.user)
