from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from accounts.roles import STAFF_ROLES, Roles


class User(AbstractUser):
    role = models.CharField(
        max_length=20,
        choices=Roles.CHOICES,
        default=Roles.STUDENT,
        verbose_name=_("Роль"),
    )
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Telegram Chat ID"),
    )

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = Roles.OWNER
        self.is_staff = self.is_superuser or self.role in STAFF_ROLES
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.role})"
