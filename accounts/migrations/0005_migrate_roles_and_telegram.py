from django.db import migrations


def migrate_data_forward(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    User.objects.filter(role="admin").update(role="owner")


def migrate_data_backward(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    User.objects.filter(role="owner").update(role="admin")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_telegram_chat_id_alter_user_role"),
        ("students", "0002_alter_course_options_alter_student_options"),
    ]

    operations = [
        migrations.RunPython(
            migrate_data_forward,
            migrate_data_backward,
        ),
    ]
