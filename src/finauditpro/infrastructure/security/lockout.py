"""Failed authentication attempt tracker and automatic 15-minute brute-force lockout manager."""

import contextlib
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from finauditpro.domain.exceptions import ValidationError
from finauditpro.infrastructure.first_run import get_app_data_dir

# Process-level state (immune to filesystem deletion within the application session)
_FAILED_ATTEMPTS: int = 0
_LOCKOUT_UNTIL: datetime | None = None
_LOCKOUT_INTEGRITY_SALT = b"FinAuditPro-Lockout-Integrity-v1"


def _get_lockout_file_path() -> Path:
    return get_app_data_dir() / "lockout.json"


def _compute_hmac(data_str: str) -> str:
    return hmac.new(
        _LOCKOUT_INTEGRITY_SALT, data_str.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def check_lockout() -> None:
    """Check if the system is locked out. Raise ValidationError if locked. Fails closed on tampering."""
    global _LOCKOUT_UNTIL, _FAILED_ATTEMPTS
    now = datetime.now(UTC)

    # 1. Check in-process memory state first
    if _LOCKOUT_UNTIL is not None:
        if now < _LOCKOUT_UNTIL:
            remaining = int((_LOCKOUT_UNTIL - now).total_seconds())
            raise ValidationError(
                f"Account locked out due to too many failed attempts. Please try again in {remaining} seconds."
            )
        # Cooldown expired in memory
        _LOCKOUT_UNTIL = None
        _FAILED_ATTEMPTS = 0

    # 2. Check persistent state file
    lockout_file = _get_lockout_file_path()
    if not lockout_file.exists():
        return

    try:
        raw_text = lockout_file.read_text(encoding="utf-8")
        payload = json.loads(raw_text)

        # Integrity verification
        stored_hmac = payload.get("hmac")
        attempts = payload.get("attempts", 0)
        lockout_until_str = payload.get("lockout_until")

        body_str = f"{attempts}:{lockout_until_str}"
        expected_hmac = _compute_hmac(body_str)

        if not stored_hmac or not hmac.compare_digest(stored_hmac, expected_hmac):
            # Fail closed on tampering or corruption
            _LOCKOUT_UNTIL = now + timedelta(minutes=15)
            raise ValidationError(
                "Security state integrity violation: Authentication lockout file was tampered with. System locked for 15 minutes."
            )

        if lockout_until_str:
            lockout_until = datetime.fromisoformat(lockout_until_str)
            if now < lockout_until:
                _LOCKOUT_UNTIL = lockout_until
                _FAILED_ATTEMPTS = max(_FAILED_ATTEMPTS, attempts)
                remaining = int((lockout_until - now).total_seconds())
                raise ValidationError(
                    f"Account locked out due to too many failed attempts. Please try again in {remaining} seconds."
                )
    except (json.JSONDecodeError, ValueError) as ex:
        if isinstance(ex, ValidationError):
            raise
        # Fail closed on corrupted JSON
        _LOCKOUT_UNTIL = now + timedelta(minutes=15)
        raise ValidationError(
            "Security state corruption detected. Authentication temporarily locked for 15 minutes."
        ) from ex


def record_failed_attempt() -> None:
    """Increment failed login attempts. Trigger 15-minute lockout at 5 failed attempts."""
    global _FAILED_ATTEMPTS, _LOCKOUT_UNTIL
    now = datetime.now(UTC)

    # 1. Update in-memory counter
    _FAILED_ATTEMPTS += 1

    # 2. Check existing file to sync across instances if present
    lockout_file = _get_lockout_file_path()
    file_attempts = 0
    if lockout_file.exists():
        with contextlib.suppress(Exception):
            payload = json.loads(lockout_file.read_text(encoding="utf-8"))
            body_str = f"{payload.get('attempts')}:{payload.get('lockout_until')}"
            if hmac.compare_digest(payload.get("hmac", ""), _compute_hmac(body_str)):
                file_attempts = payload.get("attempts", 0)

    effective_attempts = max(_FAILED_ATTEMPTS, file_attempts + 1)
    _FAILED_ATTEMPTS = effective_attempts

    lockout_until_str = None
    if effective_attempts >= 5:
        _LOCKOUT_UNTIL = now + timedelta(minutes=15)
        lockout_until_str = _LOCKOUT_UNTIL.isoformat()

    body_str = f"{effective_attempts}:{lockout_until_str}"
    data = {
        "attempts": effective_attempts,
        "lockout_until": lockout_until_str,
        "hmac": _compute_hmac(body_str),
    }

    lockout_file.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(lockout_file, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(data))


def clear_failed_attempts() -> None:
    """Reset failed login attempts to zero."""
    global _FAILED_ATTEMPTS, _LOCKOUT_UNTIL
    _FAILED_ATTEMPTS = 0
    _LOCKOUT_UNTIL = None
    lockout_file = _get_lockout_file_path()
    if lockout_file.exists():
        with contextlib.suppress(Exception):
            lockout_file.unlink()

