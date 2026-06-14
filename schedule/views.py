from rest_framework import viewsets

from students.permissions import IsAdminOrOwnTeacher
from .models import Group, Schedule
from .serializers import GroupSerializer, ScheduleSerializer


class GroupViewSet(viewsets.ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAdminOrOwnTeacher]

    def get_queryset(self):
        qs = Group.objects.select_related("teacher").prefetch_related("schedule_entries")
        if self.request.user.role.lower() == "teacher":
            qs = qs.filter(teacher=self.request.user)
        return qs


class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [IsAdminOrOwnTeacher]

    def get_queryset(self):
        qs = Schedule.objects.select_related("group")
        if self.request.user.role.lower() == "teacher":
            qs = qs.filter(group__teacher=self.request.user)
        return qs
