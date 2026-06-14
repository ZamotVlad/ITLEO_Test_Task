from django.db import models


class NotificationLog(models.Model):
    TYPE_CHOICES = [("email", "Email"), ("telegram", "Telegram")]
    STATUS_CHOICES = [("sent", "Sent"), ("failed", "Failed")]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    recipient = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="sent")
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["type"]),
        ]
        ordering = ["-sent_at"]

    def __str__(self):
        return f"{self.type} → {self.recipient} ({self.status})"
