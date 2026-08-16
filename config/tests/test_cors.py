import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_allowed_origin_gets_cors_header(settings):
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    client = APIClient()

    response = client.get("/api/courses/", HTTP_ORIGIN="http://localhost:3000")

    assert response["Access-Control-Allow-Origin"] == "http://localhost:3000"


@pytest.mark.django_db
def test_disallowed_origin_gets_no_cors_header(settings):
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    client = APIClient()

    response = client.get("/api/courses/", HTTP_ORIGIN="http://evil.com")

    assert "Access-Control-Allow-Origin" not in response
