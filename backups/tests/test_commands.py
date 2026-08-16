import subprocess
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest
from django.core.management import call_command

from backups.models import BackupRecord


@pytest.mark.django_db
class TestBackupDbCommand:
    @patch("backups.services.subprocess.run")
    def test_command_creates_backup_record(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):

            def fake_dump(*args, **kwargs):
                output_path = args[0][args[0].index("-f") + 1]
                with open(output_path, "wb") as f:
                    f.write(b"data")
                return MagicMock()

            mock_run.side_effect = fake_dump

            out = StringIO()
            call_command("backup_db", stdout=out)

            assert BackupRecord.objects.filter(status=BackupRecord.Status.SUCCESS).exists()
            assert "Бекап створено" in out.getvalue()

    @patch("backups.services.subprocess.run")
    def test_command_reports_failure(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            mock_run.side_effect = subprocess.CalledProcessError(1, "pg_dump", stderr=b"boom")

            err = StringIO()
            call_command("backup_db", stderr=err)

            assert BackupRecord.objects.filter(status=BackupRecord.Status.FAILED).exists()
            assert "не вдався" in err.getvalue()


@pytest.mark.django_db
class TestVerifyLatestBackupCommand:
    def test_no_backups_reports_error(self):
        err = StringIO()
        call_command("verify_latest_backup", stderr=err)

        assert "Успішних бекапів не знайдено" in err.getvalue()

    @patch("backups.services.subprocess.run")
    def test_valid_backup_reports_success(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "good.dump").write_bytes(b"data")
            BackupRecord.objects.create(filename="good.dump", status=BackupRecord.Status.SUCCESS)
            mock_run.return_value = MagicMock()

            out = StringIO()
            call_command("verify_latest_backup", stdout=out)

            assert "пройшов легку перевірку" in out.getvalue()

    @patch("backups.services.subprocess.run")
    def test_corrupted_backup_reports_failure(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"data")
            BackupRecord.objects.create(filename="bad.dump", status=BackupRecord.Status.SUCCESS)
            mock_run.side_effect = subprocess.CalledProcessError(1, "pg_restore")

            err = StringIO()
            call_command("verify_latest_backup", stderr=err)

            assert "НЕ пройшов легку перевірку" in err.getvalue()


@pytest.mark.django_db
class TestVerifyBackupFullCommand:
    def test_no_backups_reports_error(self):
        err = StringIO()
        call_command("verify_backup_full", stderr=err)

        assert "Успішних бекапів не знайдено" in err.getvalue()

    @patch("backups.services.subprocess.run")
    def test_successful_restore_reports_success(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "good.dump").write_bytes(b"data")
            BackupRecord.objects.create(filename="good.dump", status=BackupRecord.Status.SUCCESS)
            mock_run.return_value = MagicMock()

            out = StringIO()
            call_command("verify_backup_full", stdout=out)

            assert "пройшов повну перевірку" in out.getvalue()

    @patch("backups.services.subprocess.run")
    def test_failed_restore_reports_failure(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"data")
            BackupRecord.objects.create(filename="bad.dump", status=BackupRecord.Status.SUCCESS)

            # check=False виклики (прибирання тимчасової бази в finally) не
            # мають кидати помилку, тільки check=True (createdb/pg_restore).
            def fake_run(*args, **kwargs):
                if kwargs.get("check"):
                    raise subprocess.CalledProcessError(1, "pg_restore")
                return MagicMock()

            mock_run.side_effect = fake_run

            err = StringIO()
            call_command("verify_backup_full", stderr=err)

            assert "НЕ пройшов повну перевірку" in err.getvalue()
