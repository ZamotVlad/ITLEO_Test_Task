from django.db import models


class NotificationLog(models.Model):
    TYPE_CHOICES = [("email", "Email"), ("telegram", "Telegram")]
    STATUS_CHOICES = [("sent", "Sent"), ("failed", "Failed")]
    NOTIFICATION_TYPE_CHOICES = [
        ("payment_reminder", "Нагадування про оплату"),
        ("welcome", "Вітання нового користувача"),
        ("schedule_change", "Зміна розкладу"),
        ("class_reminder", "Нагадування про заняття"),
        ("broadcast", "Розсилка"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    notification_type = models.CharField(
        max_length=30,
        choices=NOTIFICATION_TYPE_CHOICES,
        default="payment_reminder",
        db_index=True,
    )
    recipient = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    sent_at = models.DateTimeField(auto_now_add=True)

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
