from django.core.management.base import BaseCommand

from backups.models import BackupRecord
from backups.services import create_backup, prune_old_backups


class Command(BaseCommand):
    help = "Створює дамп бази і видаляє бекапи, старіші за термін зберігання."

    def handle(self, *args, **options):
        record = create_backup()

        if record.status == BackupRecord.Status.FAILED:
            self.stderr.write(self.style.ERROR(f"Бекап не вдався: {record.error_message}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(f"Бекап створено: {record.filename} ({record.size_bytes} байт)")
            )

        removed = prune_old_backups()
        self.stdout.write(f"Видалено застарілих бекапів: {removed}")
