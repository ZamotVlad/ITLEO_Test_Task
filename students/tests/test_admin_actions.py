import pytest
from django.contrib import admin
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core import mail

from accounts.models import User
from accounts.roles import Roles
from students.admin import StudentAdmin, create_login_action
from students.models import Parent, Student


def _prepare_request(rf, user):
    request = rf.post("/admin/students/student/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    request._messages = FallbackStorage(request)
    request.user = user
    return request


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner", role=Roles.OWNER)


@pytest.fixture
def student_admin():
    return StudentAdmin(Student, admin.site)


@pytest.mark.django_db
class TestCreateLoginAction:
    def test_creates_user_for_student_with_email(self, rf, owner, student_admin):
        student = Student.objects.create(full_name="Тест", email="test@example.com")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id=student.id))

        student.refresh_from_db()
        assert student.user is not None
        assert student.user.email == "test@example.com"
        assert student.user.role == Roles.STUDENT

    def test_creates_user_for_parent_with_correct_role(self, rf, owner, student_admin):
        parent = Parent.objects.create(full_name="Батько", email="parent@example.com")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Parent.objects.filter(id=parent.id))

        parent.refresh_from_db()
        assert parent.user.role == Roles.PARENT

    def test_skips_record_without_email(self, rf, owner, student_admin):
        student = Student.objects.create(full_name="Без email")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id=student.id))

        student.refresh_from_db()
        assert student.user is None

    def test_skips_when_email_already_belongs_to_existing_user(self, rf, owner, student_admin):
        User.objects.create_user(
            username="taken@example.com", email="taken@example.com", role=Roles.STUDENT
        )
        student = Student.objects.create(full_name="Тест", email="taken@example.com")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id=student.id))

        student.refresh_from_db()
        assert student.user is None

    def test_does_not_touch_record_that_already_has_a_user(self, rf, owner, student_admin):
        existing_user = User.objects.create_user(username="already@example.com", role=Roles.STUDENT)
        student = Student.objects.create(
            full_name="Тест", email="already@example.com", user=existing_user
        )
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id=student.id))

        student.refresh_from_db()
        assert student.user_id == existing_user.id

    def test_sends_invitation_email_with_credentials(self, rf, owner, student_admin):
        student = Student.objects.create(full_name="Тест", email="test@example.com")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id=student.id))

        assert len(mail.outbox) == 1
        sent = mail.outbox[0]
        assert sent.to == ["test@example.com"]
        assert "Логін" in sent.body
        assert "Пароль" in sent.body

    def test_two_students_get_different_passwords(self, rf, owner, student_admin):
        s1 = Student.objects.create(full_name="Перший", email="one@example.com")
        s2 = Student.objects.create(full_name="Другий", email="two@example.com")
        request = _prepare_request(rf, owner)

        create_login_action(student_admin, request, Student.objects.filter(id__in=[s1.id, s2.id]))

        password_1 = mail.outbox[0].body.split("Пароль: ")[1].split("\n")[0]
        password_2 = mail.outbox[1].body.split("Пароль: ")[1].split("\n")[0]
        assert password_1 != password_2

    def test_reports_correct_created_and_skipped_counts(self, rf, owner, student_admin):
        with_email = Student.objects.create(full_name="З email", email="ok@example.com")
        without_email = Student.objects.create(full_name="Без email")
        request = _prepare_request(rf, owner)

        create_login_action(
            student_admin,
            request,
            Student.objects.filter(id__in=[with_email.id, without_email.id]),
        )

        messages = list(request._messages)
        assert len(messages) == 1
        assert "Створено: 1" in str(messages[0])
        assert "пропущено: 1" in str(messages[0])
