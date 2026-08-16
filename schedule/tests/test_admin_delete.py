import pytest

from accounts.roles import Roles
from schedule.admin import GroupAdmin, ScheduleAdmin
from schedule.models import Group, Schedule


class FakeRequest:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner_sched", role=Roles.OWNER)


@pytest.fixture
def teacher(django_user_model):
    return django_user_model.objects.create_user(username="teacher_sched", role=Roles.TEACHER)


@pytest.mark.django_db
class TestGroupAdminGetQueryset:
    def test_owner_sees_all_groups(self, owner):
        Group.objects.create(name="A")
        Group.objects.create(name="B")

        admin = GroupAdmin(Group, None)
        result = admin.get_queryset(FakeRequest(owner))

        assert result.count() == 2

    def test_teacher_branch_filters_own_groups(self, teacher):
        own_group = Group.objects.create(name="Своя", teacher=teacher)
        Group.objects.create(name="Чужа")

        admin = GroupAdmin(Group, None)
        result = admin.get_queryset(FakeRequest(teacher))

        assert list(result) == [own_group]


@pytest.mark.django_db
class TestScheduleAdminGetQueryset:
    def test_teacher_branch_filters_own_group_schedule(self, teacher):
        own_group = Group.objects.create(name="Своя", teacher=teacher)
        other_group = Group.objects.create(name="Чужа")
        own_entry = Schedule.objects.create(
            group=own_group, weekday=0, start_time="10:00", end_time="11:00"
        )
        Schedule.objects.create(group=other_group, weekday=1, start_time="12:00", end_time="13:00")

        admin = ScheduleAdmin(Schedule, None)
        result = admin.get_queryset(FakeRequest(teacher))

        assert list(result) == [own_entry]


@pytest.mark.django_db
class TestGroupAndScheduleAdminDeleteIsSoft:
    def test_group_single_delete_is_soft(self, client, owner):
        group = Group.objects.create(name="Тест")
        client.force_login(owner)

        client.post(f"/admin/schedule/group/{group.id}/delete/", {"post": "yes"})

        assert not Group.objects.filter(id=group.id).exists()
        assert Group.all_objects.filter(id=group.id).exists()

    def test_group_bulk_delete_is_soft(self, client, owner):
        g1 = Group.objects.create(name="Перша")
        g2 = Group.objects.create(name="Друга")
        client.force_login(owner)

        client.post(
            "/admin/schedule/group/",
            {"action": "delete_selected", "_selected_action": [g1.id, g2.id], "post": "yes"},
        )

        assert Group.objects.count() == 0
        assert Group.all_objects.count() == 2

    def test_schedule_single_delete_is_soft(self, client, owner):
        group = Group.objects.create(name="Тест")
        schedule = Schedule.objects.create(
            group=group, weekday=0, start_time="10:00", end_time="11:00"
        )
        client.force_login(owner)

        client.post(f"/admin/schedule/schedule/{schedule.id}/delete/", {"post": "yes"})

        assert not Schedule.objects.filter(id=schedule.id).exists()
        assert Schedule.all_objects.filter(id=schedule.id).exists()

    def test_schedule_bulk_delete_is_soft(self, client, owner):
        group = Group.objects.create(name="Тест")
        s1 = Schedule.objects.create(group=group, weekday=0, start_time="10:00", end_time="11:00")
        s2 = Schedule.objects.create(group=group, weekday=1, start_time="12:00", end_time="13:00")
        client.force_login(owner)

        client.post(
            "/admin/schedule/schedule/",
            {"action": "delete_selected", "_selected_action": [s1.id, s2.id], "post": "yes"},
        )

        assert Schedule.objects.count() == 0
        assert Schedule.all_objects.count() == 2
