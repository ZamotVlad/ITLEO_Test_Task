from django.core.management.base import BaseCommand

from accounts.models import User
from accounts.roles import Roles


class Command(BaseCommand):
    help = "Ініціалізує БД: створює owner-акаунт для входу в адмінку"

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin",
                email="admin@academy.com",
                password="admin",
                role=Roles.OWNER,
            )
            self.stdout.write(
                self.style.SUCCESS('✅ Створено owner-акаунт: логін "admin", пароль "admin"')
            )
        else:
            self.stdout.write("ℹ️  Owner-акаунт вже існує, пропускаємо.")

        self.stdout.write(
            self.style.SUCCESS("✅ Готово. Відкрий http://localhost:8000/admin/ і увійди.")
        )
