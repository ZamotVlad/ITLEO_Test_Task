from payments.models import Payment


def get_debtors(user):
    qs = Payment.objects.filter(status="debt").select_related("student", "student__group")
    if user.role.lower() == "teacher":
        qs = qs.filter(student__group__teacher=user)
    return qs
