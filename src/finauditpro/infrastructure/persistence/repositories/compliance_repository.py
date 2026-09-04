"""Repository for Indian Compliance: CARO 2020 Clause Workpapers and Form 3CD Tax Audit Checks."""

import json
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.compliance_entities import (
    CAROApplicabilityEnum,
    CAROClauseWorkpaper,
    CAROReportAnswerEnum,
    TaxAuditCategoryEnum,
    TaxAuditCheck,
    TaxAuditCheckResultEnum,
)
from finauditpro.infrastructure.persistence.financial_statement_models import (
    CAROWorkpaperModel,
    TaxAuditCheckModel,
)


class ComplianceRepository:
    """Persistence repository for CARO 2020 clause workpapers and Form 3CD Tax Audit checks."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_caro_workpaper(self, wp: CAROClauseWorkpaper) -> CAROClauseWorkpaper:
        model = CAROWorkpaperModel(
            id=wp.id or str(uuid4()),
            engagement_id=wp.engagement_id,
            clause_code=wp.clause_code,
            clause_title=wp.clause_title,
            applicability=wp.applicability.value
            if hasattr(wp.applicability, "value")
            else str(wp.applicability),
            applicability_reason=wp.applicability_reason,
            question=wp.question,
            procedure_text=wp.procedure_text,
            evidence_refs_json=json.dumps(wp.evidence_refs),
            finding_refs_json=json.dumps(wp.finding_refs),
            management_response=wp.management_response,
            conclusion_text=wp.conclusion_text,
            report_answer=wp.report_answer.value
            if hasattr(wp.report_answer, "value")
            else str(wp.report_answer),
            preparer=wp.preparer,
            reviewer=wp.reviewer,
            status=wp.status,
            created_at=wp.created_at,
            updated_at=wp.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_caro_entity(model)

    def get_caro_workpaper_by_clause(
        self, engagement_id: str, clause_code: str
    ) -> CAROClauseWorkpaper | None:
        stmt = select(CAROWorkpaperModel).where(
            CAROWorkpaperModel.engagement_id == engagement_id,
            CAROWorkpaperModel.clause_code == clause_code,
        )
        model = self.session.scalars(stmt).first()
        return self._to_caro_entity(model) if model else None

    def list_caro_workpapers_for_engagement(self, engagement_id: str) -> list[CAROClauseWorkpaper]:
        stmt = (
            select(CAROWorkpaperModel)
            .where(CAROWorkpaperModel.engagement_id == engagement_id)
            .order_by(CAROWorkpaperModel.clause_code)
        )
        return [self._to_caro_entity(m) for m in self.session.scalars(stmt).all()]

    def update_caro_workpaper(self, wp: CAROClauseWorkpaper) -> CAROClauseWorkpaper:
        model = self.session.get(CAROWorkpaperModel, wp.id)
        if not model:
            return self.add_caro_workpaper(wp)
        model.applicability = (
            wp.applicability.value if hasattr(wp.applicability, "value") else str(wp.applicability)
        )
        model.applicability_reason = wp.applicability_reason
        model.procedure_text = wp.procedure_text
        model.evidence_refs_json = json.dumps(wp.evidence_refs)
        model.finding_refs_json = json.dumps(wp.finding_refs)
        model.management_response = wp.management_response
        model.conclusion_text = wp.conclusion_text
        model.report_answer = (
            wp.report_answer.value if hasattr(wp.report_answer, "value") else str(wp.report_answer)
        )
        model.reviewer = wp.reviewer
        model.status = wp.status
        model.updated_at = wp.updated_at
        self.session.flush()
        return self._to_caro_entity(model)

    def add_tax_check(self, check: TaxAuditCheck) -> TaxAuditCheck:
        model = TaxAuditCheckModel(
            id=check.id or str(uuid4()),
            engagement_id=check.engagement_id,
            clause_code=check.clause_code,
            category=check.category.value
            if hasattr(check.category, "value")
            else str(check.category),
            description=check.description,
            input_source=check.input_source,
            rule_logic=check.rule_logic,
            system_result=check.system_result.value
            if hasattr(check.system_result, "value")
            else str(check.system_result),
            auditor_conclusion=check.auditor_conclusion.value
            if hasattr(check.auditor_conclusion, "value")
            else str(check.auditor_conclusion),
            exception_amount_paise=check.exception_amount_paise,
            exception_id=check.exception_id,
            evidence_ref=check.evidence_ref,
            reviewer_notes=check.reviewer_notes,
            reviewer=check.reviewer,
            status=check.status,
            created_at=check.created_at,
            updated_at=check.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_tax_check_entity(model)

    def list_tax_checks_for_engagement(self, engagement_id: str) -> list[TaxAuditCheck]:
        stmt = (
            select(TaxAuditCheckModel)
            .where(TaxAuditCheckModel.engagement_id == engagement_id)
            .order_by(TaxAuditCheckModel.clause_code)
        )
        return [self._to_tax_check_entity(m) for m in self.session.scalars(stmt).all()]

    def update_tax_check(self, check: TaxAuditCheck) -> TaxAuditCheck:
        model = self.session.get(TaxAuditCheckModel, check.id)
        if not model:
            return self.add_tax_check(check)
        model.auditor_conclusion = (
            check.auditor_conclusion.value
            if hasattr(check.auditor_conclusion, "value")
            else str(check.auditor_conclusion)
        )
        model.exception_amount_paise = check.exception_amount_paise
        model.exception_id = check.exception_id
        model.evidence_ref = check.evidence_ref
        model.reviewer_notes = check.reviewer_notes
        model.reviewer = check.reviewer
        model.status = check.status
        model.updated_at = check.updated_at
        self.session.flush()
        return self._to_tax_check_entity(model)

    def _to_caro_entity(self, m: CAROWorkpaperModel) -> CAROClauseWorkpaper:
        return CAROClauseWorkpaper(
            id=m.id,
            engagement_id=m.engagement_id,
            clause_code=m.clause_code,
            clause_title=m.clause_title,
            applicability=CAROApplicabilityEnum(m.applicability)
            if m.applicability in CAROApplicabilityEnum._value2member_map_
            else CAROApplicabilityEnum.APPLICABLE,
            applicability_reason=m.applicability_reason,
            question=m.question,
            procedure_text=m.procedure_text,
            evidence_refs=json.loads(m.evidence_refs_json) if m.evidence_refs_json else [],
            finding_refs=json.loads(m.finding_refs_json) if m.finding_refs_json else [],
            management_response=m.management_response,
            conclusion_text=m.conclusion_text,
            report_answer=CAROReportAnswerEnum(m.report_answer)
            if m.report_answer in CAROReportAnswerEnum._value2member_map_
            else CAROReportAnswerEnum.UNQUALIFIED,
            preparer=m.preparer,
            reviewer=m.reviewer,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _to_tax_check_entity(self, m: TaxAuditCheckModel) -> TaxAuditCheck:
        return TaxAuditCheck(
            id=m.id,
            engagement_id=m.engagement_id,
            clause_code=m.clause_code,
            category=TaxAuditCategoryEnum(m.category)
            if m.category in TaxAuditCategoryEnum._value2member_map_
            else TaxAuditCategoryEnum.BASIC_ASSESSEE_INFO,
            description=m.description,
            input_source=m.input_source,
            rule_logic=m.rule_logic,
            system_result=TaxAuditCheckResultEnum(m.system_result)
            if m.system_result in TaxAuditCheckResultEnum._value2member_map_
            else TaxAuditCheckResultEnum.COMPLIANT,
            auditor_conclusion=TaxAuditCheckResultEnum(m.auditor_conclusion)
            if m.auditor_conclusion in TaxAuditCheckResultEnum._value2member_map_
            else TaxAuditCheckResultEnum.COMPLIANT,
            exception_amount_paise=m.exception_amount_paise,
            exception_id=m.exception_id,
            evidence_ref=m.evidence_ref,
            reviewer_notes=m.reviewer_notes,
            reviewer=m.reviewer,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
