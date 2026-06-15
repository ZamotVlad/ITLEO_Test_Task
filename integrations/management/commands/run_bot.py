from django.core.management.base import BaseCommand

from integrations.bot.runner import run


class Command(BaseCommand):
    help = "Запускає Telegram-бота (aiogram, polling)"

    def handle(self, *args, **options):
        run()
