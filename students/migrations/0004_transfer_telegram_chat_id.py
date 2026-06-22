import uuid

from django.db import migrations


def transfer_telegram_forward(apps, schema_editor):
    Student = apps.get_model("students", "Student")
    User = apps.get_model("accounts", "User")

    students_to_update = []

    for student in Student.objects.filter(telegram_chat_id__isnull=False):
        if not student.user:
            base_username = student.email if student.email else f"student_{uuid.uuid4().hex[:8]}"
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User.objects.create(
                username=username,
                email=student.email,
                role="student",
                telegram_chat_id=student.telegram_chat_id,
            )

            student.user = user
            students_to_update.append(student)

    if students_to_update:
        Student.objects.bulk_update(students_to_update, ["user"])


def transfer_telegram_backward(apps, schema_editor):
    Student = apps.get_model("students", "Student")

    students_to_update = []
    for student in Student.objects.filter(
        user__isnull=False, user__telegram_chat_id__isnull=False
    ).select_related("user"):
        student.telegram_chat_id = student.user.telegram_chat_id
        students_to_update.append(student)

    if students_to_update:
        Student.objects.bulk_update(students_to_update, ["telegram_chat_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("students", "0003_parent_remove_student_students_st_status_5e2210_idx_and_more"),
    ]

    operations = [
        migrations.RunPython(
            transfer_telegram_forward,
            transfer_telegram_backward,
        ),
    ]
