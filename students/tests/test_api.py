from datetime import date

import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from payments.models import Payment
from schedule.models import Group
from students.models import Course, Parent, Student

# --- Fixtures ---


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="testadmin",
        password="testpass123",
        role="owner",  # було "admin" — оновлено
    )


@pytest.fixture
def manager_user(db):
    # is_staff встановлюється автоматично через User.save()
    return User.objects.create_user(
        username="testmanager",
        password="testpass123",
        role="manager",
    )


@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(
        username="testteacher",
        password="testpass123",
        role="teacher",
    )


@pytest.fixture
def parent_user(db):
    return User.objects.create_user(
        username="testparent",
        password="testpass123",
        role="parent",
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="teststudent",
        password="testpass123",
        role="student",
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=admin_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def manager_client(manager_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=manager_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def teacher_client(teacher_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=teacher_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def parent_client(parent_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=parent_user)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client


@pytest.fixture
def student_client(student_user):
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=student_user)
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


# --- Ролі автоматично виставляють is_staff ---


def test_owner_has_is_staff(admin_user):
    assert admin_user.is_staff is True
    assert admin_user.role == "owner"


def test_manager_has_is_staff(manager_user):
    assert manager_user.is_staff is True
    assert manager_user.role == "manager"


def test_teacher_has_no_is_staff(teacher_user):
    assert teacher_user.is_staff is False


# --- Студенти ---


def test_owner_can_list_students(admin_client, student):
    response = admin_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] >= 1


def test_manager_can_list_students(manager_client, student):
    response = manager_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] >= 1


def test_owner_can_create_student(admin_client, course, group):
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


def test_teacher_sees_only_own_group_students(teacher_client, student):
    response = teacher_client.get("/api/students/")
    assert response.status_code == 200
    for s in response.data["results"]:
        assert s["group"] == student.group.id


def test_teacher_cannot_post_student(teacher_client, course, group):
    """Teacher може лише читати — не створювати."""
    response = teacher_client.post(
        "/api/students/",
        {"full_name": "Новий", "status": "lead"},
    )
    assert response.status_code == 403


def test_parent_sees_only_own_child(parent_client, parent_user, student, db):
    parent = Parent.objects.create(full_name="Батько", user=parent_user)
    parent.students.add(student)
    response = parent_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_student_sees_only_themselves(student_client, student_user, student, db):
    student.user = student_user
    student.save()
    response = student_client.get("/api/students/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_parent_cannot_post_student(parent_client, course, group):
    response = parent_client.post(
        "/api/students/",
        {"full_name": "Новий", "status": "lead"},
    )
    assert response.status_code == 403


# --- DELETE — тільки owner ---


def test_owner_can_delete_student(admin_client, student):
    response = admin_client.delete(f"/api/students/{student.id}/")
    assert response.status_code == 204


def test_manager_cannot_delete_student(manager_client, student):
    response = manager_client.delete(f"/api/students/{student.id}/")
    assert response.status_code == 403


def test_teacher_cannot_delete_student(teacher_client, student):
    response = teacher_client.delete(f"/api/students/{student.id}/")
    assert response.status_code == 403


# --- Ролі — validate_role ---


def test_manager_cannot_assign_owner_role(manager_client, student_user):
    response = manager_client.patch(
        f"/api/users/{student_user.id}/",
        {"role": "owner"},
        format="json",
    )
    assert response.status_code in [400, 403]


def test_owner_can_change_role(admin_client, teacher_user):
    response = admin_client.patch(
        f"/api/users/{teacher_user.id}/",
        {"role": "manager"},
        format="json",
    )
    assert response.status_code == 200


# --- Оплати ---


def test_owner_can_create_payment(admin_client, student):
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


def test_teacher_cannot_access_payments(teacher_client, payment):
    """Teacher не бачить фінансів — нова матриця прав."""
    response = teacher_client.get("/api/payments/")
    assert response.status_code == 200
    assert response.data["count"] == 0


def test_parent_sees_only_own_child_payments(parent_client, parent_user, student, payment, db):
    parent = Parent.objects.create(full_name="Батько", user=parent_user)
    parent.students.add(student)
    response = parent_client.get("/api/payments/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_parent_cannot_see_other_student_payments(parent_client, db, course, group):
    other_student = Student.objects.create(full_name="Чужа дитина", group=group, status="studying")
    Payment.objects.create(student=other_student, amount=1000, date=date.today(), status="debt")
    response = parent_client.get("/api/payments/")
    assert response.data["count"] == 0


def test_owner_can_see_debtors(admin_client, payment):
    response = admin_client.get("/api/payments/debtors/")
    assert response.status_code == 200
    assert len(response.data) >= 1


# --- Групи ---


def test_owner_can_list_groups(admin_client, group):
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


# --- /api/me/ ---


def test_me_endpoint_returns_current_user(admin_client, admin_user):
    response = admin_client.get("/api/users/me/")
    assert response.status_code == 200
    assert response.data["username"] == admin_user.username
    assert response.data["role"] == "owner"


def test_me_endpoint_works_for_teacher(teacher_client, teacher_user):
    response = teacher_client.get("/api/users/me/")
    assert response.status_code == 200
    assert response.data["role"] == "teacher"


def test_jwt_auth_respects_role_based_permission(teacher_client, teacher_user, student):
    """
    Перевірка ризику, який згадав Лео: RoleBasedPermission і scope_*
    мають однаково коректно працювати незалежно від того, чи це Token, чи JWT.
    """
    from rest_framework.test import APIClient

    jwt_client = APIClient()
    response = jwt_client.post(
        "/api/auth/jwt/create/",
        {"username": teacher_user.username, "password": "testpass123"},
    )
    assert response.status_code == 200
    assert response.data["role"] == "teacher"

    access_token = response.data["access"]
    jwt_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    # Той самий scope_students, що і в Token-варіанті — має віддати тільки свою групу
    response = jwt_client.get("/api/students/")
    assert response.status_code == 200
    for s in response.data["results"]:
        assert s["group"] == student.group.id

    # Той самий RoleBasedPermission — teacher все ще не може створювати
    response = jwt_client.post("/api/students/", {"full_name": "Новий", "status": "lead"})
    assert response.status_code == 403
