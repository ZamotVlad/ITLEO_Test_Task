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
