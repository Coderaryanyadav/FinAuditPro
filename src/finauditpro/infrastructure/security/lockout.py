"""Failed authentication attempt tracker and automatic 15-minute brute-force lockout manager."""

import contextlib
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.first_run import get_app_data_dir


def _get_lockout_file_path() -> Path:
    return get_app_data_dir() / "lockout.json"


def check_lockout() -> None:
    """Check if the system is locked out. Raise ValidationError if locked."""
    lockout_file = _get_lockout_file_path()
    if not lockout_file.exists():
        return

    try:
        data = json.loads(lockout_file.read_text(encoding="utf-8"))
        lockout_until_str = data.get("lockout_until")

        if lockout_until_str:
            lockout_until = datetime.fromisoformat(lockout_until_str)
            now = datetime.now(UTC)
            if now < lockout_until:
                remaining = int((lockout_until - now).total_seconds())
                raise ValidationError(
                    f"Account locked out due to too many failed attempts. Please try again in {remaining} seconds."
                )
    except (json.JSONDecodeError, ValueError) as ex:
        if isinstance(ex, ValidationError):
            raise
        pass


def record_failed_attempt() -> None:
    """Increment failed login attempts. Trigger 15-minute lockout at 5 failed attempts."""
    lockout_file = _get_lockout_file_path()
    attempts = 0
    lockout_until = None

    if lockout_file.exists():
        with contextlib.suppress(Exception):
            data = json.loads(lockout_file.read_text(encoding="utf-8"))
            attempts = data.get("attempts", 0)

    attempts += 1
    if attempts >= 5:
        lockout_until = (datetime.now(UTC) + timedelta(minutes=15)).isoformat()

    data = {
        "attempts": attempts,
        "lockout_until": lockout_until,
    }

    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(lockout_file, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(data))


def clear_failed_attempts() -> None:
    """Reset failed login attempts to zero."""
    lockout_file = _get_lockout_file_path()
    if lockout_file.exists():
        with contextlib.suppress(Exception):
            lockout_file.unlink()
