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

logger = logging.getLogger(__name__)

@dataclass
class SecurityAuditEntry:
    entry_id: str
    user_email: str
    role: str
    action: str
    details: str
    machine_id: str = field(default_factory=lambda: platform.node())
    ip_address: str = field(default_factory=lambda: socket.gethostname())
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

    def log_action(self, user_email: str, role: str, action: str, details: str = "") -> SecurityAuditEntry:
        """Log an immutable security audit entry into the ledger."""
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
        return entry

    def verify_ledger_integrity(self) -> bool:
        """Verifies hash chain integrity across all audit log entries."""
        if not self.ledger:
            return True

        expected_prev_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        for entry in self.ledger:
            if entry.previous_hash != expected_prev_hash:
                logger.error(f"Ledger tamper detected at entry {entry.entry_id}! Invalid previous hash.")
                return False

            # Verify entry hash
            payload = f"{entry.entry_id}:{entry.user_email}:{entry.action}:{entry.timestamp.isoformat()}:{entry.previous_hash}"
            computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if computed != entry.entry_hash:
                logger.error(f"Ledger tamper detected at entry {entry.entry_id}! Entry hash mismatch.")
                return False

            expected_prev_hash = entry.entry_hash

        return True
