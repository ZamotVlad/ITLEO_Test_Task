from django.db import models
from django.utils.translation import gettext_lazy as _

from dashboard.models import SoftDeleteModel
from students.models import Student


class Payment(SoftDeleteModel):
    STATUS_CHOICES = [
        ("paid", "Оплачено"),
        ("pending", "Очікується"),
        ("debt", "Борг"),
    ]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="payments", verbose_name=_("Студент")
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("Сума"))
    date = models.DateField(verbose_name=_("Дата"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending", verbose_name=_("Статус")
    )
    comment = models.TextField(blank=True, verbose_name=_("Коментар"))

    class Meta:
        verbose_name = "Оплата"
        verbose_name_plural = "Оплати"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student.full_name} — {self.amount} ({self.status})"
