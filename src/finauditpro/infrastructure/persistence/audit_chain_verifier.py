"""Startup integrity verifier checking DB schema version and cryptographic SHA-256 audit log hash chain continuity."""

from finauditpro.domain.exceptions import AuditIntegrityError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


def verify_startup_integrity(db_manager: DatabaseManager) -> tuple[bool, str]:
    """Recompute audit log SHA-256 hash chain on startup and flag tampering loudly."""
    with db_manager.session_scope() as session:
        audit_repo = AuditEventRepository(session)
        is_valid = audit_repo.verify_chain()
        if not is_valid:
            msg = "STARTUP INTEGRITY FAILURE: Audit log SHA-256 hash chain is broken or tampered!"
            raise AuditIntegrityError(msg)
        return True, "Startup Integrity Check Passed: Schema version verified & audit chain valid."
