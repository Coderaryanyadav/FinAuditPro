"""Data Transfer Objects (DTOs) for First-Class Audit Evidence Domain."""

from dataclasses import dataclass
from typing import Any

from finauditpro.domain.audit_matrix_entities import (
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    EvidenceStatusEnum,
)
from finauditpro.domain.working_paper_entities import WorkingPaper


@dataclass(frozen=True)
class CreateEvidenceDTO:
    engagement_id: str
    title: str
    excerpt_or_reference: str
    evidence_code: str = ""
    file_path: str | None = None
    source: str = "Uploaded Document"
    document_type: str = "General"
    location: str | None = None
    page_number: int | None = None
    row_index: int | None = None
    procedure_id: str | None = None
    working_paper_id: str | None = None
    finding_id: str | None = None
    sample_ref: str | None = None
    test_execution_id: str | None = None
    uploaded_by: str = "Auditor"


@dataclass(frozen=True)
class UpdateEvidenceStatusDTO:
    evidence_id: str
    target_status: EvidenceStatusEnum
    actor: str = "Auditor"
    actor_role: str = "Auditor"
    review_notes: str | None = None


@dataclass(frozen=True)
class LinkEvidenceDTO:
    evidence_id: str
    procedure_id: str | None = None
    working_paper_id: str | None = None
    finding_id: str | None = None
    sample_ref: str | None = None
    actor: str = "Auditor"


@dataclass
class EvidenceProvenanceDTO:
    evidence: AuditEvidence
    provenance_path: str
    working_paper: WorkingPaper | None = None
    procedure: AuditProcedure | None = None
    finding: AuditFinding | None = None
    sample_ref: str | None = None
    document_location: str | None = None
    hash_verified: bool = True


@dataclass
class EvidenceIntegrityReportDTO:
    evidence_id: str
    title: str
    stored_hash: str | None
    actual_hash: str | None
    is_valid: bool
    status: str
    details: str
