from django.conf import settings
from django.db import models


class Group(models.Model):
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_groups",
        limit_choices_to={"role": "teacher"},
    )

    class Meta:
        verbose_name = "Група"
        verbose_name_plural = "Групи"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Schedule(models.Model):
    WEEKDAY_CHOICES = [
        (0, "Понеділок"),
        (1, "Вівторок"),
        (2, "Середа"),
        (3, "Четвер"),
        (4, "П'ятниця"),
        (5, "Субота"),
        (6, "Неділя"),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="schedule_entries")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    google_event_id = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name = "Розклад"
        verbose_name_plural = "Розклад"
        indexes = [models.Index(fields=["weekday"])]
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.group.name} — {self.get_weekday_display()} {self.start_time}-{self.end_time}"
