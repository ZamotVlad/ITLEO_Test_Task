import os
import subprocess
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from django.conf import settings

from accounts.models import User
from accounts.roles import Roles
from notifications.models import NotificationLog
from notifications.services import send_telegram_message

from .models import BackupRecord

BACKUP_DIR = Path(settings.BASE_DIR) / "backups_storage"

# Дамп великої бази може тривати довго - краще впасти з чіткою помилкою
# за таймаутом, ніж зависнути назавжди в cron-задачі.
DUMP_TIMEOUT = 600
RESTORE_TIMEOUT = 600


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
        record = BackupRecord.objects.create(
            filename=filename,
            status=BackupRecord.Status.FAILED,
            error_message=_extract_error(exc)[:2000],
            duration_seconds=time.monotonic() - started,
        )
        _notify_backup_failure("не вдалося створити дамп бази", record.error_message[:300])
        return record

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


def verify_backup_quick(record):
    """
    Легка щоденна перевірка: pg_restore --list читає лише заголовок архіву
    (список таблиць/об'єктів), не створює нічого в базі й не потребує
    прав CREATEDB. Доводить, що файл не пошкоджений і є валідним дампом.
    """
    if record.status != BackupRecord.Status.SUCCESS:
        return False

    file_path = BACKUP_DIR / record.filename
    if not file_path.exists():
        _save_quick_verification(record, ok=False)
        _notify_backup_failure("файл бекапу відсутній на диску", record.filename)
        return False

    try:
        subprocess.run(
            ["pg_restore", "--list", str(file_path)],
            check=True,
            capture_output=True,
            timeout=60,
        )
        ok = True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        ok = False

    _save_quick_verification(record, ok)
    if not ok:
        _notify_backup_failure(
            "легка перевірка не пройдена, файл може бути пошкоджений", record.filename
        )
    return ok


def verify_backup_full(record):
    """
    Важка перевірка: реально відновлює бекап у тимчасову базу і перевіряє,
    що процес пройшов без помилок. Тимчасова база видаляється незалежно
    від результату. Потребує прав CREATEDB на застосунковому користувачі.
    """
    if record.status != BackupRecord.Status.SUCCESS:
        return False

    file_path = BACKUP_DIR / record.filename
    if not file_path.exists():
        _save_full_verification(record, ok=False)
        _notify_backup_failure("файл бекапу відсутній на диску", record.filename)
        return False

    host, port, user, password, dbname = _db_settings()
    env = _env_with_password(password)
    test_db_name = f"{dbname}_verify_test"

    ok = True
    try:
        _run_quiet(["dropdb", "-h", host, "-p", port, "-U", user, "--if-exists", test_db_name], env)
        subprocess.run(
            ["createdb", "-h", host, "-p", port, "-U", user, test_db_name],
            env=env,
            check=True,
            capture_output=True,
            timeout=60,
        )
        subprocess.run(
            ["pg_restore", "-h", host, "-p", port, "-U", user, "-d", test_db_name, str(file_path)],
            env=env,
            check=True,
            capture_output=True,
            timeout=RESTORE_TIMEOUT,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        ok = False
    finally:
        _run_quiet(["dropdb", "-h", host, "-p", port, "-U", user, "--if-exists", test_db_name], env)

    _save_full_verification(record, ok)
    if not ok:
        _notify_backup_failure("повна перевірка відновлення не пройдена", record.filename)
    return ok


def _run_quiet(command, env):
    subprocess.run(command, env=env, check=False, capture_output=True, timeout=60)


def _save_quick_verification(record, ok):
    record.verified_at = datetime.now(tz=timezone.utc)
    record.verified_ok = ok
    record.save(update_fields=["verified_at", "verified_ok"])


def _save_full_verification(record, ok):
    record.full_verified_at = datetime.now(tz=timezone.utc)
    record.full_verified_ok = ok
    record.save(update_fields=["full_verified_at", "full_verified_ok"])


def _notify_backup_failure(reason, detail):
    """
    Сповіщає в Telegram усіх користувачів з роллю owner, у кого заповнений
    telegram_chat_id. Використовує ту саму інфраструктуру, що й
    notifications/services.py, щоб не дублювати логіку відправки.
    """
    owners = User.objects.filter(role=Roles.OWNER, telegram_chat_id__isnull=False)
    text = f"⚠️ Бекап бази ITLEO: {reason}\n{detail}"

    for owner in owners:
        success = send_telegram_message(owner.telegram_chat_id, text)
        NotificationLog.objects.create(
            type="telegram",
            notification_type="backup_failed",
            recipient=str(owner.telegram_chat_id),
            message=text,
            status="sent" if success else "failed",
        )
