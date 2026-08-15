import pytest

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User
from payments.models import Payment
from students.models import Student


@pytest.mark.django_db
def test_soft_delete_hides_payment_from_default_manager():
    student = Student.objects.create(full_name="Тест")
    payment = Payment.objects.create(student=student, amount=100, date="2026-08-15")
    payment.soft_delete()

    assert Payment.objects.count() == 0
    assert Payment.all_objects.count() == 1


@pytest.mark.django_db
def test_api_delete_payment_is_soft():
    owner = User.objects.create_superuser(
        username="api_owner_payment", password="pass12345", role="owner"
    )
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=owner)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    student = Student.objects.create(full_name="Тест")
    payment = Payment.objects.create(student=student, amount=100, date="2026-08-15")

    response = client.delete(f"/api/payments/{payment.id}/")

    assert response.status_code == 204
    assert not Payment.objects.filter(id=payment.id).exists()
    assert Payment.all_objects.filter(id=payment.id).exists()
