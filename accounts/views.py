from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from accounts.roles import OPERATIONAL_ROLES
from accounts.serializers import UserSerializer
from students.permissions import RoleBasedPermission


class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        if self.request.user.role in OPERATIONAL_ROLES:
            return User.objects.all().order_by("username")
        return User.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        /api/me/ — профіль поточного користувача.
        Доступний для будь-якої ролі — кожен бачить себе.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
