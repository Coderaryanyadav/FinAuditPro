"""SQLAlchemy ORM models for Engagement Archival, Retention Configs, and Reopen Records."""

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from finauditpro.infrastructure.persistence.database import Base


class EngagementArchiveModel(Base):
    """ORM Model representing a sealed, tamper-evident audit file archive."""

    __tablename__ = "engagement_archives"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    archive_path: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_hash: Mapped[str] = mapped_column(String, nullable=False)
    sealed_content_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_encrypted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    report_date: Mapped[str] = mapped_column(String, nullable=False)
    assembly_deadline: Mapped[str] = mapped_column(String, nullable=False)
    retain_until: Mapped[str] = mapped_column(String, nullable=False)
    sealed_by: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class RetentionConfigModel(Base):
    """ORM Model representing versioned, configurable retention and final assembly policies."""

    __tablename__ = "retention_configs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    version: Mapped[str] = mapped_column(String, nullable=False, default="1.0")
    assembly_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    retention_period_years: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    source: Mapped[str] = mapped_column(String, nullable=False)
    effective_from: Mapped[str] = mapped_column(String, nullable=False)
    verified_statutory: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String, nullable=False)


class ArchiveReopenRecordModel(Base):
    """ORM Model representing an audited reopen event of a previously sealed engagement archive."""

    __tablename__ = "archive_reopen_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    engagement_id: Mapped[str] = mapped_column(
        String, ForeignKey("engagements.id", ondelete="CASCADE"), nullable=False
    )
    reopened_by: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    prior_archive_id: Mapped[str] = mapped_column(
        String, ForeignKey("engagement_archives.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[str] = mapped_column(String, nullable=False)
