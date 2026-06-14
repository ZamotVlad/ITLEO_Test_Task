from rest_framework import serializers

from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = ["id", "student", "student_name", "amount", "date", "status", "comment"]
