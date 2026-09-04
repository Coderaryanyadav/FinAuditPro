"""Repository managing Audit Adjusting Journal Entries (AJE) and line items."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from finauditpro.domain.audit_adjustment_entities import (
    AJEStatusEnum,
    AJETypeEnum,
    AuditJournalEntry,
    AuditJournalLine,
)
from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.mapping_and_adjustment_models import (
    AuditJournalEntryModel,
    AuditJournalLineModel,
)


class AuditAdjustmentRepository:
    """Repository managing AJE aggregate roots and double-entry lines."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_line_entity(self, model: AuditJournalLineModel) -> AuditJournalLine:
        return AuditJournalLine(
            id=model.id,
            entry_id=model.entry_id,
            line_no=model.line_no,
            account_code=model.account_code,
            account_name=model.account_name,
            debit_paise=model.debit_paise,
            credit_paise=model.credit_paise,
            lead_schedule_ref=model.lead_schedule_ref,
            narration=model.narration,
        )

    def _to_entry_entity(self, model: AuditJournalEntryModel) -> AuditJournalEntry:
        lines = [self._to_line_entity(line) for line in model.lines]
        return AuditJournalEntry(
            id=model.id,
            engagement_id=model.engagement_id,
            aje_number=model.aje_number,
            entry_date=model.entry_date,
            aje_type=AJETypeEnum(model.aje_type)
            if model.aje_type in AJETypeEnum._value2member_map_
            else AJETypeEnum.MANAGEMENT_ACCEPTED,
            status=AJEStatusEnum(model.status)
            if model.status in AJEStatusEnum._value2member_map_
            else AJEStatusEnum.DRAFT,
            title=model.title,
            narration=model.narration,
            reason=model.reason,
            working_paper_ref=model.working_paper_ref,
            total_debit_paise=model.total_debit_paise,
            total_credit_paise=model.total_credit_paise,
            prepared_by=model.prepared_by,
            prepared_at=model.prepared_at.isoformat()
            if isinstance(model.prepared_at, datetime)
            else str(model.prepared_at),
            reviewed_by=model.reviewed_by,
            reviewed_at=model.reviewed_at.isoformat()
            if isinstance(model.reviewed_at, datetime)
            else (str(model.reviewed_at) if model.reviewed_at else None),
            reversal_of_entry_id=model.reversal_of_entry_id,
            lines=lines,
        )

    def add_entry(self, entry: AuditJournalEntry) -> AuditJournalEntry:
        entry.validate_double_entry()
        model = AuditJournalEntryModel(
            id=entry.id,
            engagement_id=entry.engagement_id,
            aje_number=entry.aje_number,
            entry_date=entry.entry_date,
            aje_type=entry.aje_type.value
            if hasattr(entry.aje_type, "value")
            else str(entry.aje_type),
            status=entry.status.value if hasattr(entry.status, "value") else str(entry.status),
            title=entry.title,
            narration=entry.narration,
            reason=entry.reason,
            working_paper_ref=entry.working_paper_ref,
            total_debit_paise=entry.total_debit_paise,
            total_credit_paise=entry.total_credit_paise,
            prepared_by=entry.prepared_by,
            prepared_at=datetime.fromisoformat(entry.prepared_at)
            if isinstance(entry.prepared_at, str)
            else utc_now(),
            reviewed_by=entry.reviewed_by,
            reviewed_at=datetime.fromisoformat(entry.reviewed_at)
            if isinstance(entry.reviewed_at, str) and entry.reviewed_at
            else None,
            reversal_of_entry_id=entry.reversal_of_entry_id,
        )
        self.session.add(model)
        self.session.flush()

        for idx, line in enumerate(entry.lines, start=1):
            line_model = AuditJournalLineModel(
                id=line.id or str(uuid4()),
                entry_id=model.id,
                line_no=idx,
                account_code=line.account_code,
                account_name=line.account_name,
                debit_paise=line.debit_paise,
                credit_paise=line.credit_paise,
                lead_schedule_ref=line.lead_schedule_ref,
                narration=line.narration,
            )
            self.session.add(line_model)

        self.session.flush()
        return self._to_entry_entity(model)

    def update_entry(self, entry: AuditJournalEntry) -> AuditJournalEntry:
        entry.validate_double_entry()
        model = self.session.get(AuditJournalEntryModel, entry.id)
        if not model:
            return self.add_entry(entry)

        model.entry_date = entry.entry_date
        model.aje_type = (
            entry.aje_type.value if hasattr(entry.aje_type, "value") else str(entry.aje_type)
        )
        model.status = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
        model.title = entry.title
        model.narration = entry.narration
        model.reason = entry.reason
        model.working_paper_ref = entry.working_paper_ref
        model.total_debit_paise = entry.total_debit_paise
        model.total_credit_paise = entry.total_credit_paise
        model.reviewed_by = entry.reviewed_by
        model.reviewed_at = (
            datetime.fromisoformat(entry.reviewed_at)
            if isinstance(entry.reviewed_at, str) and entry.reviewed_at
            else None
        )

        # Replace lines
        stmt = delete(AuditJournalLineModel).where(AuditJournalLineModel.entry_id == model.id)
        self.session.execute(stmt)

        for idx, line in enumerate(entry.lines, start=1):
            line_model = AuditJournalLineModel(
                id=line.id or str(uuid4()),
                entry_id=model.id,
                line_no=idx,
                account_code=line.account_code,
                account_name=line.account_name,
                debit_paise=line.debit_paise,
                credit_paise=line.credit_paise,
                lead_schedule_ref=line.lead_schedule_ref,
                narration=line.narration,
            )
            self.session.add(line_model)

        self.session.flush()
        return self._to_entry_entity(model)

    def get_entry_by_id(self, entry_id: str) -> AuditJournalEntry | None:
        model = self.session.get(AuditJournalEntryModel, entry_id)
        return self._to_entry_entity(model) if model else None

    def get_entry_by_number(self, engagement_id: str, aje_number: str) -> AuditJournalEntry | None:
        stmt = select(AuditJournalEntryModel).where(
            AuditJournalEntryModel.engagement_id == engagement_id,
            AuditJournalEntryModel.aje_number == aje_number,
        )
        model = self.session.scalars(stmt).first()
        return self._to_entry_entity(model) if model else None

    def list_entries_for_engagement(
        self, engagement_id: str, status: AJEStatusEnum | None = None
    ) -> list[AuditJournalEntry]:
        stmt = select(AuditJournalEntryModel).where(
            AuditJournalEntryModel.engagement_id == engagement_id
        )
        if status is not None:
            status_val = status.value if hasattr(status, "value") else str(status)
            stmt = stmt.where(AuditJournalEntryModel.status == status_val)
        stmt = stmt.order_by(AuditJournalEntryModel.aje_number.asc())
        return [self._to_entry_entity(m) for m in self.session.scalars(stmt).all()]

    def list_applied_and_approved_entries(self, engagement_id: str) -> list[AuditJournalEntry]:
        stmt = (
            select(AuditJournalEntryModel)
            .where(
                AuditJournalEntryModel.engagement_id == engagement_id,
                AuditJournalEntryModel.status.in_(
                    [AJEStatusEnum.APPROVED.value, AJEStatusEnum.APPLIED.value]
                ),
            )
            .order_by(AuditJournalEntryModel.aje_number.asc())
        )
        return [self._to_entry_entity(m) for m in self.session.scalars(stmt).all()]

    def delete_draft_entry(self, entry_id: str) -> bool:
        model = self.session.get(AuditJournalEntryModel, entry_id)
        if not model or model.status != AJEStatusEnum.DRAFT.value:
            return False
        self.session.delete(model)
        self.session.flush()
        return True
