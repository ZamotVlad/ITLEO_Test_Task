from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.roles import OPERATIONAL_ROLES
from payments.models import Payment
from schedule.models import Group
from students.models import Student


def dashboard_callback(request, context):
    context.update(
        {
            "total_students": Student.objects.count(),
            "studying_count": Student.objects.filter(status="studying").count(),
            "debtors_count": Payment.objects.filter(status="debt").count(),
            "groups_count": Group.objects.count(),
        }
    )
    return context


class DashboardStatsPermission(IsAuthenticated):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.role in OPERATIONAL_ROLES


class DashboardStatsView(APIView):
    """JSON-версія тих самих цифр, що dashboard_callback віддає Unfold."""

    permission_classes = [DashboardStatsPermission]

    def get(self, request):
        return Response(
            {
                "total_students": Student.objects.count(),
                "studying_count": Student.objects.filter(status="studying").count(),
                "debtors_count": Payment.objects.filter(status="debt").count(),
                "groups_count": Group.objects.count(),
            }
        )
