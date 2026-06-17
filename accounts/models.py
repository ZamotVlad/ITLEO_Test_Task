from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("teacher", "Teacher"),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="teacher")

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def __str__(self):
        return f"{self.username} ({self.role})"
