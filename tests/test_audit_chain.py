"""Unit tests for SHA-256 hash-chained audit events and SQLite trigger enforcement."""

import pytest
from sqlalchemy import text

from finauditpro.domain.entities import AuditEvent
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository


def test_hash_chaining_and_verification(tmp_path) -> None:
    db_file = tmp_path / "test_chain.db"
    manager = DatabaseManager(db_path=db_file)
    manager.create_tables()

    with manager.session_scope() as session:
        repo = AuditEventRepository(session)

        ev1 = repo.add(AuditEvent(actor="Auditor 1", action="Created Firm", details="Firm A"))
        ev2 = repo.add(AuditEvent(actor="Auditor 1", action="Created Client", details="Client X"))
        ev3 = repo.add(
            AuditEvent(actor="Auditor 2", action="Created Engagement", details="FY 2025-26")
        )

        assert ev1.previous_hash == "GENESIS_HASH"
        assert ev2.previous_hash == ev1.entry_hash
        assert ev3.previous_hash == ev2.entry_hash

        # Verify full chain integrity
        assert repo.verify_chain() is True


def test_db_triggers_reject_update_and_delete(tmp_path) -> None:
    db_file = tmp_path / "test_triggers.db"
    manager = DatabaseManager(db_path=db_file)
    manager.create_tables()

    with manager.session_scope() as session:
        repo = AuditEventRepository(session)
        ev = repo.add(AuditEvent(actor="System", action="Test Trigger", details="Payload"))
        event_id = ev.id

    # Try updating audit event directly via raw SQL
    with pytest.raises(Exception) as excinfo, manager.engine.begin() as conn:
        conn.execute(
            text("UPDATE audit_events SET actor = 'Hacker' WHERE id = :id"), {"id": event_id}
        )
    assert "append-only" in str(excinfo.value).lower()

    # Try deleting audit event directly via raw SQL
    with pytest.raises(Exception) as excinfo2, manager.engine.begin() as conn:
        conn.execute(text("DELETE FROM audit_events WHERE id = :id"), {"id": event_id})
    assert "append-only" in str(excinfo2.value).lower()
