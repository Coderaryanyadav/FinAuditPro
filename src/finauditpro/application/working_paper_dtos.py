from dataclasses import dataclass, field
from typing import Any

from finauditpro.domain.audit_matrix_entities import (
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
)
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    SignOffLevelEnum,
    SignOffRecord,
    WorkingPaper,
    WorkingPaperSection,
)


@dataclass(frozen=True)
class CreateWorkingPaperDTO:
    engagement_id: str
    index_reference: str
    title: str
    area: str
    file_category: str = "Current File"
    preparer_id: str = "Lead Auditor"
    reviewer_id: str | None = None
    procedure_ids: list[str] = field(default_factory=list)
    initial_sections: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateWorkingPaperDTO:
    working_paper_id: str
    title: str | None = None
    area: str | None = None
    conclusion: str | None = None
    sections: list[dict[str, str]] | None = None


@dataclass(frozen=True)
class CreateReviewNoteDTO:
    working_paper_id: str
    raised_by: str
    note_text: str
    section_id: str | None = None


@dataclass(frozen=True)
class RespondReviewNoteDTO:
    review_note_id: str
    response_text: str
    responder: str


@dataclass(frozen=True)
class ClearReviewNoteDTO:
    review_note_id: str
    reviewer: str


@dataclass(frozen=True)
class ReopenReviewNoteDTO:
    review_note_id: str
    reviewer: str
    reason: str = ""


@dataclass(frozen=True)
class SignOffDTO:
    working_paper_id: str
    level: SignOffLevelEnum | str
    user_id: str
    user_role: str
    note: str | None = None


@dataclass(frozen=True)
class ReopenWorkingPaperDTO:
    working_paper_id: str
    reopened_by: str
    reason: str


@dataclass(frozen=True)
class HistoricalVersionSnapshotDTO:
    id: str
    working_paper_id: str
    version: int
    title: str
    area: str
    status: str
    conclusion: str
    preparer_id: str
    reviewer_id: str | None
    content_hash: str | None
    sections: list[dict[str, Any]]
    created_at_iso: str


@dataclass
class WorkingPaperWorkbenchDTO:
    working_paper: WorkingPaper
    sections: list[WorkingPaperSection]
    objective: str
    risks: list[AuditRisk]
    assertions: list[str]
    procedures: list[AuditProcedure]
    population: str
    samples: list[dict[str, Any]]
    test_executions: list[dict[str, Any]]
    evidence_items: list[AuditEvidence]
    exceptions: list[dict[str, Any]]
    findings: list[AuditFinding]
    conclusion: str
    reviewer: str | None
    sign_offs: list[SignOffRecord]
    version: int
    open_review_notes_count: int
    review_notes: list[ReviewNote]
    historical_versions: list[HistoricalVersionSnapshotDTO]
    is_locked: bool
    content_hash: str | None
