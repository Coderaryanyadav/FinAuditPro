"""Application service managing Working Paper lifecycles, review notes, sign-offs, and integrity."""

import hashlib
import json
from uuid import uuid4

from finauditpro.application.services.working_paper_scaffolder import (
    archive_working_paper_version,
    resolve_user_role,
    scaffold_permanent_audit_file,
    scaffold_schedule_iii_working_papers,
)
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.domain.working_paper_entities import (
    FileCategoryEnum,
    ReviewNote,
    ReviewNoteStatusEnum,
    SignOffLevelEnum,
    SignOffRecord,
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import EngagementMemberModel, UserModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.working_paper_models import (
    ReviewNoteModel,
    WorkingPaperSectionModel,
)


class WorkingPaperService:
    """Service orchestrating Working Paper lifecycle, review points, sign-offs, and SHA-256 hash integrity."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def compute_content_hash(
        self,
        wp: WorkingPaper,
        sections: list[WorkingPaperSection],
        links: list[dict[str, str]],
    ) -> str:
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
            "links": sorted(
                [{"type": l["link_type"], "target": l["target_id"]} for l in links],
                key=lambda x: (x["type"], x["target"]),
            ),
        }
        json_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(json_bytes).hexdigest()

    def create_working_paper(self, dto: CreateWorkingPaperDTO) -> WorkingPaper:
        """Create a new Working Paper with initial sections and linked procedure IDs."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            try:
                f_cat = FileCategoryEnum(dto.file_category)
            except Exception:
                f_cat = FileCategoryEnum.CURRENT_FILE

            wp_repo = WorkingPaperRepository(session)
            wp = WorkingPaper(
                engagement_id=dto.engagement_id,
                index_reference=dto.index_reference,
                title=dto.title,
                area=dto.area,
                file_category=f_cat,
                status=WorkingPaperStatusEnum.DRAFT,
                preparer_id=dto.preparer_id,
                reviewer_id=dto.reviewer_id,
            )
            saved_wp = wp_repo.add_working_paper(wp)

            if dto.initial_sections:
                for idx, sec_data in enumerate(dto.initial_sections, start=1):
                    wp_repo.add_section(
                        WorkingPaperSection(
                            working_paper_id=saved_wp.id,
                            section_order=idx,
                            title=sec_data.get("title", f"Section {idx}"),
                            content_markdown=sec_data.get("content", ""),
                        )
                    )
            else:
                for order, title, content in [
                    (1, "1. Objective & Scope", "Document audit procedure objectives."),
                    (2, "2. Work Done & Testing Summary", "Detail substantive sample testing."),
                    (3, "3. Conclusion", "Auditor conclusion."),
                ]:
                    wp_repo.add_section(
                        WorkingPaperSection(
                            working_paper_id=saved_wp.id,
                            section_order=order,
                            title=title,
                            content_markdown=content,
                        )
                    )

            for proc_id in dto.procedure_ids:
                wp_repo.add_link(str(uuid4()), saved_wp.id, "procedure", proc_id)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.preparer_id,
                    action="Working Paper Created",
                    details=(
                        f"Created Working Paper '{saved_wp.index_reference}': {saved_wp.title}"
                        f" ({f_cat.value})"
                    ),
                )
            )
            return saved_wp

    def scaffold_permanent_audit_file(
        self, engagement_id: str, preparer_id: str = "auditor"
    ) -> list[WorkingPaper]:
        return scaffold_permanent_audit_file(self.db_manager, engagement_id, preparer_id)

    def scaffold_schedule_iii_working_papers(
        self, engagement_id: str, preparer_id: str = "auditor"
    ) -> list[WorkingPaper]:
        return scaffold_schedule_iii_working_papers(self.db_manager, engagement_id, preparer_id)

    def get_working_paper(self, wp_id: str) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp = WorkingPaperRepository(session).get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            return wp

    def list_working_papers(self, engagement_id: str) -> list[WorkingPaper]:
        with self.db_manager.session_scope() as session:
            return WorkingPaperRepository(session).list_for_engagement(engagement_id)

    def get_sections(self, wp_id: str) -> list[WorkingPaperSection]:
        with self.db_manager.session_scope() as session:
            return WorkingPaperRepository(session).get_sections(wp_id)

    def list_links(self, wp_id: str) -> list[dict[str, str]]:
        with self.db_manager.session_scope() as session:
            return WorkingPaperRepository(session).get_links(wp_id)

    def count_open_review_notes(self, wp_id: str) -> int:
        with self.db_manager.session_scope() as session:
            return WorkingPaperRepository(session).count_open_review_notes(wp_id)

    def list_review_notes(self, wp_id: str) -> list[ReviewNote]:
        with self.db_manager.session_scope() as session:
            return WorkingPaperRepository(session).list_review_notes(wp_id)

    def _resolve_user_role(self, session, engagement_id: str, username: str) -> str:
        return resolve_user_role(session, engagement_id, username)

    def _archive_working_paper_version(self, session, wp: WorkingPaper) -> None:
        archive_working_paper_version(session, wp)

    def assign_user_to_engagement(self, engagement_id: str, username: str, role: str) -> None:
        with self.db_manager.session_scope() as session:
            user = session.query(UserModel).filter(UserModel.username == username).first()
            if not user:
                raise EntityNotFoundError("User", username)
            existing = (
                session.query(EngagementMemberModel)
                .filter(
                    EngagementMemberModel.engagement_id == engagement_id,
                    EngagementMemberModel.user_id == user.id,
                )
                .first()
            )
            if existing:
                existing.role = role
            else:
                session.add(
                    EngagementMemberModel(
                        id=str(uuid4()),
                        engagement_id=engagement_id,
                        user_id=user.id,
                        role=role,
                        created_at=utc_now(),
                        updated_at=utc_now(),
                    )
                )
            session.flush()

    def prepare_working_paper(self, wp_id: str, preparer_id: str) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.is_locked:
                raise ValidationError("Working Paper is locked and cannot be modified.")
            role = self._resolve_user_role(session, wp.engagement_id, preparer_id)
            if role == "Administrator":
                raise ValidationError("Administrator accounts do not have audit professional authority.")
            wp.preparer_id = preparer_id
            wp.transition_to(WorkingPaperStatusEnum.PREPARED)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=preparer_id,
                    action="Working Paper Prepared",
                    details=f"Prepared Working Paper '{wp.index_reference}'",
                )
            )
            return updated

    def submit_for_review(self, wp_id: str, submitter_id: str) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.is_locked:
                raise ValidationError("Working Paper is locked.")
            role = self._resolve_user_role(session, wp.engagement_id, submitter_id)
            if role == "Administrator":
                raise ValidationError("Administrator accounts do not have audit professional authority.")
            new_status = (
                WorkingPaperStatusEnum.RESUBMITTED
                if wp.status == WorkingPaperStatusEnum.RETURNED
                else WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW
            )
            wp.preparer_id = submitter_id
            wp.transition_to(new_status)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=submitter_id,
                    action=f"Working Paper Submitted ({new_status.value})",
                    details=f"Submitted Working Paper '{wp.index_reference}' for review",
                )
            )
            return updated

    def start_review(self, wp_id: str, reviewer_id: str) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.preparer_id == reviewer_id:
                raise ValidationError("Segregation of Duties Violation: Preparer cannot review their own workpaper.")
            role = self._resolve_user_role(session, wp.engagement_id, reviewer_id)
            if role not in ("Senior", "Manager", "Partner"):
                raise ValidationError("Unauthorized reviewer: Must be Senior, Manager, or Partner to start review.")
            wp.reviewer_id = reviewer_id
            if wp.status in (WorkingPaperStatusEnum.DRAFT, WorkingPaperStatusEnum.PREPARED):
                wp.status = WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW
            wp.transition_to(WorkingPaperStatusEnum.UNDER_REVIEW)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=reviewer_id,
                    action="Working Paper Review Started",
                    details=f"Started review of Working Paper '{wp.index_reference}'",
                )
            )
            return updated

    def return_working_paper(self, wp_id: str, reviewer_id: str) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.preparer_id == reviewer_id:
                raise ValidationError("Segregation of Duties Violation: Preparer cannot return their own workpaper.")
            role = self._resolve_user_role(session, wp.engagement_id, reviewer_id)
            if role not in ("Senior", "Manager", "Partner"):
                raise ValidationError("Unauthorized reviewer: Must be Senior, Manager, or Partner to return workpaper.")
            wp.reviewer_id = reviewer_id
            wp.transition_to(WorkingPaperStatusEnum.RETURNED)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=reviewer_id,
                    action="Working Paper Returned",
                    details=f"Returned Working Paper '{wp.index_reference}' to preparer",
                )
            )
            return updated

    def update_working_paper_content(
        self,
        wp_id: str,
        title: str,
        area: str,
        conclusion: str,
        sections_list: list[dict],
        editor_id: str,
    ) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.is_locked:
                raise ValidationError("Working Paper is locked and cannot be edited.")
            role = self._resolve_user_role(session, wp.engagement_id, editor_id)
            if role == "Administrator":
                raise ValidationError("Administrator accounts do not have audit professional authority.")
            if wp.status == WorkingPaperStatusEnum.RETURNED:
                self._archive_working_paper_version(session, wp)
                wp.version += 1
                wp.status = WorkingPaperStatusEnum.DRAFT
            elif wp.status == WorkingPaperStatusEnum.REOPENED:
                wp.status = WorkingPaperStatusEnum.DRAFT

            wp.title = title
            wp.area = area
            wp.conclusion = conclusion
            wp.updated_at = utc_now()
            session.query(WorkingPaperSectionModel).filter(
                WorkingPaperSectionModel.working_paper_id == wp.id
            ).delete()
            for idx, sec in enumerate(sections_list, start=1):
                wp_repo.add_section(
                    WorkingPaperSection(
                        working_paper_id=wp.id,
                        section_order=idx,
                        title=sec.get("title", f"Section {idx}"),
                        content_markdown=sec.get("content_markdown", ""),
                    )
                )
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=editor_id,
                    action="Working Paper Content Updated",
                    details=f"Updated content of Working Paper '{wp.index_reference}'",
                )
            )
            return updated

    def raise_review_note(self, dto: CreateReviewNoteDTO) -> ReviewNote:
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
            if wp.status in (
                WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
                WorkingPaperStatusEnum.RESUBMITTED,
                WorkingPaperStatusEnum.DRAFT,
                WorkingPaperStatusEnum.PREPARED,
            ):
                wp.status = WorkingPaperStatusEnum.UNDER_REVIEW
                wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.raised_by,
                    action="Review Note Raised",
                    details=f"Raised review note on '{wp.index_reference}': {dto.note_text[:60]}",
                )
            )
            return saved_note

    def respond_review_note(self, dto: RespondReviewNoteDTO) -> ReviewNote:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
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
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id="",
                    actor=dto.responder,
                    action="Review Note Responded",
                    details=f"Responded to review note '{saved.id}'",
                )
            )
            return saved

    def clear_review_note(self, dto: ClearReviewNoteDTO) -> ReviewNote:
        with self.db_manager.session_scope() as session:
            n_model = session.get(ReviewNoteModel, dto.review_note_id)
            if not n_model:
                raise EntityNotFoundError("ReviewNote", dto.review_note_id)
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(n_model.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", n_model.working_paper_id)
            cleared_by = getattr(dto, "cleared_by", getattr(dto, "reviewer", "Reviewer"))
            role = self._resolve_user_role(session, wp.engagement_id, cleared_by)
            if cleared_by != n_model.raised_by and role not in ("Manager", "Partner"):
                raise ValidationError("Cannot clear someone else's review note without Manager or Partner authority.")
            note = ReviewNote(
                id=n_model.id,
                working_paper_id=n_model.working_paper_id,
                section_id=n_model.section_id,
                raised_by=n_model.raised_by,
                note_text=n_model.note_text,
                status=ReviewNoteStatusEnum(n_model.status),
            )
            note.clear(cleared_by)
            saved = wp_repo.update_review_note(note)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=cleared_by,
                    action="Review Note Cleared",
                    details=f"Cleared review note '{saved.id}'",
                )
            )
            return saved

    def sign_off_working_paper(self, dto: SignOffDTO) -> SignOffRecord:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)
            if wp.is_locked:
                raise ValidationError(f"Working Paper '{wp.index_reference}' is locked and cannot be signed off.")
            if wp.preparer_id == dto.user_id:
                raise ValidationError("Segregation of Duties Violation: Preparer cannot approve or sign-off own workpaper.")
            res_role = self._resolve_user_role(session, wp.engagement_id, dto.user_id)
            if res_role == "Administrator":
                raise ValidationError("Administrator accounts do not have audit professional authority to perform sign-offs.")
            if isinstance(dto.level, SignOffLevelEnum):
                level_enum = dto.level
            else:
                try:
                    level_enum = SignOffLevelEnum(dto.level)
                except ValueError:
                    level_enum = (
                        SignOffLevelEnum[dto.level]
                        if str(dto.level) in SignOffLevelEnum.__members__
                        else SignOffLevelEnum.REVIEWED
                    )
            level_val = getattr(level_enum, "value", str(level_enum))
            if level_enum == SignOffLevelEnum.FINAL_SIGN_OFF and res_role != "Partner":
                raise ValidationError("Unauthorized: Only Partners can perform final sign-off.")
            if level_enum == SignOffLevelEnum.REVIEWED and res_role not in ("Senior", "Manager", "Partner"):
                raise ValidationError("Unauthorized: Must be Senior, Manager, or Partner to approve.")
            open_notes = wp_repo.count_open_review_notes(wp.id)
            if open_notes > 0:
                raise ValidationError(
                    f"Audit Quality Violation: Cannot sign off Working Paper '{wp.index_reference}'"
                    f" while {open_notes} open review notes exist."
                )
            sections, links = wp_repo.get_sections(wp.id), wp_repo.get_links(wp.id)
            chash = self.compute_content_hash(wp, sections, links)
            wp.content_hash = chash
            if level_enum == SignOffLevelEnum.REVIEWED:
                if wp.status in (
                    WorkingPaperStatusEnum.DRAFT,
                    WorkingPaperStatusEnum.PREPARED,
                    WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
                ):
                    wp.status = WorkingPaperStatusEnum.UNDER_REVIEW
                wp.transition_to(WorkingPaperStatusEnum.APPROVED)
            else:
                if wp.status in (
                    WorkingPaperStatusEnum.DRAFT,
                    WorkingPaperStatusEnum.PREPARED,
                    WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW,
                    WorkingPaperStatusEnum.UNDER_REVIEW,
                ):
                    wp.status = WorkingPaperStatusEnum.APPROVED
                wp.transition_to(WorkingPaperStatusEnum.LOCKED)
            wp_repo.update_working_paper(wp)
            saved_signoff = wp_repo.add_sign_off(
                SignOffRecord(
                    working_paper_id=wp.id,
                    level=level_enum,
                    user_id=dto.user_id,
                    user_role=dto.user_role,
                    content_hash=chash,
                    note=dto.note,
                )
            )
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.user_id,
                    action=f"Working Paper {level_val}",
                    details=f"Signed off '{wp.index_reference}' ({level_val}) by {dto.user_role} {dto.user_id}. Content Hash: {chash[:16]}...",
                )
            )
            return saved_signoff

    def verify_integrity(self, wp_id: str) -> tuple[bool, str]:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if not wp.content_hash:
                return True, "Working paper has not been signed off yet."
            recalculated = self.compute_content_hash(wp, wp_repo.get_sections(wp.id), wp_repo.get_links(wp.id))
            if recalculated == wp.content_hash:
                return True, f"Integrity Verified: Content hash matches signed hash ({wp.content_hash[:16]}...)"
            return False, f"TAMPER ALERT: Content hash mismatch! Stored: {wp.content_hash[:16]}, Recalculated: {recalculated[:16]}"

    def reopen_working_paper(self, dto: ReopenWorkingPaperDTO) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)
            role = self._resolve_user_role(session, wp.engagement_id, dto.reopened_by)
            if role != "Partner":
                raise ValidationError("Unauthorized: Only Partners can reopen locked working papers.")
            if not wp.is_locked:
                raise ValidationError("Working Paper is not locked.")
            self._archive_working_paper_version(session, wp)
            wp.transition_to(WorkingPaperStatusEnum.REOPENED)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=dto.reopened_by,
                    action="Working Paper Reopened",
                    details=f"Reopened Working Paper '{wp.index_reference}' (v{wp.version}). Reason: {dto.reason}",
                )
            )
            return updated
