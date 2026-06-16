import os

import requests
from django.core.mail import send_mail

from payments.models import Payment
from students.models import Student

from .models import NotificationLog


def send_telegram_message(chat_id, text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5,
        )
        return True
    except requests.RequestException:
        return False


def get_bot_debtors_text():
    debts = Payment.objects.filter(status="debt").select_related("student")
    if not debts.exists():
        return "Боржників немає 🎉"
    lines = [f"• {p.student.full_name} — {p.amount} грн" for p in debts]
    return "Боржники:\n" + "\n".join(lines)


def send_payment_reminders():
    debts = Payment.objects.filter(status__in=["pending", "debt"]).select_related("student")
    sent = 0
    skipped = 0

    for payment in debts:
        student = payment.student

        # Email
        if student.email:
            try:
                send_mail(
                    subject="Нагадування про оплату — ITLEO Academy",
                    message=f"Вітаємо, {student.full_name}!\n\nНагадуємо про оплату на суму {payment.amount} грн.\n\nЗ повагою, ITLEO Academy",
                    from_email=None,
                    recipient_list=[student.email],
                )
                NotificationLog.objects.create(
                    type="email",
                    recipient=student.email,
                    message=f"Payment reminder: {payment.amount} грн",
                    status="sent",
                )
                sent += 1
            except Exception:
                NotificationLog.objects.create(
                    type="email",
                    recipient=student.email,
                    message=f"Payment reminder: {payment.amount} грн",
                    status="failed",
                )
                skipped += 1

        # Telegram
        if student.telegram_chat_id:
            success = send_telegram_message(
                student.telegram_chat_id,
                f"Привіт, {student.full_name}! Нагадуємо про оплату: {payment.amount} грн.",
            )
            NotificationLog.objects.create(
                type="telegram",
                recipient=str(student.telegram_chat_id),
                message=f"Payment reminder: {payment.amount} грн",
                status="sent" if success else "failed",
            )

    return sent, skipped


def broadcast_to_group(group_id, message):
    students = Student.objects.filter(
        group_id=group_id,
        telegram_chat_id__isnull=False,
    )
    sent = 0
    skipped = 0

    for student in students:
        success = send_telegram_message(student.telegram_chat_id, message)
        NotificationLog.objects.create(
            type="telegram",
            recipient=str(student.telegram_chat_id),
            message=message,
            status="sent" if success else "failed",
        )
        if success:
            sent += 1
        else:
            skipped += 1

    return sent, skipped


def remind_debtors_telegram():
    debts = Payment.objects.filter(
        status__in=["pending", "debt"],
    ).select_related("student")
    sent = 0
    skipped = 0

    for payment in debts:
        student = payment.student
        if not student.telegram_chat_id:
            skipped += 1
            continue
        success = send_telegram_message(
            student.telegram_chat_id,
            f"Привіт, {student.full_name}! Нагадуємо про оплату: {payment.amount} грн.",
        )
        NotificationLog.objects.create(
            type="telegram",
            recipient=str(student.telegram_chat_id),
            message=f"Remind: {payment.amount} грн",
            status="sent" if success else "failed",
        )
        if success:
            sent += 1
        else:
            skipped += 1

    return sent, skipped
