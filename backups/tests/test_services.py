import subprocess
from unittest.mock import MagicMock, patch

import pytest

from backups.models import BackupRecord
from backups.services import create_backup, prune_old_backups


@pytest.mark.django_db
class TestCreateBackup:
    @patch("backups.services.subprocess.run")
    def test_success_creates_record_with_correct_status(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):

            def fake_dump(*args, **kwargs):
                output_path = args[0][args[0].index("-f") + 1]
                with open(output_path, "wb") as f:
                    f.write(b"fake dump content")
                return MagicMock()

            mock_run.side_effect = fake_dump

            record = create_backup()

            assert record.status == BackupRecord.Status.SUCCESS
            assert record.size_bytes == len(b"fake dump content")
            assert record.filename.startswith("backup_")
            assert record.filename.endswith(".dump")

    @patch("backups.services.subprocess.run")
    def test_failed_dump_creates_failed_record(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            mock_run.side_effect = subprocess.CalledProcessError(
                1, "pg_dump", stderr=b"connection refused"
            )

            record = create_backup()

            assert record.status == BackupRecord.Status.FAILED
            assert "connection refused" in record.error_message

    @patch("backups.services.subprocess.run")
    def test_timeout_creates_failed_record(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            mock_run.side_effect = subprocess.TimeoutExpired("pg_dump", 600)

            record = create_backup()

            assert record.status == BackupRecord.Status.FAILED


@pytest.mark.django_db
class TestPruneOldBackups:
    def test_removes_records_older_than_retention(self, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            old = BackupRecord.objects.create(
                filename="old.dump", status=BackupRecord.Status.SUCCESS
            )
            BackupRecord.objects.filter(id=old.id).update(created_at="2020-01-01T00:00:00Z")
            recent = BackupRecord.objects.create(
                filename="recent.dump", status=BackupRecord.Status.SUCCESS
            )

            removed = prune_old_backups(keep_days=14)

            assert removed == 0
            assert not BackupRecord.objects.filter(id=old.id).exists()
            assert BackupRecord.objects.filter(id=recent.id).exists()

    def test_removes_actual_file_when_present(self, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "old.dump").write_bytes(b"data")
            old = BackupRecord.objects.create(
                filename="old.dump", status=BackupRecord.Status.SUCCESS
            )
            BackupRecord.objects.filter(id=old.id).update(created_at="2020-01-01T00:00:00Z")

            removed = prune_old_backups(keep_days=14)

            assert removed == 1
            assert not (tmp_path / "old.dump").exists()

    def test_never_removes_failed_records(self, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            failed = BackupRecord.objects.create(
                filename="failed.dump", status=BackupRecord.Status.FAILED
            )
            BackupRecord.objects.filter(id=failed.id).update(created_at="2020-01-01T00:00:00Z")

            prune_old_backups(keep_days=14)

            assert BackupRecord.objects.filter(id=failed.id).exists()
