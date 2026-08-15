import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
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


@pytest.mark.django_db
def test_api_delete_group_is_soft():
    owner = User.objects.create_superuser(
        username="api_owner_group", password="pass12345", role="owner"
    )
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=owner)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    group = Group.objects.create(name="Тест")

    response = client.delete(f"/api/groups/{group.id}/")

    assert response.status_code == 204
    assert not Group.objects.filter(id=group.id).exists()
    assert Group.all_objects.filter(id=group.id).exists()
