import pytest
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from accounts.models import User


@pytest.mark.django_db
def test_anonymous_cannot_access_dashboard_stats():
    client = APIClient()
    response = client.get("/api/dashboard/")
    assert response.status_code == 401


@pytest.mark.django_db
def test_student_cannot_access_dashboard_stats():
    student = User.objects.create_user(username="stud_dash", password="pass12345", role="student")
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=student)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.get("/api/dashboard/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_owner_can_access_dashboard_stats():
    owner = User.objects.create_superuser(username="owner_dash", password="pass12345", role="owner")
    client = APIClient()
    token, _ = Token.objects.get_or_create(user=owner)
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    response = client.get("/api/dashboard/")

    assert response.status_code == 200
    assert "total_students" in response.data
