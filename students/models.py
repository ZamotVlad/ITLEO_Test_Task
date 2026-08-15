from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Course(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Назва"))

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курси"

    def __str__(self):
        return self.name


class Student(models.Model):
    STATUS_CHOICES = [
        ("lead", "Лід"),
        ("studying", "Навчається"),
        ("finished", "Завершив"),
        ("frozen", "Заморозка"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_profile",
        verbose_name=_("Користувач"),
    )
    full_name = models.CharField(max_length=200, verbose_name=_("Повне ім'я"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    telegram_username = models.CharField(
        max_length=100, blank=True, verbose_name=_("Telegram (нікнейм)")
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Курс"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="lead",
        db_index=True,
        verbose_name=_("Статус"),
    )
    group = models.ForeignKey(
        "schedule.Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name=_("Група"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата створення"))

    class Meta:
        verbose_name = "Студент"
        verbose_name_plural = "Студенти"
        ordering = ["-created_at"]

    def __str__(self):
        return self.full_name

    @property
    def telegram_chat_id(self):
        """Береться з прив'язаного User."""
        return self.user.telegram_chat_id if self.user_id else None


class Parent(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="parent_profile",
    )
    full_name = models.CharField(max_length=200, verbose_name=_("Повне ім'я"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    students = models.ManyToManyField(
        Student,
        related_name="parents",
        blank=True,
        verbose_name=_("Студенти"),
    )

    class Meta:
        verbose_name = "Батько/мати"
        verbose_name_plural = "Батьки"

    def __str__(self):
        return self.full_name
