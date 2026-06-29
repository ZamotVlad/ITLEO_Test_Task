from django.core.management.base import BaseCommand

from accounts.models import User
from accounts.roles import Roles
from schedule.models import Group
from students.models import Parent, Student


class Command(BaseCommand):
    help = "Наповнює БД реальними даними академії"

    def handle(self, *args, **options):

        # --- Власники ---
        owners_data = [
            ("leonid_owner", "Леонід", "Ксенчук"),
            ("anastasiia_owner", "Анастасія", "Чумак"),
            ("oleksandr_owner", "Олександр", "Чумак"),
        ]
        for username, first, last in owners_data:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password="academy123",
                    first_name=first,
                    last_name=last,
                    role=Roles.OWNER,
                )
        self.stdout.write(self.style.SUCCESS("✅ Власники створені"))

        # --- Менеджери ---
        managers_data = [
            ("oleksii_manager", "Олексій", "Колба"),
            ("kira_manager", "Кіра", "Мороз"),
        ]
        for username, first, last in managers_data:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password="academy123",
                    first_name=first,
                    last_name=last,
                    role=Roles.MANAGER,
                )
        self.stdout.write(self.style.SUCCESS("✅ Менеджери створені"))

        # --- Викладачі ---
        teachers_data = [
            ("leonid_teacher", "Леонід", ""),
            ("anastasiia_teacher", "Анастасія", ""),
            ("oleksandr_teacher", "Олександр", ""),
            ("oleksii_teacher", "Олексій", ""),
            ("yelyzaveta_teacher", "Єлизавета", ""),
        ]
        for username, first, last in teachers_data:
            if not User.objects.filter(username=username).exists():
                User.objects.create_user(
                    username=username,
                    password="academy123",
                    first_name=first,
                    last_name=last,
                    role=Roles.TEACHER,
                )
        self.stdout.write(self.style.SUCCESS("✅ Викладачі створені"))

        # --- Група U13 (викладач не вказаний) ---
        group, _ = Group.objects.get_or_create(
            name="U13",
            defaults={"teacher": None},
        )
        self.stdout.write(self.style.SUCCESS("✅ Група U13 створена"))

        # --- Студенти U13 ---
        students_data = [
            ("ivan_student", "Іван"),
            ("zakhar_student", "Захар"),
            ("kostiantyn_student", "Костянтин"),
        ]
        students = {}
        for username, full_name in students_data:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    password="academy123",
                    first_name=full_name,
                    role=Roles.STUDENT,
                )
            else:
                user = User.objects.get(username=username)

            student, _ = Student.objects.get_or_create(
                full_name=full_name,
                defaults={
                    "user": user,
                    "group": group,
                    "status": "studying",
                },
            )
            students[username] = student
        self.stdout.write(self.style.SUCCESS("✅ Студенти створені"))

        # --- Батьки ---
        parents_data = [
            ("aleksandra_parent", "Александра", "ivan_student"),
            ("viktoriia_parent", "Вікторія", "zakhar_student"),
            ("anastasiia_moiseieva_parent", "Анастасія Моісєєва", "kostiantyn_student"),
            ("oleksandr_moisieiev_parent", "Олександр Моісєєв", "kostiantyn_student"),
        ]
        for username, full_name, student_key in parents_data:
            if not User.objects.filter(username=username).exists():
                parent_user = User.objects.create_user(
                    username=username,
                    password="academy123",
                    first_name=full_name,
                    role=Roles.PARENT,
                )
            else:
                parent_user = User.objects.get(username=username)

            parent, _ = Parent.objects.get_or_create(
                full_name=full_name,
                defaults={"user": parent_user},
            )
            parent.students.add(students[student_key])
        self.stdout.write(self.style.SUCCESS("✅ Батьки створені і прив'язані"))

        self.stdout.write(self.style.SUCCESS(
            "\n🎉 База наповнена реальними даними!\n"
            "Тимчасовий пароль для всіх: academy123\n"
            "Власники і менеджери можуть змінити пароль через адмінку."
        ))
