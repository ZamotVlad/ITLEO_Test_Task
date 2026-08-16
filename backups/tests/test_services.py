import subprocess
from unittest.mock import MagicMock, patch

import pytest

from backups.models import BackupRecord
from backups.services import (
    create_backup,
    prune_old_backups,
    verify_backup_full,
    verify_backup_quick,
)


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


@pytest.mark.django_db
class TestVerifyBackupQuick:
    def test_missing_file_fails_without_running_subprocess(self, tmp_path):
        with (
            patch("backups.services.BACKUP_DIR", tmp_path),
            patch("backups.services.subprocess.run") as mock_run,
        ):
            record = BackupRecord.objects.create(
                filename="missing.dump", status=BackupRecord.Status.SUCCESS
            )

            result = verify_backup_quick(record)

            assert result is False
            mock_run.assert_not_called()
            record.refresh_from_db()
            assert record.verified_ok is False

    @patch("backups.services.subprocess.run")
    def test_valid_archive_marks_verified_true(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "good.dump").write_bytes(b"data")
            record = BackupRecord.objects.create(
                filename="good.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_run.return_value = MagicMock()

            result = verify_backup_quick(record)

            assert result is True
            record.refresh_from_db()
            assert record.verified_ok is True
            assert record.verified_at is not None
            # не мала чіпати повну перевірку
            assert record.full_verified_ok is None

    @patch("backups.services.subprocess.run")
    def test_corrupted_archive_marks_verified_false(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"not a real dump")
            record = BackupRecord.objects.create(
                filename="bad.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_run.side_effect = subprocess.CalledProcessError(1, "pg_restore")

            result = verify_backup_quick(record)

            assert result is False

    def test_skipped_for_already_failed_record(self, tmp_path):
        with patch("backups.services.subprocess.run") as mock_run:
            record = BackupRecord.objects.create(
                filename="x.dump", status=BackupRecord.Status.FAILED
            )

            result = verify_backup_quick(record)

            assert result is False
            mock_run.assert_not_called()


@pytest.mark.django_db
class TestVerifyBackupFull:
    def test_missing_file_fails_without_running_subprocess(self, tmp_path):
        with (
            patch("backups.services.BACKUP_DIR", tmp_path),
            patch("backups.services.subprocess.run") as mock_run,
        ):
            record = BackupRecord.objects.create(
                filename="missing.dump", status=BackupRecord.Status.SUCCESS
            )

            result = verify_backup_full(record)

            assert result is False
            mock_run.assert_not_called()
            record.refresh_from_db()
            assert record.full_verified_ok is False

    @patch("backups.services.subprocess.run")
    def test_successful_restore_marks_full_verified_true(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "good.dump").write_bytes(b"data")
            record = BackupRecord.objects.create(
                filename="good.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_run.return_value = MagicMock()

            result = verify_backup_full(record)

            assert result is True
            record.refresh_from_db()
            assert record.full_verified_ok is True
            assert record.full_verified_at is not None
            # не мала чіпати легку перевірку
            assert record.verified_ok is None

    @patch("backups.services.subprocess.run")
    def test_restore_failure_marks_full_verified_false(self, mock_run, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"data")
            record = BackupRecord.objects.create(
                filename="bad.dump", status=BackupRecord.Status.SUCCESS
            )

            # Мок має поводитись як реальний subprocess.run: check=False
            # (прибиральні виклики dropdb) ніколи не кидає CalledProcessError,
            # незалежно від коду виходу. Кидаємо тільки для check=True.
            def fake_run(*args, **kwargs):
                if kwargs.get("check"):
                    raise subprocess.CalledProcessError(1, "pg_restore")
                return MagicMock()

            mock_run.side_effect = fake_run

            result = verify_backup_full(record)

            assert result is False

    def test_skipped_for_already_failed_record(self, tmp_path):
        with patch("backups.services.subprocess.run") as mock_run:
            record = BackupRecord.objects.create(
                filename="x.dump", status=BackupRecord.Status.FAILED
            )

            result = verify_backup_full(record)

            assert result is False
            mock_run.assert_not_called()
