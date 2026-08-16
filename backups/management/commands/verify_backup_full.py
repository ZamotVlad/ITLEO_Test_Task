from django.core.management.base import BaseCommand

from backups.models import BackupRecord
from backups.services import verify_backup_full


class Command(BaseCommand):
    help = (
        "Повна перевірка останнього успішного бекапу через реальне відновлення (потребує CREATEDB)."
    )

    def handle(self, *args, **options):
        record = BackupRecord.objects.filter(status=BackupRecord.Status.SUCCESS).first()

        if record is None:
            self.stderr.write(self.style.ERROR("Успішних бекапів не знайдено"))
            return

        ok = verify_backup_full(record)

        if ok:
            self.stdout.write(
                self.style.SUCCESS(f"Бекап {record.filename} пройшов повну перевірку")
            )
        else:
            self.stderr.write(
                self.style.ERROR(f"Бекап {record.filename} НЕ пройшов повну перевірку")
            )
