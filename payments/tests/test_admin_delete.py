import pytest

from accounts.roles import Roles
from payments.admin import PaymentAdmin
from payments.models import Payment
from students.models import Student


class FakeRequest:
    def __init__(self, user):
        self.user = user


@pytest.fixture
def owner(django_user_model):
    return django_user_model.objects.create_user(username="owner_pay", role=Roles.OWNER)


@pytest.fixture
def teacher(django_user_model):
    return django_user_model.objects.create_user(username="teacher_pay", role=Roles.TEACHER)


@pytest.mark.django_db
class TestPaymentAdminGetQueryset:
    def test_owner_sees_all_payments_unfiltered(self, owner):
        admin = PaymentAdmin(Payment, None)
        student = Student.objects.create(full_name="Тест")
        Payment.objects.create(student=student, amount=100, date="2026-08-15")

        result = admin.get_queryset(FakeRequest(owner))

        assert result.count() == 1

    def test_teacher_branch_filters_by_own_group(self, teacher):
        """
        Called directly, bypassing has_view_permission - documents the
        filtering behaviour even though the standard admin UI never
        reaches teachers (OPERATIONAL_ROLES gates access earlier).
        """
        from schedule.models import Group

        own_group = Group.objects.create(name="Своя", teacher=teacher)
        other_group = Group.objects.create(name="Чужа")
        own_student = Student.objects.create(full_name="Свій", group=own_group)
        other_student = Student.objects.create(full_name="Чужий", group=other_group)
        own_payment = Payment.objects.create(student=own_student, amount=100, date="2026-08-15")
        Payment.objects.create(student=other_student, amount=200, date="2026-08-15")

        admin = PaymentAdmin(Payment, None)
        result = admin.get_queryset(FakeRequest(teacher))

        assert list(result) == [own_payment]


@pytest.mark.django_db
class TestPaymentAdminDeleteIsSoft:
    def test_single_delete_is_soft(self, client, owner):
        student = Student.objects.create(full_name="Тест")
        payment = Payment.objects.create(student=student, amount=100, date="2026-08-15")
        client.force_login(owner)

        client.post(f"/admin/payments/payment/{payment.id}/delete/", {"post": "yes"})

        assert not Payment.objects.filter(id=payment.id).exists()
        assert Payment.all_objects.filter(id=payment.id).exists()

    def test_bulk_delete_is_soft(self, client, owner):
        student = Student.objects.create(full_name="Тест")
        p1 = Payment.objects.create(student=student, amount=100, date="2026-08-15")
        p2 = Payment.objects.create(student=student, amount=200, date="2026-08-15")
        client.force_login(owner)

        client.post(
            "/admin/payments/payment/",
            {"action": "delete_selected", "_selected_action": [p1.id, p2.id], "post": "yes"},
        )

        assert Payment.objects.count() == 0
        assert Payment.all_objects.count() == 2
