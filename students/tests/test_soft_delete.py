import pytest

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from students.models import Course, Parent, Student


@pytest.mark.django_db
def test_soft_delete_hides_student_from_default_manager():
    student = Student.objects.create(full_name="Тест")
    student.soft_delete()

    assert Student.objects.count() == 0
    assert Student.all_objects.count() == 1


@pytest.mark.django_db
def test_restore_makes_student_visible_again():
    student = Student.objects.create(full_name="Тест")
    student.soft_delete()

    student.restore()

    assert Student.objects.count() == 1


@pytest.mark.django_db
def test_admin_delete_is_soft(client, django_user_model):
    owner = django_user_model.objects.create_superuser(
        username="owner_test", password="pass12345", email="o@test.com"
    )
    student = Student.objects.create(full_name="Тест")
    client.force_login(owner)

    client.post(f"/admin/students/student/{student.id}/delete/", {"post": "yes"})

    assert not Student.objects.filter(id=student.id).exists()
    assert Student.all_objects.filter(id=student.id).exists()


@pytest.mark.django_db
def test_soft_delete_hides_parent_from_default_manager():
    parent = Parent.objects.create(full_name="Тест")
    parent.soft_delete()

    assert Parent.objects.count() == 0
    assert Parent.all_objects.count() == 1


@pytest.mark.django_db
def test_soft_delete_hides_course_from_default_manager():
    course = Course.objects.create(name="Тест")
    course.soft_delete()

    assert Course.objects.count() == 0
    assert Course.all_objects.count() == 1


@pytest.mark.django_db
def test_api_delete_is_soft_not_permanent():
    owner = User.objects.create_superuser(
        username="api_owner_test", password="pass12345", role="owner"
    )
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=owner)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    student = Student.objects.create(full_name="Тест")

    response = client.delete(f"/api/students/{student.id}/")

    assert response.status_code == 204
    assert not Student.objects.filter(id=student.id).exists()
    assert Student.all_objects.filter(id=student.id).exists()
