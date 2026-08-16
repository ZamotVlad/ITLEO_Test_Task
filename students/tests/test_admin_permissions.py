import pytest

from accounts.roles import Roles
from students.admin import CourseAdmin, ParentAdmin, StudentAdmin
from students.models import Course, Parent, Student


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


@pytest.fixture
def parent_user(django_user_model):
    return django_user_model.objects.create_user(username="parent_user", role=Roles.PARENT)


@pytest.fixture
def student_user(django_user_model):
    return django_user_model.objects.create_user(username="student_user", role=Roles.STUDENT)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "admin_class,model",
    [(CourseAdmin, Course), (StudentAdmin, Student), (ParentAdmin, Parent)],
)
class TestStudentsAppAdminPermissions:
    def test_owner_has_full_access(self, admin_class, model, owner):
        admin = admin_class(model, None)
        request = FakeRequest(owner)
        assert admin.has_view_permission(request) is True
        assert admin.has_add_permission(request) is True
        assert admin.has_change_permission(request) is True
        assert admin.has_delete_permission(request) is True

    def test_manager_can_write_but_not_delete(self, admin_class, model, manager):
        admin = admin_class(model, None)
        request = FakeRequest(manager)
        assert admin.has_view_permission(request) is True
        assert admin.has_add_permission(request) is True
        assert admin.has_change_permission(request) is True
        assert admin.has_delete_permission(request) is False

    @pytest.mark.parametrize("role_fixture", ["teacher", "parent_user", "student_user"])
    def test_non_operational_roles_have_no_access(self, admin_class, model, request, role_fixture):
        user = request.getfixturevalue(role_fixture)
        admin = admin_class(model, None)
        fake_request = FakeRequest(user)
        assert admin.has_view_permission(fake_request) is False
        assert admin.has_add_permission(fake_request) is False
        assert admin.has_change_permission(fake_request) is False
        assert admin.has_delete_permission(fake_request) is False


@pytest.mark.django_db
@pytest.mark.parametrize("admin_class,model", [(StudentAdmin, Student), (ParentAdmin, Parent)])
class TestExportPermission:
    def test_owner_and_manager_can_export(self, admin_class, model, owner, manager):
        for user in (owner, manager):
            admin = admin_class(model, None)
            assert admin.has_export_permission(FakeRequest(user)) is True

    @pytest.mark.parametrize("role_fixture", ["teacher", "parent_user", "student_user"])
    def test_others_cannot_export(self, admin_class, model, request, role_fixture):
        user = request.getfixturevalue(role_fixture)
        admin = admin_class(model, None)
        assert admin.has_export_permission(FakeRequest(user)) is False
