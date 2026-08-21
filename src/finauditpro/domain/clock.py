"""Deterministic time provider module."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current time in UTC with timezone awareness.

    Always use this helper instead of datetime.now() or datetime.utcnow().
    """
    return datetime.now(UTC)
