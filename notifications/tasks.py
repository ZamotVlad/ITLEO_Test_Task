from celery import shared_task

from . import services


@shared_task
def send_payment_reminders_task():
    sent, skipped = services.send_payment_reminders()
    return f"Email надіслано: {sent}, пропущено: {skipped}"


@shared_task
def broadcast_to_group_task(group_id, message):
    sent, skipped = services.broadcast_to_group(group_id, message)
    return f"Telegram надіслано: {sent}, пропущено: {skipped}"
