from django.db import models


class BackupRecord(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Успішно"
        FAILED = "failed", "Помилка"

    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Створено")
    filename = models.CharField(max_length=255, verbose_name="Файл")
    size_bytes = models.BigIntegerField(null=True, blank=True, verbose_name="Розмір (байт)")
    duration_seconds = models.FloatField(null=True, blank=True, verbose_name="Тривалість (с)")
    status = models.CharField(
        max_length=20, choices=Status.choices, db_index=True, verbose_name="Статус"
    )
    error_message = models.TextField(blank=True, verbose_name="Помилка")

    # Легка щоденна перевірка: pg_restore --list, без створення бази
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="Перевірено (легка)")
    verified_ok = models.BooleanField(null=True, verbose_name="Легка перевірка успішна")

    # Важка перевірка: реальне відновлення в тимчасову базу
    full_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Перевірено (повна)"
    )
    full_verified_ok = models.BooleanField(null=True, verbose_name="Повна перевірка успішна")

    class Meta:
        verbose_name = "Резервна копія"
        verbose_name_plural = "Резервні копії"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.filename} ({self.status})"
