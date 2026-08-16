import subprocess
from unittest.mock import MagicMock, patch

import pytest

from accounts.models import User
from accounts.roles import Roles
from backups.models import BackupRecord
from backups.services import (
    _notify_backup_failure,
    create_backup,
    verify_backup_full,
    verify_backup_quick,
)
from notifications.models import NotificationLog


def _make_owner(username, chat_id=None):
    return User.objects.create(username=username, role=Roles.OWNER, telegram_chat_id=chat_id)


@pytest.mark.django_db
class TestNotifyBackupFailure:
    @patch("backups.services.send_telegram_message")
    def test_sends_only_to_owners_with_chat_id(self, mock_send):
        _make_owner("owner_with_chat", chat_id=111)
        _make_owner("owner_without_chat", chat_id=None)
        User.objects.create(username="manager1", role=Roles.MANAGER, telegram_chat_id=222)
        mock_send.return_value = True

        _notify_backup_failure("тестова причина", "деталі")

        mock_send.assert_called_once_with(111, "⚠️ Бекап бази ITLEO: тестова причина\nдеталі")

    @patch("backups.services.send_telegram_message")
    def test_logs_sent_status_on_success(self, mock_send):
        _make_owner("owner1", chat_id=111)
        mock_send.return_value = True

        _notify_backup_failure("причина", "деталі")

        log = NotificationLog.objects.get(notification_type="backup_failed")
        assert log.status == "sent"
        assert log.type == "telegram"
        assert log.recipient == "111"

    @patch("backups.services.send_telegram_message")
    def test_logs_failed_status_when_send_fails(self, mock_send):
        _make_owner("owner1", chat_id=111)
        mock_send.return_value = False

        _notify_backup_failure("причина", "деталі")

        log = NotificationLog.objects.get(notification_type="backup_failed")
        assert log.status == "failed"

    @patch("backups.services.send_telegram_message")
    def test_no_owners_sends_nothing(self, mock_send):
        _notify_backup_failure("причина", "деталі")

        mock_send.assert_not_called()
        assert not NotificationLog.objects.filter(notification_type="backup_failed").exists()


@pytest.mark.django_db
class TestFailureTriggersNotification:
    @patch("backups.services.send_telegram_message")
    @patch("backups.services.subprocess.run")
    def test_create_backup_failure_notifies_owner(self, mock_run, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            _make_owner("owner1", chat_id=111)
            mock_run.side_effect = subprocess.CalledProcessError(1, "pg_dump", stderr=b"boom")
            mock_send.return_value = True

            create_backup()

            mock_send.assert_called_once()

    @patch("backups.services.send_telegram_message")
    def test_verify_quick_missing_file_notifies_owner(self, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            _make_owner("owner1", chat_id=111)
            record = BackupRecord.objects.create(
                filename="missing.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_send.return_value = True

            verify_backup_quick(record)

            mock_send.assert_called_once()

    @patch("backups.services.send_telegram_message")
    @patch("backups.services.subprocess.run")
    def test_verify_quick_corrupted_notifies_owner(self, mock_run, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"data")
            _make_owner("owner1", chat_id=111)
            record = BackupRecord.objects.create(
                filename="bad.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_run.side_effect = subprocess.CalledProcessError(1, "pg_restore")
            mock_send.return_value = True

            verify_backup_quick(record)

            mock_send.assert_called_once()

    @patch("backups.services.send_telegram_message")
    def test_verify_full_missing_file_notifies_owner(self, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            _make_owner("owner1", chat_id=111)
            record = BackupRecord.objects.create(
                filename="missing.dump", status=BackupRecord.Status.SUCCESS
            )
            mock_send.return_value = True

            verify_backup_full(record)

            mock_send.assert_called_once()

    @patch("backups.services.send_telegram_message")
    @patch("backups.services.subprocess.run")
    def test_verify_full_restore_failure_notifies_owner(self, mock_run, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            (tmp_path / "bad.dump").write_bytes(b"data")
            _make_owner("owner1", chat_id=111)
            record = BackupRecord.objects.create(
                filename="bad.dump", status=BackupRecord.Status.SUCCESS
            )

            def fake_run(*args, **kwargs):
                if kwargs.get("check"):
                    raise subprocess.CalledProcessError(1, "pg_restore")
                return MagicMock()

            mock_run.side_effect = fake_run
            mock_send.return_value = True

            verify_backup_full(record)

            mock_send.assert_called_once()

    @patch("backups.services.send_telegram_message")
    @patch("backups.services.subprocess.run")
    def test_successful_backup_does_not_notify(self, mock_run, mock_send, tmp_path):
        with patch("backups.services.BACKUP_DIR", tmp_path):
            _make_owner("owner1", chat_id=111)

            def fake_dump(*args, **kwargs):
                output_path = args[0][args[0].index("-f") + 1]
                with open(output_path, "wb") as f:
                    f.write(b"data")
                return MagicMock()

            mock_run.side_effect = fake_dump

            create_backup()

            mock_send.assert_not_called()
