from django.core.management.base import BaseCommand

from backups.models import BackupRecord
from backups.services import verify_backup_quick


class Command(BaseCommand):
    help = "Легка щоденна перевірка останнього успішного бекапу (pg_restore --list)."

    def handle(self, *args, **options):
        record = BackupRecord.objects.filter(status=BackupRecord.Status.SUCCESS).first()

        if record is None:
            self.stderr.write(self.style.ERROR("Успішних бекапів не знайдено"))
            return

        ok = verify_backup_quick(record)

        if ok:
            self.stdout.write(
                self.style.SUCCESS(f"Бекап {record.filename} пройшов легку перевірку")
            )
        else:
            self.stderr.write(
                self.style.ERROR(f"Бекап {record.filename} НЕ пройшов легку перевірку")
            )
