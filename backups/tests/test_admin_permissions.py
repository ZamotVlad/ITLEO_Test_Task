from types import SimpleNamespace

import pytest
from django.contrib.admin.sites import AdminSite

from accounts.roles import Roles
from backups.admin import BackupRecordAdmin
from backups.models import BackupRecord


@pytest.fixture
def admin_instance():
    return BackupRecordAdmin(BackupRecord, AdminSite())


def make_request(role=None, is_staff=False):
    user = SimpleNamespace(role=role, is_staff=is_staff)
    return SimpleNamespace(user=user)


class TestBackupRecordAdminPermissions:
    def test_add_always_denied(self, admin_instance):
        assert admin_instance.has_add_permission(make_request()) is False

    def test_change_always_denied(self, admin_instance):
        assert admin_instance.has_change_permission(make_request()) is False

    def test_delete_allowed_for_owner(self, admin_instance):
        request = make_request(role=Roles.OWNER)
        assert admin_instance.has_delete_permission(request) is True

    def test_delete_denied_for_non_owner(self, admin_instance):
        request = make_request(role=Roles.MANAGER)
        assert admin_instance.has_delete_permission(request) is False

    def test_view_allowed_for_staff(self, admin_instance):
        request = make_request(is_staff=True)
        assert admin_instance.has_view_permission(request) is True

    def test_view_denied_for_non_staff(self, admin_instance):
        request = make_request(is_staff=False)
        assert admin_instance.has_view_permission(request) is False
