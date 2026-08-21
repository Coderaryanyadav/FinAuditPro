"""Domain entities and state machine for Working Papers, Review Notes, and Sign-offs."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import DomainBaseModel
from finauditpro.domain.exceptions import InvalidStateTransitionError, ValidationError


class WorkingPaperStatusEnum(StrEnum):
    DRAFT = "Draft"
    IN_PREPARATION = "In Preparation"
    SUBMITTED_FOR_REVIEW = "Submitted for Review"
    UNDER_REVIEW = "Under Review"
    REVIEW_NOTES_OPEN = "Review Notes Open"
    REWORKING = "Reworking"
    REVIEWED = "Reviewed"
    SIGNED_OFF = "Signed Off"
    LOCKED = "Locked"
    REOPENED = "Reopened"


class ReviewNoteStatusEnum(StrEnum):
    OPEN = "Open"
    RESPONDED = "Responded"
    CLEARED = "Cleared"
    REOPENED = "Reopened"


class SignOffLevelEnum(StrEnum):
    PREPARED = "Prepared"
    REVIEWED = "Reviewed"
    FINAL_SIGN_OFF = "Signed Off"


# Non-statutory guidance disclaimer for working paper index structures and retention rules
DEFAULT_WORKING_PAPER_INDEX_GUIDANCE = {
    "source": "SA 230 Guidance & ICAI Practice Manual (Editable Suggestion)",
    "effective_from": "2025-04-01",
    "verified_statutory": False,
    "suggested_areas": [
        "A. Audit Planning & Materiality",
        "B. Internal Control Evaluation",
        "C. Revenue & Receivables",
        "D. Purchases & Payables",
        "E. Cash, Bank & Borrowings",
        "F. Statutory Liabilities & Taxes",
        "G. Fixed Assets & Depreciation",
        "H. Final Accounts & Disclosure Notes",
    ],
    "suggested_retention_years": 7,
    "disclaimer": "Working paper structures and retention policies are firm-configurable policies guided by SA 230, not locked statutory rules.",
}


LEGAL_WP_TRANSITIONS: dict[WorkingPaperStatusEnum, set[WorkingPaperStatusEnum]] = {
    WorkingPaperStatusEnum.DRAFT: {WorkingPaperStatusEnum.IN_PREPARATION, WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
    WorkingPaperStatusEnum.IN_PREPARATION: {WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW, WorkingPaperStatusEnum.DRAFT, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
    WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW: {WorkingPaperStatusEnum.UNDER_REVIEW, WorkingPaperStatusEnum.REVIEW_NOTES_OPEN, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
    WorkingPaperStatusEnum.UNDER_REVIEW: {WorkingPaperStatusEnum.REVIEW_NOTES_OPEN, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
    WorkingPaperStatusEnum.REVIEW_NOTES_OPEN: {WorkingPaperStatusEnum.REWORKING, WorkingPaperStatusEnum.UNDER_REVIEW},
    WorkingPaperStatusEnum.REWORKING: {WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW, WorkingPaperStatusEnum.UNDER_REVIEW, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
    WorkingPaperStatusEnum.REVIEWED: {WorkingPaperStatusEnum.SIGNED_OFF, WorkingPaperStatusEnum.UNDER_REVIEW, WorkingPaperStatusEnum.LOCKED},
    WorkingPaperStatusEnum.SIGNED_OFF: {WorkingPaperStatusEnum.LOCKED, WorkingPaperStatusEnum.REOPENED},
    WorkingPaperStatusEnum.LOCKED: {WorkingPaperStatusEnum.REOPENED},
    WorkingPaperStatusEnum.REOPENED: {WorkingPaperStatusEnum.IN_PREPARATION, WorkingPaperStatusEnum.UNDER_REVIEW, WorkingPaperStatusEnum.DRAFT, WorkingPaperStatusEnum.REVIEWED, WorkingPaperStatusEnum.SIGNED_OFF},
}


class WorkingPaperSection(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    working_paper_id: str = Field(...)
    section_order: int = Field(default=1)
    title: str = Field(..., min_length=1)
    content_markdown: str = Field(default="")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class ReviewNote(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    working_paper_id: str = Field(...)
    section_id: str | None = Field(default=None)
    raised_by: str = Field(..., min_length=1)
    note_text: str = Field(..., min_length=1)
    status: ReviewNoteStatusEnum = Field(default=ReviewNoteStatusEnum.OPEN)
    response_text: str | None = Field(default=None)
    responded_by: str | None = Field(default=None)
    cleared_by: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def respond(self, response_text: str, responder: str) -> None:
        if not response_text or not response_text.strip():
            raise ValidationError("Response text cannot be empty.")
        self.response_text = response_text.strip()
        self.responded_by = responder
        self.status = ReviewNoteStatusEnum.RESPONDED
        self.updated_at = utc_now()

    def clear(self, reviewer: str) -> None:
        self.cleared_by = reviewer
        self.status = ReviewNoteStatusEnum.CLEARED
        self.updated_at = utc_now()


class SignOffRecord(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    working_paper_id: str = Field(...)
    level: SignOffLevelEnum = Field(...)
    user_id: str = Field(..., min_length=1)
    user_role: str = Field(..., min_length=1)
    content_hash: str = Field(..., min_length=64, max_length=64)
    entry_hash: str | None = Field(default=None)
    note: str | None = Field(default=None)
    disclaimer_notice: str = Field(
        default="Notice: This electronic sign-off is an internal workflow attestation and audit record. It is NOT an IT Act 2000 Class 3 PKI Digital Signature (DSC) and NOT an ICAI UDIN."
    )
    created_at: datetime = Field(default_factory=utc_now)


class WorkingPaper(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    index_reference: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    area: str = Field(..., min_length=1)
    status: WorkingPaperStatusEnum = Field(default=WorkingPaperStatusEnum.DRAFT)
    conclusion: str = Field(default="")
    preparer_id: str = Field(..., min_length=1)
    reviewer_id: str | None = Field(default=None)
    content_hash: str | None = Field(default=None)
    version: int = Field(default=1)
    is_locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def transition_to(self, new_status: WorkingPaperStatusEnum) -> None:
        allowed = LEGAL_WP_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                "WorkingPaper", self.status.value, new_status.value
            )
        self.status = new_status
        if new_status in (WorkingPaperStatusEnum.SIGNED_OFF, WorkingPaperStatusEnum.LOCKED):
            self.is_locked = True
        elif new_status == WorkingPaperStatusEnum.REOPENED:
            self.is_locked = False
            self.version += 1
        self.updated_at = utc_now()
