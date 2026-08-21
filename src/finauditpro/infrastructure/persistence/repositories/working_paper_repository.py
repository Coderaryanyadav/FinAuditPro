"""Repository for Working Paper persistence, review notes, and sign-offs."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.working_paper_entities import (
    ReviewNote,
    ReviewNoteStatusEnum,
    SignOffLevelEnum,
    SignOffRecord,
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.working_paper_models import (
    ReviewNoteModel,
    SignOffRecordModel,
    WorkingPaperLinkModel,
    WorkingPaperModel,
    WorkingPaperSectionModel,
)


class WorkingPaperRepository:
    """Repository managing Working Papers, Sections, Links, Review Notes, and Sign-offs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_wp_entity(self, model: WorkingPaperModel) -> WorkingPaper:
        return WorkingPaper(
            id=model.id,
            engagement_id=model.engagement_id,
            index_reference=model.index_reference,
            title=model.title,
            area=model.area,
            status=WorkingPaperStatusEnum(model.status),
            conclusion=model.conclusion,
            preparer_id=model.preparer_id,
            reviewer_id=model.reviewer_id,
            content_hash=model.content_hash,
            version=model.version,
            is_locked=model.is_locked,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def add_working_paper(self, wp: WorkingPaper) -> WorkingPaper:
        model = WorkingPaperModel(
            id=wp.id,
            engagement_id=wp.engagement_id,
            index_reference=wp.index_reference,
            title=wp.title,
            area=wp.area,
            status=wp.status.value,
            conclusion=wp.conclusion,
            preparer_id=wp.preparer_id,
            reviewer_id=wp.reviewer_id,
            content_hash=wp.content_hash,
            version=wp.version,
            is_locked=wp.is_locked,
            created_at=wp.created_at,
            updated_at=wp.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_wp_entity(model)

    def get_working_paper(self, wp_id: str) -> WorkingPaper | None:
        model = self.session.get(WorkingPaperModel, wp_id)
        return self._to_wp_entity(model) if model else None

    def list_for_engagement(self, engagement_id: str) -> list[WorkingPaper]:
        stmt = (
            select(WorkingPaperModel)
            .where(WorkingPaperModel.engagement_id == engagement_id)
            .order_by(WorkingPaperModel.index_reference)
        )
        models = self.session.scalars(stmt).all()
        return [self._to_wp_entity(m) for m in models]

    def add_section(self, sec: WorkingPaperSection) -> WorkingPaperSection:
        model = WorkingPaperSectionModel(
            id=sec.id,
            working_paper_id=sec.working_paper_id,
            section_order=sec.section_order,
            title=sec.title,
            content_markdown=sec.content_markdown,
            created_at=sec.created_at,
            updated_at=sec.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return sec

    def get_sections(self, wp_id: str) -> list[WorkingPaperSection]:
        stmt = (
            select(WorkingPaperSectionModel)
            .where(WorkingPaperSectionModel.working_paper_id == wp_id)
            .order_by(WorkingPaperSectionModel.section_order)
        )
        models = self.session.scalars(stmt).all()
        return [
            WorkingPaperSection(
                id=m.id,
                working_paper_id=m.working_paper_id,
                section_order=m.section_order,
                title=m.title,
                content_markdown=m.content_markdown,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def add_link(self, link_id: str, wp_id: str, link_type: str, target_id: str) -> None:
        model = WorkingPaperLinkModel(
            id=link_id,
            working_paper_id=wp_id,
            link_type=link_type,
            target_id=target_id,
        )
        self.session.add(model)
        self.session.flush()

    def get_links(self, wp_id: str) -> list[dict[str, str]]:
        stmt = select(WorkingPaperLinkModel).where(WorkingPaperLinkModel.working_paper_id == wp_id)
        models = self.session.scalars(stmt).all()
        return [{"id": m.id, "link_type": m.link_type, "target_id": m.target_id} for m in models]

    def add_review_note(self, note: ReviewNote) -> ReviewNote:
        model = ReviewNoteModel(
            id=note.id,
            working_paper_id=note.working_paper_id,
            section_id=note.section_id,
            raised_by=note.raised_by,
            note_text=note.note_text,
            status=note.status.value,
            response_text=note.response_text,
            responded_by=note.responded_by,
            cleared_by=note.cleared_by,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return note

    def update_review_note(self, note: ReviewNote) -> ReviewNote:
        model = self.session.get(ReviewNoteModel, note.id)
        if model:
            model.status = note.status.value
            model.response_text = note.response_text
            model.responded_by = note.responded_by
            model.cleared_by = note.cleared_by
            model.updated_at = note.updated_at
            self.session.flush()
        return note

    def list_review_notes(self, wp_id: str) -> list[ReviewNote]:
        stmt = (
            select(ReviewNoteModel)
            .where(ReviewNoteModel.working_paper_id == wp_id)
            .order_by(ReviewNoteModel.created_at)
        )
        models = self.session.scalars(stmt).all()
        return [
            ReviewNote(
                id=m.id,
                working_paper_id=m.working_paper_id,
                section_id=m.section_id,
                raised_by=m.raised_by,
                note_text=m.note_text,
                status=ReviewNoteStatusEnum(m.status),
                response_text=m.response_text,
                responded_by=m.responded_by,
                cleared_by=m.cleared_by,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def count_open_review_notes(self, wp_id: str) -> int:
        notes = self.list_review_notes(wp_id)
        return sum(
            1
            for n in notes
            if n.status
            in (
                ReviewNoteStatusEnum.OPEN,
                ReviewNoteStatusEnum.RESPONDED,
                ReviewNoteStatusEnum.REOPENED,
            )
        )

    def add_sign_off(self, signoff: SignOffRecord) -> SignOffRecord:
        model = SignOffRecordModel(
            id=signoff.id,
            working_paper_id=signoff.working_paper_id,
            level=signoff.level.value,
            user_id=signoff.user_id,
            user_role=signoff.user_role,
            content_hash=signoff.content_hash,
            entry_hash=signoff.entry_hash,
            note=signoff.note,
            disclaimer_notice=signoff.disclaimer_notice,
            created_at=signoff.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return signoff

    def list_sign_offs(self, wp_id: str) -> list[SignOffRecord]:
        stmt = (
            select(SignOffRecordModel)
            .where(SignOffRecordModel.working_paper_id == wp_id)
            .order_by(SignOffRecordModel.created_at)
        )
        models = self.session.scalars(stmt).all()
        return [
            SignOffRecord(
                id=m.id,
                working_paper_id=m.working_paper_id,
                level=SignOffLevelEnum(m.level),
                user_id=m.user_id,
                user_role=m.user_role,
                content_hash=m.content_hash,
                entry_hash=m.entry_hash,
                note=m.note,
                disclaimer_notice=m.disclaimer_notice,
                created_at=m.created_at,
            )
            for m in models
        ]

    def update_working_paper(self, wp: WorkingPaper) -> WorkingPaper:
        model = self.session.get(WorkingPaperModel, wp.id)
        if model:
            model.title = wp.title
            model.area = wp.area
            model.status = wp.status.value
            model.conclusion = wp.conclusion
            model.reviewer_id = wp.reviewer_id
            model.content_hash = wp.content_hash
            model.version = wp.version
            model.is_locked = wp.is_locked
            model.updated_at = wp.updated_at
            self.session.flush()
        return wp
