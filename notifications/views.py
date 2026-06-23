from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.roles import Roles
from schedule.models import Group
from students.permissions import RoleBasedPermission
from students.services import scope_notifications

from .serializers import BroadcastSerializer, NotificationLogSerializer
from .tasks import broadcast_to_group_task, send_payment_reminders_task


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationLogSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        return scope_notifications(self.request.user).order_by("-sent_at")

    @action(methods=["post"], detail=False)
    def send_payment_reminders(self, request):
        send_payment_reminders_task.delay()
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)

    @action(methods=["post"], detail=False)
    def broadcast_group(self, request):
        serializer = BroadcastSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            group = Group.objects.get(pk=serializer.validated_data["group_id"])
        except Group.DoesNotExist:
            return Response({"detail": "Групу не знайдено."}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role == Roles.TEACHER and group.teacher_id != request.user.id:
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        broadcast_to_group_task.delay(group.id, serializer.validated_data["message"])
        return Response({"status": "queued"}, status=status.HTTP_202_ACCEPTED)
