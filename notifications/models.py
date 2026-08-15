from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationLog(models.Model):
    TYPE_CHOICES = [("email", "Email"), ("telegram", "Telegram")]
    STATUS_CHOICES = [("sent", "Надіслано"), ("failed", "Помилка")]
    NOTIFICATION_TYPE_CHOICES = [
        ("payment_reminder", "Нагадування про оплату"),
        ("welcome", "Вітання нового користувача"),
        ("schedule_change", "Зміна розкладу"),
        ("class_reminder", "Нагадування про заняття"),
        ("broadcast", "Розсилка"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name=_("Тип"))
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="payment_reminder",
        db_index=True,
        verbose_name=_("Вид сповіщення"),
    )
    recipient = models.CharField(max_length=255, verbose_name=_("Отримувач"))
    message = models.TextField(verbose_name=_("Повідомлення"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="sent", verbose_name=_("Статус")
    )
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата надсилання"))

    class Meta:
        verbose_name = "Лог сповіщення"
        verbose_name_plural = "Логи сповіщень"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
            models.Index(fields=["notification_type"]),
        ]
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.type}/{self.notification_type} → {self.recipient} ({self.status})"
