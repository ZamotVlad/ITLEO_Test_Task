from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from students.permissions import RoleBasedPermission
from students.services import get_debtors, scope_payments

from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [RoleBasedPermission]

    def get_queryset(self):
        return scope_payments(self.request.user)

    @action(detail=False, methods=["get"])
    def debtors(self, request):
        qs = get_debtors(request.user)
        return Response(PaymentSerializer(qs, many=True).data)
