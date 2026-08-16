import pytest
from django.contrib.auth.models import AnonymousUser

from accounts.roles import Roles
from notifications.models import NotificationLog
from payments.models import Payment
from schedule.models import Group, Schedule
from students.models import Parent, Student
from students.permissions import RoleBasedPermission


class FakeRequest:
    """Permission classes here only read .user and .method - no need for a real HTTP request."""

    def __init__(self, user, method="GET"):
        self.user = user
        self.method = method


@pytest.fixture
def permission():
    return RoleBasedPermission()


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
def other_parent_user(django_user_model):
    return django_user_model.objects.create_user(username="other_parent_user", role=Roles.PARENT)


@pytest.fixture
def student_user(django_user_model):
    return django_user_model.objects.create_user(username="student_user", role=Roles.STUDENT)


@pytest.fixture
def other_student_user(django_user_model):
    return django_user_model.objects.create_user(username="other_student_user", role=Roles.STUDENT)


@pytest.fixture
def group(teacher):
    return Group.objects.create(name="Група A", teacher=teacher)


@pytest.fixture
def student(group, student_user):
    return Student.objects.create(full_name="Студент", group=group, user=student_user)


@pytest.fixture
def parent(parent_user, student):
    p = Parent.objects.create(full_name="Батько", user=parent_user)
    p.students.add(student)
    return p


# ---------------------------------------------------------------------------
# has_permission - method-level, no object involved
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestHasPermission:
    @pytest.mark.parametrize("method", ["GET", "POST", "PATCH", "DELETE"])
    def test_owner_can_do_everything(self, permission, owner, method):
        assert permission.has_permission(FakeRequest(owner, method), None) is True

    @pytest.mark.parametrize("method", ["GET", "POST", "PATCH"])
    def test_manager_can_write_but_not_delete(self, permission, manager, method):
        assert permission.has_permission(FakeRequest(manager, method), None) is True

    def test_manager_cannot_delete(self, permission, manager):
        assert permission.has_permission(FakeRequest(manager, "DELETE"), None) is False

    @pytest.mark.parametrize("role_fixture", ["teacher", "parent_user", "student_user"])
    def test_read_only_roles_can_read(self, permission, request, role_fixture):
        user = request.getfixturevalue(role_fixture)
        assert permission.has_permission(FakeRequest(user, "GET"), None) is True

    @pytest.mark.parametrize("role_fixture", ["teacher", "parent_user", "student_user"])
    @pytest.mark.parametrize("method", ["POST", "PATCH", "DELETE"])
    def test_read_only_roles_cannot_write(self, permission, request, role_fixture, method):
        user = request.getfixturevalue(role_fixture)
        assert permission.has_permission(FakeRequest(user, method), None) is False

    def test_unauthenticated_user_denied(self, permission):
        assert permission.has_permission(FakeRequest(AnonymousUser(), "GET"), None) is False


# ---------------------------------------------------------------------------
# has_object_permission - Student
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionStudent:
    def test_owner_sees_any_student(self, permission, owner, student):
        assert permission.has_object_permission(FakeRequest(owner), None, student) is True

    def test_manager_can_edit_but_not_delete(self, permission, manager, student):
        assert (
            permission.has_object_permission(FakeRequest(manager, "PATCH"), None, student) is True
        )
        assert (
            permission.has_object_permission(FakeRequest(manager, "DELETE"), None, student) is False
        )

    def test_own_teacher_sees_student(self, permission, teacher, student):
        assert permission.has_object_permission(FakeRequest(teacher), None, student) is True

    def test_other_teacher_denied(self, permission, other_teacher, student):
        assert permission.has_object_permission(FakeRequest(other_teacher), None, student) is False

    def test_own_parent_sees_child(self, permission, parent_user, parent, student):
        assert permission.has_object_permission(FakeRequest(parent_user), None, student) is True

    def test_other_parent_denied(self, permission, other_parent_user, parent, student):
        assert (
            permission.has_object_permission(FakeRequest(other_parent_user), None, student) is False
        )

    def test_student_sees_self(self, permission, student_user, student):
        assert permission.has_object_permission(FakeRequest(student_user), None, student) is True

    def test_other_student_denied(self, permission, other_student_user, student):
        assert (
            permission.has_object_permission(FakeRequest(other_student_user), None, student)
            is False
        )


# ---------------------------------------------------------------------------
# has_object_permission - Parent
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionParent:
    def test_teacher_never_sees_parent(self, permission, teacher, parent, student):
        """Parent chain never sets teacher_id - teachers have no reason to touch parent records."""
        assert permission.has_object_permission(FakeRequest(teacher), None, parent) is False

    def test_own_parent_sees_self(self, permission, parent_user, parent, student):
        assert permission.has_object_permission(FakeRequest(parent_user), None, parent) is True

    def test_other_parent_denied(self, permission, other_parent_user, parent, student):
        assert (
            permission.has_object_permission(FakeRequest(other_parent_user), None, parent) is False
        )

    def test_linked_student_sees_own_parent(self, permission, student_user, parent, student):
        assert permission.has_object_permission(FakeRequest(student_user), None, parent) is True

    def test_unrelated_student_denied(self, permission, other_student_user, parent, student):
        assert (
            permission.has_object_permission(FakeRequest(other_student_user), None, parent) is False
        )


