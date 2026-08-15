from django.apps import AppConfig


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"
    verbose_name = "Дашборд"

    def ready(self):
        from django.apps import apps

        apps.get_app_config("authtoken").verbose_name = "Авторизація"
        apps.get_app_config("django_celery_beat").verbose_name = "Автоматизація"
