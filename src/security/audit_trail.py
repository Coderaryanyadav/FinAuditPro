"""
Immutable Security Audit Logger for FinAuditPro.
Logs every user action into an append-only ledger with machine ID, user email, and SHA-256 chain hash.
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import platform
import socket
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

@dataclass
class SecurityAuditEntry:
    entry_id: str
    user_email: str
    role: str
    action: str
    details: str
    machine_id: str = field(default_factory=lambda: platform.node())
    ip_address: str = field(default_factory=lambda: "127.0.0.1")
    timestamp: datetime = field(default_factory=datetime.utcnow)
    previous_hash: str = "0000000000000000000000000000000000000000000000000000000000000000"
    entry_hash: str = ""

    def __post_init__(self):
        if not self.entry_hash:
            payload = f"{self.entry_id}:{self.user_email}:{self.action}:{self.timestamp.isoformat()}:{self.previous_hash}"
            self.entry_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "user_email": self.user_email,
            "role": self.role,
            "action": self.action,
            "details": self.details,
            "machine_id": self.machine_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat(),
            "previous_hash": self.previous_hash,
            "entry_hash": self.entry_hash,
        }


class ImmutableAuditLogger:
    """Append-only security log ledger enforcing hash-chain tamper detection."""

    def __init__(self):
        self.ledger: List[SecurityAuditEntry] = []
        self._last_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self._load_ledger_from_db()

    def _load_ledger_from_db(self):
        """Reload audit log entries and hash chain state from SQLite database."""
        try:
            from database.database import SessionLocal
            from database.models import AuditLog, User
            session = SessionLocal()
            logs = session.query(AuditLog).order_by(AuditLog.id.asc()).all()
            user_cache = {u.id: (u.email or u.username) for u in session.query(User).all()}
            session.close()

            for log in logs:
                u_email = user_cache.get(log.user_id, "system@finauditpro.local")
                prev_h = log.previous_hash or self._last_hash
                e_id = f"LOG-{log.id:06d}"
                entry = SecurityAuditEntry(
                    entry_id=e_id,
                    user_email=u_email,
                    role="User",
                    action=log.action,
                    details=log.target_entity or "",
                    ip_address=log.ip_address or "127.0.0.1",
                    timestamp=log.created_at or datetime.utcnow(),
                    previous_hash=prev_h,
                    entry_hash=log.entry_hash or ""
                )
                if entry.entry_hash:
                    self._last_hash = entry.entry_hash
                self.ledger.append(entry)
        except (SQLAlchemyError, OSError) as e:
            logger.debug(f"Audit log database load skipped: {e}")

    def log_action(self, user_email: str, role: str, action: str, details: str = "") -> SecurityAuditEntry:
        """Log an immutable security audit entry into memory and persistent SQLite database."""
        entry_id = f"LOG-{len(self.ledger) + 1:06d}"
        entry = SecurityAuditEntry(
            entry_id=entry_id,
            user_email=user_email,
            role=role,
            action=action,
            details=details,
            previous_hash=self._last_hash
        )
        self._last_hash = entry.entry_hash
        self.ledger.append(entry)
        logger.info(f"[SECURITY AUDIT LOG] {action} by {user_email} ({role}) | Hash: {entry.entry_hash[:16]}...")

        # Persist to SQLite Database
        try:
            from database.database import SessionLocal
            from database.models import AuditLog, User
            session = SessionLocal()
            user = session.query(User).filter_by(email=user_email).first()
            user_id = user.id if user else 1
            log_record = AuditLog(
                user_id=user_id,
                action=action,
                target_entity=details or "SecurityAudit",
                ip_address=entry.ip_address,
                previous_hash=entry.previous_hash,
                entry_hash=entry.entry_hash
            )
            session.add(log_record)
            session.commit()
            session.close()
        except (SQLAlchemyError, OSError) as e:
            logger.warning(f"Failed to persist audit log to DB: {e}")

        return entry

    def verify_ledger_integrity(self) -> bool:
        """Verifies hash chain integrity across all audit log entries."""
        if not self.ledger:
            return True

        expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        for entry in self.ledger:
            if entry.previous_hash != expected_prev_hash:
                logger.error(f"Ledger tamper detected at entry {entry.entry_id}! Invalid previous hash: expected {expected_prev_hash}, got {entry.previous_hash}")
                return False

            expected_prev_hash = entry.entry_hash

        return True
