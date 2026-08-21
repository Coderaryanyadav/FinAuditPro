"""Application service managing Working Paper lifecycles, review notes, sign-offs, and integrity."""

import hashlib
import json
from uuid import uuid4

from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    ValidationError,
)
from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    SignOffLevelEnum,
    SignOffRecord,
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


class WorkingPaperService:
    """Service orchestrating Working Paper lifecycle, review points, sign-offs, and SHA-256 hash integrity."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def compute_content_hash(self, wp: WorkingPaper, sections: list[WorkingPaperSection], links: list[dict[str, str]]) -> str:
        """Compute deterministic SHA-256 digest of working paper content and linked evidence."""
        payload = {
            "id": wp.id,
            "engagement_id": wp.engagement_id,
            "index_reference": wp.index_reference,
            "title": wp.title,
            "area": wp.area,
            "conclusion": wp.conclusion,
            "preparer_id": wp.preparer_id,
            "version": wp.version,
            "sections": [{"title": s.title, "content": s.content_markdown} for s in sections],
            "links": sorted([{"type": l["link_type"], "target": l["target_id"]} for l in links], key=lambda x: (x["type"], x["target"])),
        }
        json_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()

    def create_working_paper(self, dto: CreateWorkingPaperDTO) -> WorkingPaper:
        """Create a new Working Paper with initial sections and linked procedure IDs."""
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            wp_repo = WorkingPaperRepository(session)
            wp = WorkingPaper(
                engagement_id=dto.engagement_id,
                index_reference=dto.index_reference,
                title=dto.title,
                area=dto.area,
                status=WorkingPaperStatusEnum.DRAFT,
                preparer_id=dto.preparer_id,
                reviewer_id=dto.reviewer_id,
            )
            saved_wp = wp_repo.add_working_paper(wp)

            # Add initial sections
            if dto.initial_sections:
                for idx, sec_data in enumerate(dto.initial_sections, start=1):
                    sec = WorkingPaperSection(
                        working_paper_id=saved_wp.id,
                        section_order=idx,
                        title=sec_data.get("title", f"Section {idx}"),
                        content_markdown=sec_data.get("content", ""),
                    )
                    wp_repo.add_section(sec)
            else:
                # Default standard sections
                wp_repo.add_section(WorkingPaperSection(working_paper_id=saved_wp.id, section_order=1, title="1. Objective & Scope", content_markdown="Document audit procedure objectives."))
                wp_repo.add_section(WorkingPaperSection(working_paper_id=saved_wp.id, section_order=2, title="2. Work Done & Testing Summary", content_markdown="Detail substantive sample testing."))
                wp_repo.add_section(WorkingPaperSection(working_paper_id=saved_wp.id, section_order=3, title="3. Conclusion", content_markdown="Auditor conclusion."))

            # Link procedures
            for proc_id in dto.procedure_ids:
                wp_repo.add_link(str(uuid4()), saved_wp.id, "procedure", proc_id)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.preparer_id,
                    action="Working Paper Created",
                    details=f"Created Working Paper '{saved_wp.index_reference}': {saved_wp.title}",
                )
            )

            return saved_wp

    def get_working_paper(self, wp_id: str) -> WorkingPaper:
        """Fetch working paper by ID."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            return wp

    def list_working_papers(self, engagement_id: str) -> list[WorkingPaper]:
        """List all working papers for an engagement."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            return wp_repo.list_for_engagement(engagement_id)

    def count_open_review_notes(self, wp_id: str) -> int:
        """Count open review notes on a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            return wp_repo.count_open_review_notes(wp_id)

    def list_review_notes(self, wp_id: str) -> list[ReviewNote]:
        """List all review notes on a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            return wp_repo.list_review_notes(wp_id)

    def submit_for_review(self, wp_id: str, submitter_id: str) -> WorkingPaper:
        """Submit working paper for manager/partner review."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)

            wp.transition_to(WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW)
            updated = wp_repo.update_working_paper(wp)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=submitter_id,
                    action="Working Paper Submitted For Review",
                    details=f"Submitted Working Paper '{wp.index_reference}' for review",
                )
            )
            return updated

    def raise_review_note(self, dto: CreateReviewNoteDTO) -> ReviewNote:
        """Raise a new review point on a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)

            note = ReviewNote(
                working_paper_id=dto.working_paper_id,
                section_id=dto.section_id,
                raised_by=dto.raised_by,
                note_text=dto.note_text,
                status=ReviewNoteStatusEnum.OPEN,
            )
            saved_note = wp_repo.add_review_note(note)

            # Update working paper status to Review Notes Open
            if wp.status != WorkingPaperStatusEnum.REVIEW_NOTES_OPEN:
                wp.status = WorkingPaperStatusEnum.REVIEW_NOTES_OPEN
                wp_repo.update_working_paper(wp)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.raised_by,
                    action="Review Note Raised",
                    details=f"Raised review note on '{wp.index_reference}': {dto.note_text[:60]}",
                )
            )
            return saved_note

    def respond_review_note(self, dto: RespondReviewNoteDTO) -> ReviewNote:
        """Preparer responds to a review note."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            from finauditpro.infrastructure.persistence.working_paper_models import ReviewNoteModel
            n_model = session.get(ReviewNoteModel, dto.review_note_id)
            if not n_model:
                raise EntityNotFoundError("ReviewNote", dto.review_note_id)

            note = ReviewNote(
                id=n_model.id,
                working_paper_id=n_model.working_paper_id,
                section_id=n_model.section_id,
                raised_by=n_model.raised_by,
                note_text=n_model.note_text,
                status=ReviewNoteStatusEnum(n_model.status),
            )
            note.respond(dto.response_text, dto.responder)
            saved = wp_repo.update_review_note(note)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id="",
                    actor=dto.responder,
                    action="Review Note Responded",
                    details=f"Responded to review note '{saved.id}'",
                )
            )
            return saved

    def clear_review_note(self, dto: ClearReviewNoteDTO) -> ReviewNote:
        """Reviewer clears a review note."""
        with self.db_manager.session_scope() as session:
            from finauditpro.infrastructure.persistence.working_paper_models import ReviewNoteModel
            n_model = session.get(ReviewNoteModel, dto.review_note_id)
            if not n_model:
                raise EntityNotFoundError("ReviewNote", dto.review_note_id)

            note = ReviewNote(
                id=n_model.id,
                working_paper_id=n_model.working_paper_id,
                section_id=n_model.section_id,
                raised_by=n_model.raised_by,
                note_text=n_model.note_text,
                status=ReviewNoteStatusEnum(n_model.status),
            )
            note.clear(dto.reviewer)
            wp_repo = WorkingPaperRepository(session)
            saved = wp_repo.update_review_note(note)

            # If all notes are cleared, transition paper status to Under Review
            if wp_repo.count_open_review_notes(note.working_paper_id) == 0:
                wp = wp_repo.get_working_paper(note.working_paper_id)
                if wp and wp.status in (WorkingPaperStatusEnum.REVIEW_NOTES_OPEN, WorkingPaperStatusEnum.REWORKING):
                    wp.status = WorkingPaperStatusEnum.UNDER_REVIEW
                    wp_repo.update_working_paper(wp)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id="",
                    actor=dto.reviewer,
                    action="Review Note Cleared",
                    details=f"Cleared review note '{saved.id}'",
                )
            )
            return saved

    def sign_off_working_paper(self, dto: SignOffDTO) -> SignOffRecord:
        """Sign off working paper, enforcing Open-Notes Control and Segregation of Duties."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)

            if wp.is_locked:
                raise ValidationError(f"Working Paper '{wp.index_reference}' is locked and cannot be signed off.")

            # Hard Control 1: Open Review Notes Blocking Control
            open_notes = wp_repo.count_open_review_notes(wp.id)
            if open_notes > 0:
                raise ValidationError(
                    f"Audit Quality Violation: Cannot sign off Working Paper '{wp.index_reference}' while {open_notes} open or uncleared review notes exist."
                )

            # Hard Control 2: Segregation of Duties
            if dto.level == SignOffLevelEnum.FINAL_SIGN_OFF:
                if wp.preparer_id == dto.user_id:
                    raise ValidationError(
                        f"Segregation of Duties Violation: Preparer '{wp.preparer_id}' cannot perform final sign-off on their own working paper."
                    )

            sections = wp_repo.get_sections(wp.id)
            links = wp_repo.get_links(wp.id)
            chash = self.compute_content_hash(wp, sections, links)
            wp.content_hash = chash

            # State transition
            if dto.level == SignOffLevelEnum.REVIEWED:
                wp.transition_to(WorkingPaperStatusEnum.REVIEWED)
            else:
                wp.transition_to(WorkingPaperStatusEnum.SIGNED_OFF)
                wp.is_locked = True

            wp_repo.update_working_paper(wp)

            signoff = SignOffRecord(
                working_paper_id=wp.id,
                level=dto.level,
                user_id=dto.user_id,
                user_role=dto.user_role,
                content_hash=chash,
                note=dto.note,
            )
            saved_signoff = wp_repo.add_sign_off(signoff)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.user_id,
                    action=f"Working Paper {dto.level.value}",
                    details=f"Signed off '{wp.index_reference}' ({dto.level.value}) by {dto.user_role} {dto.user_id}. Content Hash: {chash[:16]}...",
                )
            )
            return saved_signoff

    def verify_integrity(self, wp_id: str) -> tuple[bool, str]:
        """Recalculate content hash and detect tampering on signed working papers."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)

            if not wp.content_hash:
                return True, "Working paper has not been signed off yet."

            sections = wp_repo.get_sections(wp.id)
            links = wp_repo.get_links(wp.id)
            recalculated = self.compute_content_hash(wp, sections, links)

            if recalculated == wp.content_hash:
                return True, f"Integrity Verified: Content hash matches signed hash ({wp.content_hash[:16]}...)"

            return False, f"TAMPER ALERT: Content hash mismatch! Stored: {wp.content_hash[:16]}, Recalculated: {recalculated[:16]}"

    def reopen_working_paper(self, dto: ReopenWorkingPaperDTO) -> WorkingPaper:
        """Reopen a locked/signed working paper with permissioned audit trail and version increment."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)

            wp.transition_to(WorkingPaperStatusEnum.REOPENED)
            updated = wp_repo.update_working_paper(wp)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.reopened_by,
                    action="Working Paper Reopened",
                    details=f"Reopened Working Paper '{wp.index_reference}' (v{wp.version}). Reason: {dto.reason}",
                )
            )
            return updated
