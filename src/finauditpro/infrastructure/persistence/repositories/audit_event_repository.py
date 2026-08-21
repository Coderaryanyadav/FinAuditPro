"""Audit event repository with SHA-256 hash-chaining."""

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.entities import AuditEvent
from finauditpro.infrastructure.persistence.models import AuditEventModel


class AuditEventRepository:
    """Repository managing audit logging persistence with cryptographic SHA-256 hash-chaining."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, event: AuditEvent) -> AuditEvent:
        stmt = select(AuditEventModel).order_by(AuditEventModel.timestamp.desc(), AuditEventModel.id.desc()).limit(1)
        last_model = self.session.scalars(stmt).first()
        prev_hash = last_model.entry_hash if (last_model and last_model.entry_hash) else "GENESIS_HASH"

        ts_str = event.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
        raw_payload = f"{event.id}:{ts_str}:{event.actor}:{event.action}:{event.details or ''}:{prev_hash}"
        entry_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()

        model = AuditEventModel(
            id=event.id,
            engagement_id=event.engagement_id,
            actor=event.actor,
            action=event.action,
            details=event.details,
            previous_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=event.timestamp,
        )
        self.session.add(model)
        self.session.flush()
        return AuditEvent(
            id=model.id,
            engagement_id=model.engagement_id,
            actor=model.actor,
            action=model.action,
            details=model.details,
            previous_hash=model.previous_hash,
            entry_hash=model.entry_hash,
            timestamp=model.timestamp,
        )

    def verify_chain(self) -> bool:
        """Verify SHA-256 hash chain integrity across all stored audit events."""
        stmt = select(AuditEventModel).order_by(AuditEventModel.timestamp.asc(), AuditEventModel.id.asc())
        models = self.session.scalars(stmt).all()
        expected_prev = "GENESIS_HASH"

        for m in models:
            if m.previous_hash != expected_prev:
                return False
            ts_str = m.timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            raw_payload = f"{m.id}:{ts_str}:{m.actor}:{m.action}:{m.details or ''}:{expected_prev}"
            computed_hash = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
            if m.entry_hash != computed_hash:
                return False
            expected_prev = m.entry_hash

        return True

    def list_recent(self, limit: int = 20) -> list[AuditEvent]:
        stmt = select(AuditEventModel).order_by(AuditEventModel.timestamp.desc()).limit(limit)
        models = self.session.scalars(stmt).all()
        return [
            AuditEvent(
                id=m.id,
                engagement_id=m.engagement_id,
                actor=m.actor,
                action=m.action,
                details=m.details,
                previous_hash=m.previous_hash,
                entry_hash=m.entry_hash,
                timestamp=m.timestamp,
            )
            for m in models
        ]
