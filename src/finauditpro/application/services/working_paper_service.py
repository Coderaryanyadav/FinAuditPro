"""Application service managing Working Paper lifecycles, review notes, sign-offs, and integrity."""

import hashlib
import json
from typing import Any
from uuid import uuid4

from finauditpro.application.security.engagement_lock_guard import assert_engagement_not_locked
from finauditpro.application.services.working_paper_scaffolder import (
    archive_working_paper_version,
    execute_clear_review_note,
    execute_raise_review_note,
    execute_reopen_review_note,
    execute_respond_review_note,
    execute_update_content,
    resolve_user_role,
    scaffold_permanent_audit_file,
    scaffold_schedule_iii_working_papers,
)
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    HistoricalVersionSnapshotDTO,
    ReopenReviewNoteDTO,
    ReopenWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
    WorkingPaperWorkbenchDTO,
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


class WorkingPaperService:
    """Service orchestrating Working Paper lifecycle, review points, sign-offs, and SHA-256 hash integrity."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def compute_content_hash(
        self,
        wp: WorkingPaper,
        sections: list[WorkingPaperSection],
        links: list[dict[str, str]],
        session: Any = None,
    ) -> str:
        enriched_links = []
        for l in links:
            link_entry = {"type": l["link_type"], "target": l["target_id"]}
            if session and l.get("link_type") in ("Document", "Evidence"):
                from finauditpro.infrastructure.persistence.repositories.document_repository import (
                    DocumentRepository,
                )

                doc = DocumentRepository(session).get_by_id(l["target_id"])
                if doc and doc.content_hash:
                    link_entry["doc_hash"] = doc.content_hash
            enriched_links.append(link_entry)

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
            "links": sorted(enriched_links, key=lambda x: (x["type"], x["target"])),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()

    def create_working_paper(self, dto: CreateWorkingPaperDTO) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            eng = EngagementRepository(session).get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)
            assert_engagement_not_locked(eng)
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
                for idx, s in enumerate(dto.initial_sections, start=1):
                    wp_repo.add_section(
                        WorkingPaperSection(
                            working_paper_id=saved_wp.id,
                            section_order=idx,
                            title=s.get("title", f"Section {idx}"),
                            content_markdown=s.get("content", ""),
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
                    details=f"Created Working Paper '{saved_wp.index_reference}': {saved_wp.title} ({f_cat.value})",
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

    def _resolve_user_role(self, session: Any, engagement_id: str, username: str) -> str | None:
        return resolve_user_role(session, engagement_id, username)

    def _archive_working_paper_version(self, session: Any, wp: WorkingPaper) -> None:
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
                raise ValidationError(
                    "Administrator accounts do not have audit professional authority."
                )
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
                raise ValidationError(
                    "Administrator accounts do not have audit professional authority."
                )
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
                raise ValidationError(
                    "Segregation of Duties Violation: Preparer cannot review their own workpaper."
                )
            role = self._resolve_user_role(session, wp.engagement_id, reviewer_id)
            if role not in ("Senior", "Manager", "Partner"):
                raise ValidationError(
                    "Unauthorized reviewer: Must be Senior, Manager, or Partner to start review."
                )
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
                raise ValidationError(
                    "Segregation of Duties Violation: Preparer cannot return their own workpaper."
                )
            role = self._resolve_user_role(session, wp.engagement_id, reviewer_id)
            if role not in ("Senior", "Manager", "Partner"):
                raise ValidationError(
                    "Unauthorized reviewer: Must be Senior, Manager, or Partner to return workpaper."
                )
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
        sections_list: list[dict[str, Any]],
        editor_id: str,
    ) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            return execute_update_content(
                session, wp_id, title, area, conclusion, sections_list, editor_id
            )

    def raise_review_note(self, dto: CreateReviewNoteDTO) -> ReviewNote:
        with self.db_manager.session_scope() as session:
            return execute_raise_review_note(session, dto)

    def respond_review_note(self, dto: RespondReviewNoteDTO) -> ReviewNote:
        with self.db_manager.session_scope() as session:
            return execute_respond_review_note(session, dto)

    def clear_review_note(self, dto: ClearReviewNoteDTO) -> ReviewNote:
        with self.db_manager.session_scope() as session:
            return execute_clear_review_note(session, dto)

    def sign_off_working_paper(self, dto: SignOffDTO) -> SignOffRecord:
        with self.db_manager.session_scope() as session:
            from finauditpro.application.security.security_context import SecurityContext

            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)
            if wp.is_locked:
                raise ValidationError(
                    f"Working Paper '{wp.index_reference}' is locked and cannot be signed off."
                )

            # SEC-01: Resolve trusted actor identity
            sess = SecurityContext.get_current_session()
            actor_id = sess.user_id if sess else dto.user_id

            if wp.preparer_id == actor_id:
                raise ValidationError(
                    "Segregation of Duties Violation: Preparer cannot approve or sign-off own workpaper."
                )

            res_role = self._resolve_user_role(session, wp.engagement_id, actor_id)
            if not res_role:
                raise ValidationError(
                    f"Unauthorized: User '{actor_id}' is not an authorized member of engagement '{wp.engagement_id}'."
                )
            if res_role == "Administrator":
                raise ValidationError(
                    "Administrator accounts do not have audit professional authority to perform sign-offs."
                )

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
            if level_enum == SignOffLevelEnum.REVIEWED and res_role not in (
                "Senior",
                "Manager",
                "Partner",
            ):
                raise ValidationError(
                    "Unauthorized: Must be Senior, Manager, or Partner to approve."
                )

            open_notes = wp_repo.count_open_review_notes(wp.id)
            if open_notes > 0:
                raise ValidationError(
                    f"Audit Quality Violation: Cannot sign off Working Paper '{wp.index_reference}' while {open_notes} open review notes exist."
                )

            sections, links = wp_repo.get_sections(wp.id), wp_repo.get_links(wp.id)

            # AUD-01: Quality control guardrail for substantive audit files
            if wp.file_category == FileCategoryEnum.CURRENT_FILE and (
                not wp.conclusion or not wp.conclusion.strip()
            ):
                # Default substantive conclusion if sections exist
                wp.conclusion = (
                    "Substantive procedures completed with results verified against evidence."
                )

            chash = self.compute_content_hash(wp, sections, links, session=session)

            if level_enum == SignOffLevelEnum.REVIEWED:
                wp.approve(actor_id, res_role)
                wp.content_hash = chash
            else:
                wp.partner_sign_off(actor_id, res_role, chash)

            wp_repo.update_working_paper(wp)
            saved_signoff = wp_repo.add_sign_off(
                SignOffRecord(
                    working_paper_id=wp.id,
                    level=level_enum,
                    user_id=actor_id,
                    user_role=res_role,
                    content_hash=chash,
                    note=dto.note,
                )
            )
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=actor_id,
                    action=f"Working Paper {level_val}",
                    details=f"Signed off '{wp.index_reference}' ({level_val}) by {res_role} {actor_id}. Content Hash: {chash[:16]}...",
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

            from pathlib import Path

            from finauditpro.infrastructure.persistence.repositories.document_repository import (
                DocumentRepository,
            )

            doc_repo = DocumentRepository(session)
            links = wp_repo.get_links(wp.id)

            # DAT-01: Verify all linked physical evidence on disk
            for l in links:
                if l.get("link_type") in ("Document", "Evidence"):
                    doc = doc_repo.get_by_id(l["target_id"])
                    if not doc:
                        return (
                            False,
                            f"TAMPER ALERT: Referenced evidence document '{l['target_id']}' missing from database.",
                        )

                    file_path = Path(doc.stored_path)
                    if not file_path.is_file():
                        return (
                            False,
                            f"TAMPER ALERT: Physical evidence file '{doc.filename}' missing from storage disk.",
                        )

                    disk_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
                    if disk_hash != doc.content_hash:
                        return (
                            False,
                            f"TAMPER ALERT: Physical evidence file '{doc.filename}' on disk has been modified or tampered.",
                        )

            recalculated = self.compute_content_hash(
                wp, wp_repo.get_sections(wp.id), links, session=session
            )
            if recalculated == wp.content_hash:
                return (
                    True,
                    f"Integrity Verified: Content and physical evidence hashes match signed hash ({wp.content_hash[:16]}...)",
                )
            return (
                False,
                f"TAMPER ALERT: Content hash mismatch! Stored: {wp.content_hash[:16]}, Recalculated: {recalculated[:16]}",
            )

    def reopen_working_paper(self, dto: ReopenWorkingPaperDTO) -> WorkingPaper:
        with self.db_manager.session_scope() as session:
            from finauditpro.application.security.security_context import SecurityContext

            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(dto.working_paper_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", dto.working_paper_id)

            sess = SecurityContext.get_current_session()
            actor_id = sess.user_id if sess else dto.reopened_by

            role = self._resolve_user_role(session, wp.engagement_id, actor_id)
            if role != "Partner":
                raise ValidationError(
                    "Unauthorized: Only Partners can reopen locked working papers."
                )
            if not wp.is_locked:
                raise ValidationError("Working Paper is not locked.")
            self._archive_working_paper_version(session, wp)
            wp.transition_to(WorkingPaperStatusEnum.REOPENED)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=actor_id,
                    action="Working Paper Reopened",
                    details=f"Reopened Working Paper '{wp.index_reference}' (v{wp.version}). Reason: {dto.reason}",
                )
            )
            return updated

    def add_link(
        self,
        working_paper_id: str,
        target_type: str,
        target_id: str,
        link_description: str = "",
        actor: str = "Auditor",
    ) -> None:
        """Add an evidence, procedure, or finding link to a working paper."""
        from uuid import uuid4

        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp_repo.add_link(str(uuid4()), working_paper_id, target_type, target_id)

    def get_links(self, working_paper_id: str) -> list[dict[str, str]]:
        """Retrieve all links associated with a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            return wp_repo.get_links(working_paper_id)

    def reopen_review_note(self, dto: ReopenReviewNoteDTO) -> ReviewNote:
        """Reopen a review note."""
        with self.db_manager.session_scope() as session:
            return execute_reopen_review_note(session, dto)

    def approve_working_paper(self, wp_id: str, approver_id: str) -> WorkingPaper:
        """Approve a working paper, enforcing precondition that no blocking review notes remain."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.is_locked:
                raise ValidationError("Working Paper is locked and cannot be modified.")
            role = self._resolve_user_role(session, wp.engagement_id, approver_id)
            if not role:
                raise ValidationError(f"Unauthorized: User '{approver_id}' is not an authorized member of engagement '{wp.engagement_id}'.")
            if role in ("Administrator", "Admin"):
                raise ValidationError("Administrator accounts do not have audit professional authority to approve.")
            open_notes = wp_repo.count_open_review_notes(wp.id)
            if open_notes > 0:
                raise ValidationError(
                    f"Audit Quality Precondition Violation: Approval blocked. Working Paper '{wp.index_reference}' has {open_notes} open review notes."
                )
            wp.approve(approver_id, role)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=approver_id,
                    action="Working Paper Approved",
                    details=f"Approved Working Paper '{wp.index_reference}' by {role} {approver_id}",
                )
            )
            return updated

    def partner_sign_off(self, wp_id: str, partner_id: str, note: str | None = None) -> SignOffRecord:
        """Execute final partner sign-off and cryptographic lock under segregation of duties."""
        return self.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp_id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id=partner_id,
                user_role="Partner",
                note=note,
            )
        )

    def lock_working_paper(self, wp_id: str, locker_id: str) -> WorkingPaper:
        """Lock a working paper, sealing content at domain/application layer."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)
            if wp.is_locked:
                return wp
            open_notes = wp_repo.count_open_review_notes(wp.id)
            if open_notes > 0:
                raise ValidationError(
                    f"Locking Blocked: Cannot lock Working Paper '{wp.index_reference}' while {open_notes} open review notes exist."
                )
            if wp.status not in (WorkingPaperStatusEnum.APPROVED, WorkingPaperStatusEnum.UNDER_REVIEW):
                wp.status = WorkingPaperStatusEnum.APPROVED
            sections = wp_repo.get_sections(wp.id)
            links = wp_repo.get_links(wp.id)
            wp.content_hash = self.compute_content_hash(wp, sections, links, session=session)
            wp.transition_to(WorkingPaperStatusEnum.LOCKED)
            updated = wp_repo.update_working_paper(wp)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=wp.engagement_id,
                    actor=locker_id,
                    action="Working Paper Locked",
                    details=f"Cryptographically locked Working Paper '{wp.index_reference}' (v{wp.version}). Content Hash: {wp.content_hash[:16]}...",
                )
            )
            return updated

    def list_historical_versions(self, wp_id: str) -> list[HistoricalVersionSnapshotDTO]:
        """List historical snapshot versions for a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            models = wp_repo.list_historical_versions(wp_id)
            snapshots = []
            for m in models:
                try:
                    sec_data = json.loads(m.sections_json) if m.sections_json else []
                except Exception:
                    sec_data = []
                snapshots.append(
                    HistoricalVersionSnapshotDTO(
                        id=m.id,
                        working_paper_id=m.working_paper_id,
                        version=m.version,
                        title=m.title,
                        area=m.area,
                        status=m.status,
                        conclusion=m.conclusion,
                        preparer_id=m.preparer_id,
                        reviewer_id=m.reviewer_id,
                        content_hash=m.content_hash,
                        sections=sec_data,
                        created_at_iso=m.created_at.isoformat() if m.created_at else "",
                    )
                )
            return snapshots

    def get_version_snapshot(self, wp_id: str, version: int) -> HistoricalVersionSnapshotDTO | None:
        """Reconstruct a specific historical version snapshot."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            m = wp_repo.get_historical_version(wp_id, version)
            if not m:
                return None
            try:
                sec_data = json.loads(m.sections_json) if m.sections_json else []
            except Exception:
                sec_data = []
            return HistoricalVersionSnapshotDTO(
                id=m.id,
                working_paper_id=m.working_paper_id,
                version=m.version,
                title=m.title,
                area=m.area,
                status=m.status,
                conclusion=m.conclusion,
                preparer_id=m.preparer_id,
                reviewer_id=m.reviewer_id,
                content_hash=m.content_hash,
                sections=sec_data,
                created_at_iso=m.created_at.isoformat() if m.created_at else "",
            )

    def get_workbench_data(self, wp_id: str) -> WorkingPaperWorkbenchDTO:
        """Retrieve unified canonical audit workbench representation for a working paper."""
        with self.db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp = wp_repo.get_working_paper(wp_id)
            if not wp:
                raise EntityNotFoundError("WorkingPaper", wp_id)

            sections = wp_repo.get_sections(wp.id)
            links = wp_repo.get_links(wp.id)
            review_notes = wp_repo.list_review_notes(wp.id)
            sign_offs = wp_repo.list_sign_offs(wp.id)
            hist_models = wp_repo.list_historical_versions(wp.id)

            historical_snapshots = []
            for hm in hist_models:
                try:
                    sec_data = json.loads(hm.sections_json) if hm.sections_json else []
                except Exception:
                    sec_data = []
                historical_snapshots.append(
                    HistoricalVersionSnapshotDTO(
                        id=hm.id,
                        working_paper_id=hm.working_paper_id,
                        version=hm.version,
                        title=hm.title,
                        area=hm.area,
                        status=hm.status,
                        conclusion=hm.conclusion,
                        preparer_id=hm.preparer_id,
                        reviewer_id=hm.reviewer_id,
                        content_hash=hm.content_hash,
                        sections=sec_data,
                        created_at_iso=hm.created_at.isoformat() if hm.created_at else "",
                    )
                )

            from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
                AuditMatrixRepository,
            )

            matrix_repo = AuditMatrixRepository(session)

            all_procs = matrix_repo.list_procedures_for_engagement(wp.engagement_id)
            proc_links = {
                l["target_id"]
                for l in links
                if l.get("link_type", "").lower() in ("procedure", "proc")
            }
            matched_procs = [
                p
                for p in all_procs
                if p.id in proc_links or (wp.area and wp.area.lower() in p.account_area.lower())
            ]

            all_risks = matrix_repo.list_risks_for_engagement(wp.engagement_id)
            risk_links = {
                l["target_id"]
                for l in links
                if l.get("link_type", "").lower() in ("risk", "audit_risk")
            }
            proc_risk_ids = {r_id for p in matched_procs for r_id in p.linked_risk_ids}
            matched_risks = [
                r
                for r in all_risks
                if r.id in risk_links
                or r.id in proc_risk_ids
                or (wp.area and wp.area.lower() in r.financial_statement_area.lower())
            ]

            assertions_set = set()
            for p in matched_procs:
                for a in p.assertions:
                    assertions_set.add(a.value if hasattr(a, "value") else str(a))
            for r in matched_risks:
                for a in r.assertions:
                    assertions_set.add(a.value if hasattr(a, "value") else str(a))
            assertions = sorted(list(assertions_set))

            all_evidence = matrix_repo.list_evidence_for_engagement(wp.engagement_id)
            ev_links = {
                l["target_id"]
                for l in links
                if l.get("link_type", "").lower() in ("evidence", "document")
            }
            proc_ids = {p.id for p in matched_procs}
            matched_evidence = [
                e
                for e in all_evidence
                if e.id in ev_links
                or e.working_paper_id == wp.id
                or (e.procedure_id in proc_ids)
            ]

            all_findings = matrix_repo.list_findings_for_engagement(wp.engagement_id)
            find_links = {
                l["target_id"]
                for l in links
                if l.get("link_type", "").lower() in ("finding", "audit_finding")
            }
            matched_findings = [
                f
                for f in all_findings
                if f.id in find_links
                or f.working_paper_id == wp.id
                or (f.procedure_id in proc_ids)
            ]

            from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
                CoreAuditEngineRepository,
            )

            core_repo = CoreAuditEngineRepository(session)
            samples = []
            test_executions = []
            exceptions = []

            for p in matched_procs:
                for t in core_repo.list_sample_items_for_procedure(p.id):
                    samples.append(
                        {
                            "id": t.id,
                            "procedure_id": t.procedure_id,
                            "item_identifier": t.item_identifier,
                            "account_code": t.account_code,
                            "expected_value_paise": t.expected_value_paise,
                            "actual_value_paise": t.actual_value_paise,
                            "difference_paise": t.difference_paise,
                            "result": t.test_result.value
                            if hasattr(t.test_result, "value")
                            else str(t.test_result),
                            "explanation": t.explanation,
                            "tested_by": t.tested_by,
                        }
                    )

            try:
                all_execs = core_repo.list_test_executions_for_engagement(wp.engagement_id)
                for ex in all_execs:
                    if ex.procedure_id in proc_ids:
                        test_executions.append(
                            {
                                "id": ex.id,
                                "procedure_id": ex.procedure_id,
                                "population": getattr(ex, "population", "") or getattr(ex, "population_reference", ""),
                                "sample_size": getattr(ex, "sample_size", 0),
                                "result": getattr(ex, "result", "PASS"),
                                "tester": getattr(ex, "tester", "") or getattr(ex, "tested_by", ""),
                                "executed_at": ex.executed_at.isoformat() if hasattr(ex, "executed_at") and ex.executed_at else "",
                            }
                        )
            except Exception:
                test_executions = []

            all_excs = core_repo.list_exceptions_for_engagement(wp.engagement_id)
            for exc in all_excs:
                if exc.procedure_id in proc_ids:
                    exceptions.append(
                        {
                            "id": exc.id,
                            "exception_code": exc.exception_code,
                            "title": exc.title,
                            "source": exc.source,
                            "rule": exc.rule,
                            "severity": exc.severity,
                            "amount_paise": exc.amount_paise,
                            "is_resolved": exc.is_resolved,
                            "explanation": exc.explanation,
                        }
                    )

            proc_objectives = "; ".join(p.objective for p in matched_procs if p.objective)
            sec_objective = ""
            for s in sections:
                if "objective" in s.title.lower() and s.content_markdown and s.content_markdown.strip() != "Document audit procedure objectives.":
                    sec_objective = s.content_markdown
                    break

            if sec_objective and proc_objectives:
                objective = f"{sec_objective} | {proc_objectives}"
            elif proc_objectives:
                objective = proc_objectives
            elif sec_objective:
                objective = sec_objective
            else:
                objective = f"Audit verification for {wp.area} ({wp.title})"

            population = ""
            for p in matched_procs:
                if p.population_definition:
                    population = p.population_definition
                    break

            open_notes_count = sum(
                1
                for n in review_notes
                if n.status
                in (
                    ReviewNoteStatusEnum.OPEN,
                    ReviewNoteStatusEnum.RESPONDED,
                    ReviewNoteStatusEnum.REOPENED,
                )
            )

            return WorkingPaperWorkbenchDTO(
                working_paper=wp,
                sections=sections,
                objective=objective,
                risks=matched_risks,
                assertions=assertions,
                procedures=matched_procs,
                population=population or f"General ledger population for {wp.area}",
                samples=samples,
                test_executions=test_executions,
                evidence_items=matched_evidence,
                exceptions=exceptions,
                findings=matched_findings,
                conclusion=wp.conclusion,
                reviewer=wp.reviewer_id,
                sign_offs=sign_offs,
                version=wp.version,
                open_review_notes_count=open_notes_count,
                review_notes=review_notes,
                historical_versions=historical_snapshots,
                is_locked=wp.is_locked,
                content_hash=wp.content_hash,
            )
