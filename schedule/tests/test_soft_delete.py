import pytest

from schedule.models import Group, Schedule


@pytest.mark.django_db
def test_soft_delete_hides_group_from_default_manager():
    group = Group.objects.create(name="Тест")
    group.soft_delete()

    assert Group.objects.count() == 0
    assert Group.all_objects.count() == 1


@pytest.mark.django_db
def test_soft_delete_hides_schedule_from_default_manager():
    group = Group.objects.create(name="Тест")
    schedule = Schedule.objects.create(group=group, weekday=0, start_time="10:00", end_time="11:00")
    schedule.soft_delete()

    assert Schedule.objects.count() == 0
    assert Schedule.all_objects.count() == 1
