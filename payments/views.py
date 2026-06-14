from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from students.permissions import IsAdminOrOwnTeacher
from students.services import get_debtors
from .models import Payment
from .serializers import PaymentSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminOrOwnTeacher]

    def get_queryset(self):
        qs = Payment.objects.select_related("student", "student__group")
        if self.request.user.role.lower() == "teacher":
            qs = qs.filter(student__group__teacher=self.request.user)
        return qs

    @action(detail=False, methods=["get"])
    def debtors(self, request):
        qs = get_debtors(request.user)
        return Response(PaymentSerializer(qs, many=True).data)