# ---------------------------------------------------------------------------
# has_object_permission - Group
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionGroup:
    def test_own_teacher_sees_group(self, permission, teacher, group):
        assert permission.has_object_permission(FakeRequest(teacher), None, group) is True

    def test_other_teacher_denied(self, permission, other_teacher, group):
        assert permission.has_object_permission(FakeRequest(other_teacher), None, group) is False

    def test_parent_with_child_in_group_sees_it(
        self, permission, parent_user, parent, group, student
    ):
        assert permission.has_object_permission(FakeRequest(parent_user), None, group) is True

    def test_parent_without_child_in_group_denied(self, permission, other_parent_user, group):
        assert (
            permission.has_object_permission(FakeRequest(other_parent_user), None, group) is False
        )

    def test_student_in_group_sees_it(self, permission, student_user, group, student):
        assert permission.has_object_permission(FakeRequest(student_user), None, group) is True

    def test_student_not_in_group_denied(self, permission, other_student_user, group):
        assert (
            permission.has_object_permission(FakeRequest(other_student_user), None, group) is False
        )


# ---------------------------------------------------------------------------
# has_object_permission - Schedule
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionSchedule:
    @pytest.fixture
    def schedule(self, group):
        return Schedule.objects.create(group=group, weekday=0, start_time="10:00", end_time="11:00")

    def test_own_teacher_sees_schedule(self, permission, teacher, schedule):
        assert permission.has_object_permission(FakeRequest(teacher), None, schedule) is True

    def test_other_teacher_denied(self, permission, other_teacher, schedule):
        assert permission.has_object_permission(FakeRequest(other_teacher), None, schedule) is False

    def test_parent_of_group_student_sees_schedule(
        self, permission, parent_user, parent, schedule, student
    ):
        assert permission.has_object_permission(FakeRequest(parent_user), None, schedule) is True

    def test_student_in_group_sees_schedule(self, permission, student_user, schedule, student):
        assert permission.has_object_permission(FakeRequest(student_user), None, schedule) is True

    def test_unrelated_student_denied(self, permission, other_student_user, schedule):
        assert (
            permission.has_object_permission(FakeRequest(other_student_user), None, schedule)
            is False
        )


# ---------------------------------------------------------------------------
# has_object_permission - Payment
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionPayment:
    @pytest.fixture
    def payment(self, student):
        return Payment.objects.create(student=student, amount=100, date="2026-08-15")

    def test_teacher_never_sees_payment(self, permission, teacher, payment):
        """Payments carry no teacher_id - financial data must stay outside teacher reach."""
        assert permission.has_object_permission(FakeRequest(teacher), None, payment) is False

    def test_parent_of_student_sees_payment(
        self, permission, parent_user, parent, payment, student
    ):
        assert permission.has_object_permission(FakeRequest(parent_user), None, payment) is True

    def test_other_parent_denied(self, permission, other_parent_user, payment):
        assert (
            permission.has_object_permission(FakeRequest(other_parent_user), None, payment) is False
        )

    def test_student_sees_own_payment(self, permission, student_user, payment, student):
        assert permission.has_object_permission(FakeRequest(student_user), None, payment) is True

    def test_other_student_denied(self, permission, other_student_user, payment):
        assert (
            permission.has_object_permission(FakeRequest(other_student_user), None, payment)
            is False
        )


# ---------------------------------------------------------------------------
# has_object_permission - NotificationLog (owner/manager only, by design)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestObjectPermissionNotificationLog:
    @pytest.fixture
    def log(self):
        return NotificationLog.objects.create(
            type="email", recipient="test@test.com", message="test"
        )

    def test_owner_sees_log(self, permission, owner, log):
        assert permission.has_object_permission(FakeRequest(owner), None, log) is True

    def test_manager_sees_log(self, permission, manager, log):
        assert permission.has_object_permission(FakeRequest(manager, "GET"), None, log) is True

    def test_teacher_denied_even_if_related_data_would_match(self, permission, teacher, log):
        assert permission.has_object_permission(FakeRequest(teacher), None, log) is False

    def test_parent_denied(self, permission, parent_user, log):
        assert permission.has_object_permission(FakeRequest(parent_user), None, log) is False

    def test_student_denied(self, permission, student_user, log):
        assert permission.has_object_permission(FakeRequest(student_user), None, log) is False
