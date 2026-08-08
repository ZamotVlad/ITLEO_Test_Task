from django.apps import AppConfig


class CeleryBeatConfig(AppConfig):
    name = "django_celery_beat"
    verbose_name = "Автоматизація"


class AuthTokenConfig(AppConfig):
    name = "rest_framework.authtoken"
    verbose_name = "Авторизація"
