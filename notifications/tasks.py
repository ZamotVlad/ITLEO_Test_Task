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


@shared_task
def send_class_reminders_task():
    services.send_class_reminders()


@shared_task
def send_schedule_change_notification_task(schedule_id):
    services.notify_schedule_change(schedule_id)
