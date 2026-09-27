"""Domain entities and state machine for Working Papers, Review Notes, and Sign-offs."""

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import Field

from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import DomainBaseModel
from finauditpro.domain.exceptions import InvalidStateTransitionError, ValidationError


class FileCategoryEnum(StrEnum):
    PERMANENT_FILE = "Permanent File"
    CURRENT_FILE = "Current File"


class WorkingPaperStatusEnum(StrEnum):
    DRAFT = "Draft"
    PREPARED = "Prepared"
    SUBMITTED_FOR_REVIEW = "Submitted for Review"
    UNDER_REVIEW = "Under Review"
    RETURNED = "Returned"
    RESUBMITTED = "Resubmitted"
    APPROVED = "Approved"
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


# Permanent Audit File (PAF) Standard ICAI Structure
DEFAULT_PERMANENT_FILE_HEADS = [
    (
        "PAF-01",
        "Memorandum & Articles of Association (MOA & AOA)",
        "Legal Structure",
        "Permanent constitutional documents of the company.",
    ),
    (
        "PAF-02",
        "Tax Registrations (PAN, GSTIN, TAN, IEC Certificates)",
        "Statutory Registrations",
        "Permanent statutory registrations and tax identification numbers.",
    ),
    (
        "PAF-03",
        "Organization Structure & Key Management Personnel (KMP)",
        "Governance",
        "List of directors, board committees, and organizational chart.",
    ),
    (
        "PAF-04",
        "Long-Term Leases, Debt Instruments & Significant Contracts",
        "Agreements",
        "Major long-term agreements, title deeds, and loan agreements.",
    ),
    (
        "PAF-05",
        "Bank Account Details & Authorized Signatories",
        "Banking",
        "Permanent bank accounts, credit facilities, and authorized signatories.",
    ),
]

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
    WorkingPaperStatusEnum.DRAFT: {
        WorkingPaperStatusEnum.PREPARED,
        WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
    },
    WorkingPaperStatusEnum.PREPARED: {
        WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
        WorkingPaperStatusEnum.DRAFT,
    },
    WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW: {
        WorkingPaperStatusEnum.UNDER_REVIEW,
        WorkingPaperStatusEnum.RETURNED,
    },
    WorkingPaperStatusEnum.UNDER_REVIEW: {
        WorkingPaperStatusEnum.RETURNED,
        WorkingPaperStatusEnum.APPROVED,
    },
    WorkingPaperStatusEnum.RETURNED: {
        WorkingPaperStatusEnum.RESUBMITTED,
        WorkingPaperStatusEnum.DRAFT,
    },
    WorkingPaperStatusEnum.RESUBMITTED: {
        WorkingPaperStatusEnum.UNDER_REVIEW,
        WorkingPaperStatusEnum.RETURNED,
    },
    WorkingPaperStatusEnum.APPROVED: {
        WorkingPaperStatusEnum.LOCKED,
        WorkingPaperStatusEnum.UNDER_REVIEW,
    },
    WorkingPaperStatusEnum.LOCKED: {
        WorkingPaperStatusEnum.REOPENED,
    },
    WorkingPaperStatusEnum.REOPENED: {
        WorkingPaperStatusEnum.DRAFT,
        WorkingPaperStatusEnum.UNDER_REVIEW,
    },
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

    @property
    def author(self) -> str:
        return self.raised_by

    @property
    def timestamp(self) -> datetime:
        return self.created_at

    @property
    def target(self) -> str:
        return self.section_id or self.working_paper_id

    @property
    def comment(self) -> str:
        return self.note_text

    @property
    def response(self) -> str | None:
        return self.response_text

    @property
    def resolver(self) -> str | None:
        return self.cleared_by

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

    def reopen(self, reviewer: str, reason: str = "") -> None:
        self.status = ReviewNoteStatusEnum.REOPENED
        self.cleared_by = None
        if reason:
            self.note_text = f"{self.note_text}\n[Reopened by {reviewer}: {reason}]"
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
    file_category: FileCategoryEnum = Field(default=FileCategoryEnum.CURRENT_FILE)
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
        if self.is_locked and new_status != WorkingPaperStatusEnum.REOPENED:
            raise ValidationError("Working Paper is locked and cannot be modified or transitioned without reopening.")
        allowed = LEGAL_WP_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError("WorkingPaper", self.status.value, new_status.value)
        self.status = new_status
        if new_status == WorkingPaperStatusEnum.LOCKED:
            self.is_locked = True
        elif new_status == WorkingPaperStatusEnum.REOPENED:
            self.is_locked = False
            self.version += 1
        self.updated_at = utc_now()

    def approve(self, reviewer_id: str, role: str) -> None:
        """Domain action: Approve working paper under segregation of duties."""
        if self.is_locked:
            raise ValidationError("Working Paper is locked and cannot be modified.")
        if self.preparer_id == reviewer_id:
            raise ValidationError("Segregation of Duties Violation: Preparer cannot approve own workpaper.")
        if role not in ("Senior", "Manager", "Partner"):
            raise ValidationError("Unauthorized: Must be Senior, Manager, or Partner to approve.")
        self.reviewer_id = reviewer_id
        if self.status in (
            WorkingPaperStatusEnum.DRAFT,
            WorkingPaperStatusEnum.PREPARED,
            WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
        ):
            self.status = WorkingPaperStatusEnum.UNDER_REVIEW
        self.transition_to(WorkingPaperStatusEnum.APPROVED)

    def partner_sign_off(self, partner_id: str, role: str, content_hash: str) -> None:
        """Domain action: Final Partner Sign-off and cryptographic sealing under segregation of duties."""
        if self.is_locked:
            raise ValidationError("Working Paper is already locked.")
        if self.preparer_id == partner_id:
            raise ValidationError("Segregation of Duties Violation: Preparer cannot sign off own workpaper as Partner.")
        if role != "Partner":
            raise ValidationError("Unauthorized: Only Partners can perform final partner sign-off and locking.")
        self.content_hash = content_hash
        if self.status != WorkingPaperStatusEnum.APPROVED:
            self.status = WorkingPaperStatusEnum.APPROVED
        self.transition_to(WorkingPaperStatusEnum.LOCKED)
