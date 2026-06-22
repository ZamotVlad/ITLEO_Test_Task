from accounts.roles import OPERATIONAL_ROLES, Roles
from payments.models import Payment


def scope_students(user, qs=None):
    from students.models import Student

    qs = (
        qs
        if qs is not None
        else Student.objects.select_related("user", "course", "group", "group__teacher")
    )
    if user.role in OPERATIONAL_ROLES:
        return qs
    if user.role == Roles.TEACHER:
        return qs.filter(group__teacher=user)
    if user.role == Roles.PARENT:
        return qs.filter(parents__user=user).distinct()
    if user.role == Roles.STUDENT:
        return qs.filter(user=user)
    return qs.none()


def scope_groups(user, qs=None):
    from schedule.models import Group

    qs = (
        qs
        if qs is not None
        else Group.objects.select_related("teacher").prefetch_related("schedule_entries")
    )
    if user.role in OPERATIONAL_ROLES:
        return qs
    if user.role == Roles.TEACHER:
        return qs.filter(teacher=user)
    if user.role == Roles.PARENT:
        return qs.filter(students__parents__user=user).distinct()
    if user.role == Roles.STUDENT:
        return qs.filter(students__user=user)
    return qs.none()


def scope_schedule(user, qs=None):
    from schedule.models import Schedule

    qs = qs if qs is not None else Schedule.objects.select_related("group", "group__teacher")
    if user.role in OPERATIONAL_ROLES:
        return qs
    if user.role == Roles.TEACHER:
        return qs.filter(group__teacher=user)
    if user.role == Roles.PARENT:
        return qs.filter(group__students__parents__user=user).distinct()
    if user.role == Roles.STUDENT:
        return qs.filter(group__students__user=user)
    return qs.none()


def scope_payments(user, qs=None):
    """
    Teacher не має доступу до фінансів — свідома зміна відносно Stage 1.
    """
    qs = (
        qs
        if qs is not None
        else Payment.objects.select_related("student", "student__user", "student__group")
    )
    if user.role in OPERATIONAL_ROLES:
        return qs
    if user.role == Roles.PARENT:
        return qs.filter(student__parents__user=user).distinct()
    if user.role == Roles.STUDENT:
        return qs.filter(student__user=user)
    return qs.none()


def scope_notifications(user, qs=None):
    """Логи сповіщень — лише owner/manager."""
    from notifications.models import NotificationLog

    qs = qs if qs is not None else NotificationLog.objects.all()
    if user.role in OPERATIONAL_ROLES:
        return qs
    return qs.none()


def get_debtors(user):
    """Список боржників — через scope_payments для правильної фільтрації."""
    return scope_payments(user).filter(status="debt").select_related("student", "student__group")
