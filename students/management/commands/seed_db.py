from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker

from accounts.models import User
from payments.models import Payment
from schedule.models import Group, Schedule
from students.models import Course, Student

fake = Faker("uk_UA")


class Command(BaseCommand):
    help = "Заповнює БД тестовими даними"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Очищення старих даних...")
        Payment.objects.all().delete()
        Student.objects.all().delete()
        Schedule.objects.all().delete()
        Group.objects.all().delete()
        Course.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write("Створення курсів...")
        courses = [
            Course.objects.create(name=name)
            for name in ["Python Junior", "QA Manual", "Frontend React", "LeoGame Junior"]
        ]

        self.stdout.write("Створення викладачів...")
        teachers = []
        for i in range(3):
            teacher = User.objects.create_user(
                username=f"teacher{i + 1}",
                email=fake.email(),
                password="teacher123",
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                role="teacher",
            )
            teachers.append(teacher)

        self.stdout.write("Створення груп...")
        group_names = ["U13", "QA Manual", "LeoGame Junior", "Python Pro"]
        groups = [
            Group.objects.create(
                name=name,
                teacher=teachers[i % len(teachers)],
            )
            for i, name in enumerate(group_names)
        ]

        self.stdout.write("Створення розкладу...")
        for group in groups:
            for weekday in [1, 3]:  # вівторок, четвер
                Schedule.objects.create(
                    group=group,
                    weekday=weekday,
                    start_time="18:00",
                    end_time="20:00",
                )

        self.stdout.write("Створення студентів...")
        statuses = ["lead", "studying", "finished", "frozen"]
        students = []
        for _ in range(40):
            student = Student.objects.create(
                full_name=fake.name(),
                phone=fake.phone_number(),
                telegram_username=f"@{fake.user_name()}",
                email=fake.email(),
                course=fake.random_element(courses),
                group=fake.random_element(groups),
                status=fake.random_element(statuses),
            )
            students.append(student)

        self.stdout.write("Створення оплат...")
        payment_statuses = ["paid", "pending", "debt"]
        for student in students:
            for _ in range(fake.random_int(min=1, max=3)):
                Payment.objects.create(
                    student=student,
                    amount=fake.random_element([2500, 3000, 3500, 4000]),
                    date=fake.date_between(start_date="-90d", end_date="today"),
                    status=fake.random_element(payment_statuses),
                    comment=fake.sentence() if fake.boolean() else "",
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово! Створено: {len(courses)} курси, {len(teachers)} викладачі, "
                f"{len(groups)} групи, {len(students)} студенти"
            )
        )
