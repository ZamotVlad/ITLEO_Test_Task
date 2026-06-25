import os

import requests
from django.core.mail import send_mail

from payments.models import Payment
from students.models import Student

from .models import NotificationLog


def send_telegram_message(chat_id, text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5,
        )
        return response.status_code == 200
    except requests.RequestException:
        return False


def _log(type_, notification_type, recipient, message, status):
    NotificationLog.objects.create(
        type=type_,
        notification_type=notification_type,
        recipient=str(recipient),
        message=message,
        status=status,
    )


def get_bot_debtors_text():
    debts = Payment.objects.filter(status="debt").select_related("student")
    if not debts.exists():
        return "Боржників немає 🎉"
    lines = [f"• {p.student.full_name} — {p.amount} грн" for p in debts]
    return "Боржники:\n" + "\n".join(lines)


def remind_debtors_telegram():
    """
    Надсилає Telegram-нагадування студентам-боржникам і CC батькам.
    """
    debts = (
        Payment.objects.filter(status__in=["pending", "debt"])
        .select_related(
            "student",
            "student__user",
        )
        .prefetch_related(
            "student__parents",
            "student__parents__user",
        )
    )
    sent = 0
    skipped = 0

    for payment in debts:
        student = payment.student
        student_text = f"Нагадування про оплату: {payment.amount} грн\nСтудент: {student.full_name}"

        # Надіслати студенту
        student_chat_id = student.user.telegram_chat_id if student.user_id else None
        if student_chat_id:
            success = send_telegram_message(student_chat_id, student_text)
            _log(
                "telegram",
                "payment_reminder",
                student_chat_id,
                student_text,
                "sent" if success else "failed",
            )
            sent += 1 if success else 0
        else:
            skipped += 1

        # CC батькам
        for parent in student.parents.all():
            if not parent.user_id:
                continue
            parent_chat_id = parent.user.telegram_chat_id
            if not parent_chat_id:
                continue
            parent_text = (
                f"Нагадування для вашої дитини ({student.full_name}): оплата {payment.amount} грн"
            )
            success = send_telegram_message(parent_chat_id, parent_text)
            _log(
                "telegram",
                "payment_reminder",
                parent_chat_id,
                parent_text,
                "sent" if success else "failed",
            )
            sent += 1 if success else 0

    return sent, skipped


def send_payment_reminders():
    """
    Email-нагадування боржникам + CC батькам.
    Викликається Celery Beat щодня о 09:00.
    """
    debts = (
        Payment.objects.filter(status__in=["pending", "debt"])
        .select_related(
            "student",
            "student__user",
        )
        .prefetch_related(
            "student__parents",
            "student__parents__user",
        )
    )

    for payment in debts:
        student = payment.student
        subject = "Нагадування про оплату — Academy"
        message = (
            f"Вітаємо, {student.full_name}!\n\n"
            f"Нагадуємо про оплату на суму {payment.amount} грн.\n\n"
            f"З повагою, Academy"
        )

        # Email студенту
        if student.email:
            try:
                send_mail(subject, message, None, [student.email])
                _log("email", "payment_reminder", student.email, message, "sent")
            except Exception:
                _log("email", "payment_reminder", student.email, message, "failed")

        # CC батькам на email
        for parent in student.parents.all():
            if not parent.email:
                continue
            parent_message = (
                f"Вітаємо!\n\n"
                f"Нагадуємо про оплату вашої дитини "
                f"({student.full_name}) на суму {payment.amount} грн.\n\n"
                f"З повагою, Academy"
            )
            try:
                send_mail(subject, parent_message, None, [parent.email])
                _log("email", "payment_reminder", parent.email, parent_message, "sent")
            except Exception:
                _log("email", "payment_reminder", parent.email, parent_message, "failed")


def broadcast_to_group(group_id, message):
    """Розсилка повідомлення всім студентам групи з telegram_chat_id."""
    students = Student.objects.filter(
        group_id=group_id,
        user__telegram_chat_id__isnull=False,
    ).select_related("user")

    sent = 0
    skipped = 0

    for student in students:
        chat_id = student.user.telegram_chat_id
        success = send_telegram_message(chat_id, message)
        _log("telegram", "broadcast", chat_id, message, "sent" if success else "failed")
        if success:
            sent += 1
        else:
            skipped += 1

    return sent, skipped
