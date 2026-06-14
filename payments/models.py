from django.db import models

from students.models import Student


class Payment(models.Model):
    STATUS_CHOICES = [
        ("paid", "Оплачено"),
        ("pending", "Очікується"),
        ("debt", "Борг"),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    comment = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["date"]),
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student.full_name} — {self.amount} ({self.status})"
