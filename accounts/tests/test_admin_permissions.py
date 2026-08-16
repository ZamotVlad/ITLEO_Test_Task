import pytest

from accounts.admin import CustomUserAdmin
from accounts.models import User
from accounts.roles import Roles


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
class TestCustomUserAdminPermissions:
    def test_owner_has_full_access(self, owner):
        admin = CustomUserAdmin(User, None)
        request = FakeRequest(owner)
        assert admin.has_view_permission(request) is True
        assert admin.has_delete_permission(request) is True
        assert admin.has_export_permission(request) is True

    def test_manager_cannot_delete_users(self, manager):
        admin = CustomUserAdmin(User, None)
        request = FakeRequest(manager)
        assert admin.has_change_permission(request) is True
        assert admin.has_delete_permission(request) is False

    def test_teacher_has_no_access(self, teacher):
        admin = CustomUserAdmin(User, None)
        request = FakeRequest(teacher)
        assert admin.has_view_permission(request) is False
