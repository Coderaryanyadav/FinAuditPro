"""Repository for Core Audit Engine: Sample Items, Exceptions, and SA 450 Misstatements."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.audit_execution_entities import (
    AuditException,
    AuditMisstatement,
    AuditSampleItemTest,
    AuditTestOutcomeEnum,
    ExceptionStatusEnum,
    MisstatementStatusEnum,
    MisstatementTypeEnum,
)
from finauditpro.infrastructure.persistence.core_audit_engine_models import (
    AuditExceptionModel,
    AuditMisstatementModel,
    AuditSampleItemModel,
)


class CoreAuditEngineRepository:
    """Persistence repository for transaction sample tests, audit exceptions, and SA 450 misstatements."""

    def __init__(self, session: Session) -> None:
        self.session = session

    # --- Sample Items ---

    def add_sample_item(self, item: AuditSampleItemTest) -> AuditSampleItemTest:
        model = AuditSampleItemModel(
            id=item.id or str(uuid4()),
            procedure_id=item.procedure_id,
            sample_plan_id=item.sample_plan_id,
            item_identifier=item.item_identifier,
            account_code=item.account_code,
            expected_value_paise=item.expected_value_paise,
            actual_value_paise=item.actual_value_paise,
            difference_paise=item.difference_paise,
            test_result=item.test_result.value
            if hasattr(item.test_result, "value")
            else str(item.test_result),
            explanation=item.explanation,
            evidence_ref=item.evidence_ref,
            tested_by=item.tested_by,
            created_at=item.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_sample_item_entity(model)

    def add_sample_items_bulk(self, items: list[AuditSampleItemTest]) -> list[AuditSampleItemTest]:
        models = [
            AuditSampleItemModel(
                id=item.id or str(uuid4()),
                procedure_id=item.procedure_id,
                sample_plan_id=item.sample_plan_id,
                item_identifier=item.item_identifier,
                account_code=item.account_code,
                expected_value_paise=item.expected_value_paise,
                actual_value_paise=item.actual_value_paise,
                difference_paise=item.difference_paise,
                test_result=item.test_result.value
                if hasattr(item.test_result, "value")
                else str(item.test_result),
                explanation=item.explanation,
                evidence_ref=item.evidence_ref,
                tested_by=item.tested_by,
                created_at=item.created_at,
            )
            for item in items
        ]
        self.session.add_all(models)
        self.session.flush()
        return [self._to_sample_item_entity(m) for m in models]

    def get_sample_item_by_id(self, item_id: str) -> AuditSampleItemTest | None:
        model = self.session.get(AuditSampleItemModel, item_id)
        return self._to_sample_item_entity(model) if model else None

    def list_sample_items_for_procedure(self, procedure_id: str) -> list[AuditSampleItemTest]:
        stmt = (
            select(AuditSampleItemModel)
            .where(AuditSampleItemModel.procedure_id == procedure_id)
            .order_by(AuditSampleItemModel.created_at.asc())
        )
        return [self._to_sample_item_entity(m) for m in self.session.scalars(stmt).all()]

    # --- Exceptions ---

    def add_exception(self, exc: AuditException) -> AuditException:
        model = AuditExceptionModel(
            id=exc.id or str(uuid4()),
            engagement_id=exc.engagement_id,
            procedure_id=exc.procedure_id,
            sample_item_id=exc.sample_item_id,
            exception_code=exc.exception_code,
            title=exc.title,
            description=exc.description,
            amount_paise=exc.amount_paise,
            root_cause=exc.root_cause,
            management_response=exc.management_response,
            is_resolved=exc.is_resolved,
            resolution=exc.resolution,
            status=exc.status.value if hasattr(exc.status, "value") else str(exc.status),
            evidence_id=exc.evidence_id,
            reviewer=exc.reviewer,
            created_at=exc.created_at,
            updated_at=exc.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_exception_entity(model)

    def get_exception_by_id(self, exc_id: str) -> AuditException | None:
        model = self.session.get(AuditExceptionModel, exc_id)
        return self._to_exception_entity(model) if model else None

    def update_exception(self, exc: AuditException) -> AuditException:
        model = self.session.get(AuditExceptionModel, exc.id)
        if not model:
            return self.add_exception(exc)
        model.title = exc.title
        model.description = exc.description
        model.amount_paise = exc.amount_paise
        model.root_cause = exc.root_cause
        model.management_response = exc.management_response
        model.is_resolved = exc.is_resolved
        model.resolution = exc.resolution
        model.status = exc.status.value if hasattr(exc.status, "value") else str(exc.status)
        model.evidence_id = exc.evidence_id
        model.reviewer = exc.reviewer
        model.updated_at = exc.updated_at
        self.session.flush()
        return self._to_exception_entity(model)

    def list_exceptions_for_engagement(self, engagement_id: str) -> list[AuditException]:
        stmt = (
            select(AuditExceptionModel)
            .where(AuditExceptionModel.engagement_id == engagement_id)
            .order_by(AuditExceptionModel.created_at.desc())
        )
        return [self._to_exception_entity(m) for m in self.session.scalars(stmt).all()]

    def list_exceptions_for_procedure(self, procedure_id: str) -> list[AuditException]:
        stmt = (
            select(AuditExceptionModel)
            .where(AuditExceptionModel.procedure_id == procedure_id)
            .order_by(AuditExceptionModel.created_at.desc())
        )
        return [self._to_exception_entity(m) for m in self.session.scalars(stmt).all()]

    # --- Misstatements ---

    def add_misstatement(self, misst: AuditMisstatement) -> AuditMisstatement:
        model = AuditMisstatementModel(
            id=misst.id or str(uuid4()),
            engagement_id=misst.engagement_id,
            exception_id=misst.exception_id,
            procedure_id=misst.procedure_id,
            account_code=misst.account_code,
            account_name=misst.account_name,
            schedule_iii_category=misst.schedule_iii_category,
            misstatement_type=misst.misstatement_type.value
            if hasattr(misst.misstatement_type, "value")
            else str(misst.misstatement_type),
            status=misst.status.value if hasattr(misst.status, "value") else str(misst.status),
            amount_paise=misst.amount_paise,
            is_corrected=misst.is_corrected,
            linked_aje_id=misst.linked_aje_id,
            linked_aje_number=misst.linked_aje_number,
            rationale=misst.rationale,
            created_by=misst.created_by,
            created_at=misst.created_at,
            updated_at=misst.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_misstatement_entity(model)

    def get_misstatement_by_id(self, misst_id: str) -> AuditMisstatement | None:
        model = self.session.get(AuditMisstatementModel, misst_id)
        return self._to_misstatement_entity(model) if model else None

    def update_misstatement(self, misst: AuditMisstatement) -> AuditMisstatement:
        model = self.session.get(AuditMisstatementModel, misst.id)
        if not model:
            return self.add_misstatement(misst)
        model.account_code = misst.account_code
        model.account_name = misst.account_name
        model.schedule_iii_category = misst.schedule_iii_category
        model.misstatement_type = (
            misst.misstatement_type.value
            if hasattr(misst.misstatement_type, "value")
            else str(misst.misstatement_type)
        )
        model.status = misst.status.value if hasattr(misst.status, "value") else str(misst.status)
        model.amount_paise = misst.amount_paise
        model.is_corrected = misst.is_corrected
        model.linked_aje_id = misst.linked_aje_id
        model.linked_aje_number = misst.linked_aje_number
        model.rationale = misst.rationale
        model.updated_at = misst.updated_at
        self.session.flush()
        return self._to_misstatement_entity(model)

    def list_misstatements_for_engagement(self, engagement_id: str) -> list[AuditMisstatement]:
        stmt = (
            select(AuditMisstatementModel)
            .where(AuditMisstatementModel.engagement_id == engagement_id)
            .order_by(AuditMisstatementModel.created_at.desc())
        )
        return [self._to_misstatement_entity(m) for m in self.session.scalars(stmt).all()]

    # --- Mappers ---

    def _to_sample_item_entity(self, m: AuditSampleItemModel) -> AuditSampleItemTest:
        return AuditSampleItemTest(
            id=m.id,
            procedure_id=m.procedure_id,
            sample_plan_id=m.sample_plan_id,
            item_identifier=m.item_identifier,
            account_code=m.account_code,
            expected_value_paise=m.expected_value_paise,
            actual_value_paise=m.actual_value_paise,
            difference_paise=m.difference_paise,
            test_result=AuditTestOutcomeEnum(m.test_result)
            if m.test_result in AuditTestOutcomeEnum._value2member_map_
            else AuditTestOutcomeEnum.PASS,
            explanation=m.explanation,
            evidence_ref=m.evidence_ref,
            tested_by=m.tested_by,
            created_at=m.created_at,
        )

    def _to_exception_entity(self, m: AuditExceptionModel) -> AuditException:
        return AuditException(
            id=m.id,
            engagement_id=m.engagement_id,
            procedure_id=m.procedure_id,
            sample_item_id=m.sample_item_id,
            exception_code=m.exception_code,
            title=m.title,
            description=m.description,
            amount_paise=m.amount_paise,
            root_cause=m.root_cause,
            management_response=m.management_response,
            is_resolved=m.is_resolved,
            resolution=m.resolution,
            status=ExceptionStatusEnum(m.status)
            if m.status in ExceptionStatusEnum._value2member_map_
            else ExceptionStatusEnum.OPEN,
            evidence_id=m.evidence_id,
            reviewer=m.reviewer,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _to_misstatement_entity(self, m: AuditMisstatementModel) -> AuditMisstatement:
        return AuditMisstatement(
            id=m.id,
            engagement_id=m.engagement_id,
            exception_id=m.exception_id,
            procedure_id=m.procedure_id,
            account_code=m.account_code,
            account_name=m.account_name,
            schedule_iii_category=m.schedule_iii_category,
            misstatement_type=MisstatementTypeEnum(m.misstatement_type)
            if m.misstatement_type in MisstatementTypeEnum._value2member_map_
            else MisstatementTypeEnum.FACTUAL,
            status=MisstatementStatusEnum(m.status)
            if m.status in MisstatementStatusEnum._value2member_map_
            else MisstatementStatusEnum.UNCORRECTED,
            amount_paise=m.amount_paise,
            is_corrected=m.is_corrected,
            linked_aje_id=m.linked_aje_id,
            linked_aje_number=m.linked_aje_number,
            rationale=m.rationale,
            created_by=m.created_by,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
