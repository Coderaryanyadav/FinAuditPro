"""Persistence repository for Phase D Completion Checklist, Related Parties, and SA 240 records."""

from sqlalchemy.orm import Session

from finauditpro.domain.completion_checklist_entities import (
    ChecklistCategoryEnum,
    CompletionChecklistItem,
    CompletionStatusEnum,
    RelatedPartyCompletionRecord,
    SA240CompletionRecord,
)
from finauditpro.infrastructure.persistence.audit_completion_models import (
    CompletionChecklistItemModel,
    RelatedPartyCompletionModel,
    SA240CompletionModel,
)


class CompletionChecklistRepository:
    """Repository managing completion checklist items, related party checks, and SA 240 procedures."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_checklist_item(self, item: CompletionChecklistItem) -> CompletionChecklistItem:
        model = self.session.query(CompletionChecklistItemModel).filter_by(id=item.id).first()
        cat_val = getattr(item.category, "value", str(item.category))
        status_val = getattr(item.status, "value", str(item.status))

        if model:
            model.category = cat_val
            model.title = item.title
            model.description = item.description
            model.is_applicable = item.is_applicable
            model.status = status_val
            model.supporting_ref = item.supporting_ref
            model.reviewer = item.reviewer
            model.notes = item.notes
        else:
            model = CompletionChecklistItemModel(
                id=item.id,
                engagement_id=item.engagement_id,
                category=cat_val,
                title=item.title,
                description=item.description,
                is_applicable=item.is_applicable,
                status=status_val,
                supporting_ref=item.supporting_ref,
                reviewer=item.reviewer,
                notes=item.notes,
            )
            self.session.add(model)
        self.session.flush()
        return self._to_entity(model)

    def list_checklist_items(self, engagement_id: str) -> list[CompletionChecklistItem]:
        models = (
            self.session.query(CompletionChecklistItemModel)
            .filter_by(engagement_id=engagement_id)
            .all()
        )
        return [self._to_entity(m) for m in models]

    def get_checklist_item(self, item_id: str) -> CompletionChecklistItem | None:
        model = self.session.query(CompletionChecklistItemModel).filter_by(id=item_id).first()
        return self._to_entity(model) if model else None

    def save_related_party_completion(
        self, record: RelatedPartyCompletionRecord
    ) -> RelatedPartyCompletionRecord:
        model = (
            self.session.query(RelatedPartyCompletionModel)
            .filter_by(engagement_id=record.engagement_id)
            .first()
        )
        if model:
            model.register_reviewed = record.register_reviewed
            model.undisclosed_transactions_identified = record.undisclosed_transactions_identified
            model.arms_length_verified = record.arms_length_verified
            model.schedule_iii_disclosed = record.schedule_iii_disclosed
            model.auditor_conclusion = record.auditor_conclusion
            model.reviewer = record.reviewer
            model.is_completed = record.is_completed
        else:
            model = RelatedPartyCompletionModel(
                id=record.id,
                engagement_id=record.engagement_id,
                register_reviewed=record.register_reviewed,
                undisclosed_transactions_identified=record.undisclosed_transactions_identified,
                arms_length_verified=record.arms_length_verified,
                schedule_iii_disclosed=record.schedule_iii_disclosed,
                auditor_conclusion=record.auditor_conclusion,
                reviewer=record.reviewer,
                is_completed=record.is_completed,
            )
            self.session.add(model)
        self.session.flush()
        return record

    def get_related_party_completion(
        self, engagement_id: str
    ) -> RelatedPartyCompletionRecord | None:
        model = (
            self.session.query(RelatedPartyCompletionModel)
            .filter_by(engagement_id=engagement_id)
            .first()
        )
        if not model:
            return None
        return RelatedPartyCompletionRecord(
            id=model.id,
            engagement_id=model.engagement_id,
            register_reviewed=model.register_reviewed,
            undisclosed_transactions_identified=model.undisclosed_transactions_identified,
            arms_length_verified=model.arms_length_verified,
            schedule_iii_disclosed=model.schedule_iii_disclosed,
            auditor_conclusion=model.auditor_conclusion,
            reviewer=model.reviewer,
            is_completed=model.is_completed,
        )

    def save_sa240_completion(self, record: SA240CompletionRecord) -> SA240CompletionRecord:
        model = (
            self.session.query(SA240CompletionModel)
            .filter_by(engagement_id=record.engagement_id)
            .first()
        )
        if model:
            model.management_override_tested = record.management_override_tested
            model.journal_entry_testing_completed = record.journal_entry_testing_completed
            model.revenue_recognition_presumption_addressed = (
                record.revenue_recognition_presumption_addressed
            )
            model.risk_indicators_identified = record.risk_indicators_identified
            model.auditor_conclusion = record.auditor_conclusion
            model.reviewer = record.reviewer
            model.is_completed = record.is_completed
        else:
            model = SA240CompletionModel(
                id=record.id,
                engagement_id=record.engagement_id,
                management_override_tested=record.management_override_tested,
                journal_entry_testing_completed=record.journal_entry_testing_completed,
                revenue_recognition_presumption_addressed=record.revenue_recognition_presumption_addressed,
                risk_indicators_identified=record.risk_indicators_identified,
                auditor_conclusion=record.auditor_conclusion,
                reviewer=record.reviewer,
                is_completed=record.is_completed,
            )
            self.session.add(model)
        self.session.flush()
        return record

    def get_sa240_completion(self, engagement_id: str) -> SA240CompletionRecord | None:
        model = (
            self.session.query(SA240CompletionModel)
            .filter_by(engagement_id=engagement_id)
            .first()
        )
        if not model:
            return None
        return SA240CompletionRecord(
            id=model.id,
            engagement_id=model.engagement_id,
            management_override_tested=model.management_override_tested,
            journal_entry_testing_completed=model.journal_entry_testing_completed,
            revenue_recognition_presumption_addressed=model.revenue_recognition_presumption_addressed,
            risk_indicators_identified=model.risk_indicators_identified,
            auditor_conclusion=model.auditor_conclusion,
            reviewer=model.reviewer,
            is_completed=model.is_completed,
        )

    save_fraud_completion = save_sa240_completion  # ignore
    get_fraud_completion = get_sa240_completion  # ignore

    def _to_entity(self, m: CompletionChecklistItemModel) -> CompletionChecklistItem:
        cat_enum = ChecklistCategoryEnum.PLANNING
        for c in ChecklistCategoryEnum:
            if c.value == m.category or c.name == m.category:
                cat_enum = c
                break

        status_enum = CompletionStatusEnum.NOT_STARTED
        for s in CompletionStatusEnum:
            if s.value == m.status or s.name == m.status:
                status_enum = s
                break

        return CompletionChecklistItem(
            id=m.id,
            engagement_id=m.engagement_id,
            category=cat_enum,
            title=m.title,
            description=m.description,
            is_applicable=m.is_applicable,
            status=status_enum,
            supporting_ref=m.supporting_ref,
            reviewer=m.reviewer,
            notes=m.notes,
            updated_at=m.updated_at,
        )
