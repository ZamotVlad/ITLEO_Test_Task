import pytest

from payments.models import Payment
from students.models import Student


@pytest.mark.django_db
def test_soft_delete_hides_payment_from_default_manager():
    student = Student.objects.create(full_name="Тест")
    payment = Payment.objects.create(student=student, amount=100, date="2026-08-15")
    payment.soft_delete()

    assert Payment.objects.count() == 0
    assert Payment.all_objects.count() == 1
