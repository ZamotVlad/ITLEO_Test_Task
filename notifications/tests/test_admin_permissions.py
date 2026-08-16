import pytest

from accounts.roles import Roles
from notifications.admin import NotificationLogAdmin
from notifications.models import NotificationLog


class FakeRequest:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", role=Roles.OWNER)


@pytest.fixture
def manager(django_user_model):
    return django_user_model.objects.create_user(username="manager", role=Roles.MANAGER)


@pytest.mark.django_db
class TestNotificationLogAdminPermissions:
    def test_logs_can_never_be_added_or_changed_manually(self, owner):
        """Business rule: notification logs are system-generated, never hand-edited."""
        admin = NotificationLogAdmin(NotificationLog, None)
        request = FakeRequest(owner)
        assert admin.has_add_permission(request) is False
        assert admin.has_change_permission(request) is False

    def test_owner_can_view_and_delete(self, owner):
        admin = NotificationLogAdmin(NotificationLog, None)
        request = FakeRequest(owner)
        assert admin.has_view_permission(request) is True
        assert admin.has_delete_permission(request) is True

    def test_manager_can_view_but_not_delete(self, manager):
        admin = NotificationLogAdmin(NotificationLog, None)
        request = FakeRequest(manager)
        assert admin.has_view_permission(request) is True
        assert admin.has_delete_permission(request) is False
