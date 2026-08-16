import pytest

from accounts.roles import Roles
from notifications.models import NotificationLog
from payments.models import Payment
from schedule.models import Group, Schedule
from students.models import Parent, Student
from students.services import (
    get_debtors,
    scope_groups,
    scope_notifications,
    scope_payments,
    scope_schedule,
    scope_students,
)


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", role=Roles.OWNER)


@pytest.fixture
def manager(django_user_model):
    return django_user_model.objects.create_user(username="manager", role=Roles.MANAGER)


@pytest.fixture
def teacher(django_user_model):
    return django_user_model.objects.create_user(username="teacher", role=Roles.TEACHER)


@pytest.fixture
def other_teacher(django_user_model):
    return django_user_model.objects.create_user(username="other_teacher", role=Roles.TEACHER)


@pytest.fixture
def parent_user(django_user_model):
    return django_user_model.objects.create_user(username="parent_user", role=Roles.PARENT)


@pytest.fixture
def student_user(django_user_model):
    return django_user_model.objects.create_user(username="student_user", role=Roles.STUDENT)


@pytest.fixture
def group_a(teacher):
    return Group.objects.create(name="Група A", teacher=teacher)


@pytest.fixture
def group_b(other_teacher):
    return Group.objects.create(name="Група B", teacher=other_teacher)


@pytest.fixture
def student_in_a(group_a, student_user):
    return Student.objects.create(full_name="Свій студент", group=group_a, user=student_user)


@pytest.fixture
def student_in_b(group_b):
    return Student.objects.create(full_name="Чужий студент", group=group_b)


@pytest.fixture
def parent_of_a(parent_user, student_in_a):
    p = Parent.objects.create(full_name="Батько", user=parent_user)
    p.students.add(student_in_a)
    return p


# ---------------------------------------------------------------------------
# scope_students
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopeStudents:
    def test_owner_sees_all(self, owner, student_in_a, student_in_b):
        assert set(scope_students(owner)) == {student_in_a, student_in_b}

    def test_manager_sees_all(self, manager, student_in_a, student_in_b):
        assert set(scope_students(manager)) == {student_in_a, student_in_b}

    def test_teacher_sees_only_own_group(self, teacher, student_in_a, student_in_b):
        result = set(scope_students(teacher))
        assert result == {student_in_a}
        assert student_in_b not in result

    def test_parent_sees_only_own_child(self, parent_user, parent_of_a, student_in_a, student_in_b):
        result = set(scope_students(parent_user))
        assert result == {student_in_a}
        assert student_in_b not in result

    def test_student_sees_only_self(self, student_user, student_in_a, student_in_b):
        result = set(scope_students(student_user))
        assert result == {student_in_a}
        assert student_in_b not in result

    def test_unknown_role_sees_nothing(self, django_user_model, student_in_a):
        stranger = django_user_model.objects.create_user(username="stranger", role="unknown")
        assert list(scope_students(stranger)) == []


# ---------------------------------------------------------------------------
# scope_groups
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopeGroups:
    def test_owner_sees_all(self, owner, group_a, group_b):
        assert set(scope_groups(owner)) == {group_a, group_b}

    def test_teacher_sees_only_own_group(self, teacher, group_a, group_b):
        result = set(scope_groups(teacher))
        assert result == {group_a}
        assert group_b not in result

    def test_parent_sees_group_of_own_child(
        self, parent_user, parent_of_a, group_a, group_b, student_in_a
    ):
        result = set(scope_groups(parent_user))
        assert result == {group_a}
        assert group_b not in result

    def test_student_sees_own_group(self, student_user, group_a, group_b, student_in_a):
        result = set(scope_groups(student_user))
        assert result == {group_a}
        assert group_b not in result


# ---------------------------------------------------------------------------
# scope_schedule
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopeSchedule:
    @pytest.fixture
    def schedule_a(self, group_a):
        return Schedule.objects.create(
            group=group_a, weekday=0, start_time="10:00", end_time="11:00"
        )

    @pytest.fixture
    def schedule_b(self, group_b):
        return Schedule.objects.create(
            group=group_b, weekday=1, start_time="12:00", end_time="13:00"
        )

    def test_teacher_sees_only_own_group_schedule(self, teacher, schedule_a, schedule_b):
        result = set(scope_schedule(teacher))
        assert result == {schedule_a}
        assert schedule_b not in result

    def test_parent_sees_schedule_of_own_child_group(
        self, parent_user, parent_of_a, schedule_a, schedule_b, student_in_a
    ):
        result = set(scope_schedule(parent_user))
        assert result == {schedule_a}
        assert schedule_b not in result

    def test_student_sees_own_group_schedule(
        self, student_user, schedule_a, schedule_b, student_in_a
    ):
        result = set(scope_schedule(student_user))
        assert result == {schedule_a}
        assert schedule_b not in result


# ---------------------------------------------------------------------------
# scope_payments - teacher gets nothing, by design
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopePayments:
    @pytest.fixture
    def payment_a(self, student_in_a):
        return Payment.objects.create(student=student_in_a, amount=100, date="2026-08-15")

    @pytest.fixture
    def payment_b(self, student_in_b):
        return Payment.objects.create(student=student_in_b, amount=200, date="2026-08-15")

    def test_owner_sees_all(self, owner, payment_a, payment_b):
        assert set(scope_payments(owner)) == {payment_a, payment_b}

    def test_teacher_sees_nothing(self, teacher, payment_a, payment_b):
        """Teachers have no financial access at all - not even for their own group."""
        assert list(scope_payments(teacher)) == []

    def test_parent_sees_only_own_child_payment(
        self, parent_user, parent_of_a, payment_a, payment_b, student_in_a
    ):
        result = set(scope_payments(parent_user))
        assert result == {payment_a}
        assert payment_b not in result

    def test_student_sees_only_own_payment(self, student_user, payment_a, payment_b, student_in_a):
        result = set(scope_payments(student_user))
        assert result == {payment_a}
        assert payment_b not in result


# ---------------------------------------------------------------------------
# scope_notifications - owner/manager only
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestScopeNotifications:
    @pytest.fixture
    def log(self):
        return NotificationLog.objects.create(type="email", recipient="a@test.com", message="x")

    def test_owner_sees_logs(self, owner, log):
        assert list(scope_notifications(owner)) == [log]

    def test_teacher_sees_nothing(self, teacher, log):
        assert list(scope_notifications(teacher)) == []

    def test_parent_sees_nothing(self, parent_user, log):
        assert list(scope_notifications(parent_user)) == []

    def test_student_sees_nothing(self, student_user, log):
        assert list(scope_notifications(student_user)) == []


# ---------------------------------------------------------------------------
# get_debtors
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetDebtors:
    def test_only_debt_status_returned(self, owner, student_in_a, student_in_b):
        debt_payment = Payment.objects.create(
            student=student_in_a, amount=100, date="2026-08-15", status="debt"
        )
        Payment.objects.create(student=student_in_b, amount=200, date="2026-08-15", status="paid")

        result = list(get_debtors(owner))

        assert result == [debt_payment]

    def test_respects_role_scoping(self, parent_user, parent_of_a, student_in_a, student_in_b):
        own_debt = Payment.objects.create(
            student=student_in_a, amount=100, date="2026-08-15", status="debt"
        )
        Payment.objects.create(student=student_in_b, amount=200, date="2026-08-15", status="debt")

        result = list(get_debtors(parent_user))

        assert result == [own_debt]
