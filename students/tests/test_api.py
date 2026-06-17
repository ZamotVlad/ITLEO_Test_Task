from datetime import date

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from payments.models import Payment
from schedule.models import Group
from students.models import Course, Student

# --- Fixtures ---


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="testadmin",
        password="testpass123",
        role="admin",
    )


@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(
        username="testteacher",
        password="testpass123",
        role="teacher",
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def teacher_client(teacher_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=teacher_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def course(db):
    return Course.objects.create(name="Python Junior")


@pytest.fixture
def group(db, teacher_user):
    return Group.objects.create(name="U13", teacher=teacher_user)


@pytest.fixture
def student(db, course, group):
    return Student.objects.create(
        full_name="Тест Студент",
        email="student@test.com",
        course=course,
        group=group,
        status="studying",
    )


@pytest.fixture
def payment(db, student):
    return Payment.objects.create(
        student=student,
        amount=3000,
        date=date.today(),
        status="debt",
    )


# --- Auth тести ---


def test_unauthenticated_cannot_access(db):
    client = APIClient()
    response = client.get("/api/students/")
    assert response.status_code == 401


def test_token_auth_works(admin_client):
    response = admin_client.get("/api/students/")
    assert response.status_code == 200


# --- Студенти ---


def test_admin_can_list_students(admin_client, student):
    response = admin_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] >= 1


def test_admin_can_create_student(admin_client, course, group):
    response = admin_client.post(
        "/api/students/",
        {
            "full_name": "Новий Студент",
            "email": "new@test.com",
            "course": course.id,
            "group": group.id,
            "status": "lead",
        },
    )
    assert response.status_code == 201
    assert response.data["full_name"] == "Новий Студент"


def test_teacher_sees_only_own_group_students(teacher_client, student):
    response = teacher_client.get("/api/students/")
    assert response.status_code == 200
    for s in response.data["results"]:
        assert s["group"] == student.group.id


def test_teacher_cannot_access_other_group_student(teacher_client, db):
    other_teacher = User.objects.create_user(
        username="other_teacher",
        password="pass123",
        role="teacher",
    )
    other_group = Group.objects.create(name="OtherGroup", teacher=other_teacher)
    other_student = Student.objects.create(
        full_name="Чужий Студент",
        group=other_group,
        status="studying",
    )
    response = teacher_client.get(f"/api/students/{other_student.id}/")
    assert response.status_code in [403, 404]


# --- Оплати ---


def test_admin_can_create_payment(admin_client, student):
    response = admin_client.post(
        "/api/payments/",
        {
            "student": student.id,
            "amount": "2500.00",
            "date": date.today().isoformat(),
            "status": "pending",
            "comment": "",
        },
    )
    assert response.status_code == 201
    assert response.data["status"] == "pending"


def test_admin_can_see_debtors(admin_client, payment):
    response = admin_client.get("/api/payments/debtors/")
    assert response.status_code == 200
    assert len(response.data) >= 1


def test_debtors_have_debt_status(admin_client, payment):
    response = admin_client.get("/api/payments/debtors/")
    assert response.status_code == 200
    for p in response.data:
        assert p["status"] == "debt"


# --- Групи ---


def test_admin_can_list_groups(admin_client, group):
    response = admin_client.get("/api/groups/")
    assert response.status_code == 200


def test_teacher_sees_only_own_groups(teacher_client, group):
    response = teacher_client.get("/api/groups/")
    assert response.status_code == 200
    for g in response.data["results"]:
        assert g["id"] == group.id


# --- Сервіси ---


def test_get_debtors_service(db, payment, admin_user):
    from students.services import get_debtors

    qs = get_debtors(admin_user)
    assert qs.count() >= 1
    assert all(p.status == "debt" for p in qs)


def test_get_bot_debtors_text(db, payment):
    from notifications.services import get_bot_debtors_text

    text = get_bot_debtors_text()
    assert "Боржники" in text
    assert "Тест Студент" in text


def test_no_debtors_returns_celebration(db):
    Payment.objects.all().delete()
    from notifications.services import get_bot_debtors_text

    text = get_bot_debtors_text()
    assert text == "Боржників немає 🎉"
