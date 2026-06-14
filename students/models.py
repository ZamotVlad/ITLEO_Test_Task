from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Student(models.Model):
    STATUS_CHOICES = [
        ("lead", "Lead"),
        ("studying", "Навчається"),
        ("finished", "Завершив"),
        ("frozen", "Заморозка"),
    ]

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    telegram_chat_id = models.BigIntegerField(null=True, blank=True)
    email = models.EmailField(blank=True)
    course = models.ForeignKey(
        Course, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="lead")
    group = models.ForeignKey(
        "schedule.Group", on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["telegram_chat_id"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name
