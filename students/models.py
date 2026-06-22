from django.conf import settings
from django.db import models


class Course(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курси"

    def __str__(self):
        return self.name


class Student(models.Model):
    STATUS_CHOICES = [
        ("lead", "Lead"),
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
    )
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="lead",
        db_index=True,
    )
    group = models.ForeignKey(
        "schedule.Group",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
    )
    created_at = models.DateTimeField(auto_now_add=True)

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
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    students = models.ManyToManyField(
        Student,
        related_name="parents",
        blank=True,
    )

    class Meta:
        verbose_name = "Батько/мати"
        verbose_name_plural = "Батьки"

    def __str__(self):
        return self.full_name
