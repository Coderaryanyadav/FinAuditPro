"""Repository managing persistence for Engagement Archives, Retention Configs, and Reopen Records."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.archival_entities import (
    ArchiveReopenRecord,
    EngagementArchive,
    RetentionConfig,
)
from finauditpro.infrastructure.persistence.archival_models import (
    ArchiveReopenRecordModel,
    EngagementArchiveModel,
    RetentionConfigModel,
)


class ArchivalRepository:
    """Repository handling persistence of engagement archives, retention policies, and reopen audits."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_archive_entity(self, model: EngagementArchiveModel) -> EngagementArchive:
        return EngagementArchive(
            id=model.id,
            engagement_id=model.engagement_id,
            archive_path=model.archive_path,
            manifest_hash=model.manifest_hash,
            sealed_content_hash=model.sealed_content_hash,
            is_encrypted=bool(model.is_encrypted),
            report_date=model.report_date,
            assembly_deadline=model.assembly_deadline,
            retain_until=model.retain_until,
            sealed_by=model.sealed_by,
            created_at=model.created_at,
        )

    def _to_retention_entity(self, model: RetentionConfigModel) -> RetentionConfig:
        return RetentionConfig(
            id=model.id,
            version=model.version,
            assembly_period_days=model.assembly_period_days,
            retention_period_years=model.retention_period_years,
            source=model.source,
            effective_from=model.effective_from,
            verified_statutory=bool(model.verified_statutory),
            created_at=model.created_at,
        )

    def _to_reopen_entity(self, model: ArchiveReopenRecordModel) -> ArchiveReopenRecord:
        return ArchiveReopenRecord(
            id=model.id,
            engagement_id=model.engagement_id,
            reopened_by=model.reopened_by,
            reason=model.reason,
            prior_archive_id=model.prior_archive_id,
            created_at=model.created_at,
        )

    def add_archive(self, archive: EngagementArchive) -> EngagementArchive:
        model = EngagementArchiveModel(
            id=archive.id,
            engagement_id=archive.engagement_id,
            archive_path=archive.archive_path,
            manifest_hash=archive.manifest_hash,
            sealed_content_hash=archive.sealed_content_hash,
            is_encrypted=int(archive.is_encrypted),
            report_date=archive.report_date,
            assembly_deadline=archive.assembly_deadline,
            retain_until=archive.retain_until,
            sealed_by=archive.sealed_by,
            created_at=archive.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_archive_entity(model)

    def get_latest_archive(self, engagement_id: str) -> EngagementArchive | None:
        stmt = (
            select(EngagementArchiveModel)
            .where(EngagementArchiveModel.engagement_id == engagement_id)
            .order_by(EngagementArchiveModel.created_at.desc())
            .limit(1)
        )
        model = self.session.scalars(stmt).first()
        return self._to_archive_entity(model) if model else None

    def list_archives_for_engagement(self, engagement_id: str) -> list[EngagementArchive]:
        stmt = (
            select(EngagementArchiveModel)
            .where(EngagementArchiveModel.engagement_id == engagement_id)
            .order_by(EngagementArchiveModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_archive_entity(m) for m in models]

    def save_retention_config(self, cfg: RetentionConfig) -> RetentionConfig:
        model = RetentionConfigModel(
            id=cfg.id,
            version=cfg.version,
            assembly_period_days=cfg.assembly_period_days,
            retention_period_years=cfg.retention_period_years,
            source=cfg.source,
            effective_from=cfg.effective_from,
            verified_statutory=int(cfg.verified_statutory),
            created_at=cfg.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_retention_entity(model)

    def get_active_retention_config(self) -> RetentionConfig | None:
        stmt = select(RetentionConfigModel).order_by(RetentionConfigModel.created_at.desc()).limit(1)
        model = self.session.scalars(stmt).first()
        return self._to_retention_entity(model) if model else None

    def add_reopen_record(self, record: ArchiveReopenRecord) -> ArchiveReopenRecord:
        model = ArchiveReopenRecordModel(
            id=record.id,
            engagement_id=record.engagement_id,
            reopened_by=record.reopened_by,
            reason=record.reason,
            prior_archive_id=record.prior_archive_id,
            created_at=record.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_reopen_entity(model)

    def list_reopen_records(self, engagement_id: str) -> list[ArchiveReopenRecord]:
        stmt = (
            select(ArchiveReopenRecordModel)
            .where(ArchiveReopenRecordModel.engagement_id == engagement_id)
            .order_by(ArchiveReopenRecordModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_reopen_entity(m) for m in models]
