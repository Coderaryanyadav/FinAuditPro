"""Application DTOs for Working Papers, Review Notes, and Sign-offs."""

from dataclasses import dataclass, field

from finauditpro.domain.working_paper_entities import SignOffLevelEnum


@dataclass(frozen=True)
class CreateWorkingPaperDTO:
    engagement_id: str
    index_reference: str
    title: str
    area: str
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
