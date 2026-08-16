import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings

from .models import BackupRecord

BACKUP_DIR = Path(settings.BASE_DIR) / "backups_storage"

# Дамп великої бази може тривати довго - краще впасти з чіткою помилкою
# за таймаутом, ніж зависнути назавжди в cron-задачі.
DUMP_TIMEOUT = 600


def _db_settings():
    db = settings.DATABASES["default"]
    return db["HOST"], str(db["PORT"]), db["USER"], db["PASSWORD"], db["NAME"]


def _env_with_password(password):
    env = os.environ.copy()
    env["PGPASSWORD"] = password
    return env


def create_backup():
    """Створює новий дамп бази. Завжди записує результат (успіх чи помилку) в BackupRecord."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    host, port, user, password, dbname = _db_settings()

    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{timestamp}.dump"
    output_path = BACKUP_DIR / filename
    env = _env_with_password(password)

    started = time.monotonic()
    try:
        subprocess.run(
            ["pg_dump", "-Fc", "-h", host, "-p", port, "-U", user, "-f", str(output_path), dbname],
            env=env,
            check=True,
            capture_output=True,
            timeout=DUMP_TIMEOUT,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return BackupRecord.objects.create(
            filename=filename,
            status=BackupRecord.Status.FAILED,
            error_message=_extract_error(exc)[:2000],
            duration_seconds=time.monotonic() - started,
        )

    size = output_path.stat().st_size if output_path.exists() else None
    return BackupRecord.objects.create(
        filename=filename,
        status=BackupRecord.Status.SUCCESS,
        size_bytes=size,
        duration_seconds=time.monotonic() - started,
    )


def _extract_error(exc):
    stderr = getattr(exc, "stderr", None)
    if stderr:
        return stderr.decode(errors="replace") if isinstance(stderr, bytes) else str(stderr)
    return str(exc)


def prune_old_backups(keep_days=14):
    """Видаляє файли й записи успішних бекапів, старіші за keep_days."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=keep_days)
    old_records = BackupRecord.objects.filter(
        created_at__lt=cutoff, status=BackupRecord.Status.SUCCESS
    )

    removed = 0
    for record in old_records:
        file_path = BACKUP_DIR / record.filename
        if file_path.exists():
            file_path.unlink()
            removed += 1

    old_records.delete()
    return removed
