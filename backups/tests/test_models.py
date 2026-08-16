import pytest

from backups.models import BackupRecord


@pytest.mark.django_db
def test_str_shows_filename_and_status():
    record = BackupRecord.objects.create(
        filename="backup_test.dump", status=BackupRecord.Status.SUCCESS
    )

    assert str(record) == "backup_test.dump (success)"
