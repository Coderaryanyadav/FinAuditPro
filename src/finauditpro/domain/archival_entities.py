"""Pure domain entities for Engagement Archival, Retention Configs, and Reopen Audit Records."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class RetentionConfig(DomainBaseModel):
    """Configurable, versioned retention and assembly policy entity."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    version: str = Field(default="1.0")
    assembly_period_days: int = Field(default=60, ge=1)
    retention_period_years: int = Field(default=7, ge=1)
    source: str = Field(default="SA 230 Audit Documentation Standard Guidance (Firm Policy)")
    effective_from: str = Field(default="2025-04-01")
    verified_statutory: bool = Field(default=False)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class EngagementArchive(DomainBaseModel):
    """Sealed engagement archive entity containing cryptographic digests and storage paths."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    archive_path: str = Field(...)
    manifest_hash: str = Field(...)
    sealed_content_hash: str = Field(...)
    is_encrypted: bool = Field(default=False)
    report_date: str = Field(...)
    assembly_deadline: str = Field(...)
    retain_until: str = Field(...)
    sealed_by: str = Field(...)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class ArchiveReopenRecord(DomainBaseModel):
    """Audit record for a permissioned reopen operation of a previously sealed engagement archive."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    reopened_by: str = Field(...)
    reason: str = Field(...)
    prior_archive_id: str = Field(...)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
