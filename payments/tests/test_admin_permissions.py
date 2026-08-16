import pytest

from accounts.roles import Roles
from payments.admin import PaymentAdmin
from payments.models import Payment


class FakeRequest:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", role=Roles.OWNER)


@pytest.fixture
def manager(django_user_model):
    return django_user_model.objects.create_user(username="manager", role=Roles.MANAGER)


@pytest.fixture
def teacher(django_user_model):
    return django_user_model.objects.create_user(username="teacher", role=Roles.TEACHER)


@pytest.mark.django_db
class TestPaymentAdminPermissions:
    def test_owner_has_full_access(self, owner):
        admin = PaymentAdmin(Payment, None)
        request = FakeRequest(owner)
        assert admin.has_view_permission(request) is True
        assert admin.has_delete_permission(request) is True

    def test_manager_cannot_delete(self, manager):
        admin = PaymentAdmin(Payment, None)
        request = FakeRequest(manager)
        assert admin.has_change_permission(request) is True
        assert admin.has_delete_permission(request) is False

    def test_teacher_has_no_access_to_finances(self, teacher):
        """Explicit business rule: teachers never see payments, even their own group's."""
        admin = PaymentAdmin(Payment, None)
        request = FakeRequest(teacher)
        assert admin.has_view_permission(request) is False
        assert admin.has_add_permission(request) is False
