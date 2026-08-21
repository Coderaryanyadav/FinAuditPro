"""Audit matrix repository for Risk, Materiality, Procedures, Findings & Evidence."""

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    BenchmarkTypeEnum,
    FindingSourceEnum,
    FindingStatusEnum,
    MaterialityAssessment,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.infrastructure.persistence.models import (
    AuditEvidenceModel,
    AuditFindingModel,
    AuditProcedureModel,
    AuditRiskModel,
    MaterialityAssessmentModel,
)


class AuditMatrixRepository:
    """Repository managing Risk Register, Materiality, Procedures, Findings, and Evidence persistence."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def _to_risk_entity(self, model: AuditRiskModel) -> AuditRisk:
        try:
            raw_assertions = json.loads(model.assertions_json)
            assertions = [AssertionEnum(a) for a in raw_assertions]
        except Exception:
            assertions = [AssertionEnum.COMPLETENESS]

        return AuditRisk(
            id=model.id,
            engagement_id=model.engagement_id,
            risk_code=model.risk_code,
            title=model.title or f"Risk {model.risk_code}",
            category=model.category,
            description=model.description,
            assertions=assertions,
            inherent_risk=RiskSeverityEnum(model.inherent_risk),
            control_risk=RiskSeverityEnum(model.control_risk),
            derived_romm=RiskSeverityEnum(model.derived_romm),
            is_significant_risk=bool(model.is_significant_risk),
            risk_response=model.risk_response,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_materiality_entity(self, model: MaterialityAssessmentModel) -> MaterialityAssessment:
        return MaterialityAssessment(
            id=model.id,
            engagement_id=model.engagement_id,
            benchmark_type=BenchmarkTypeEnum(model.benchmark_type),
            benchmark_amount_paise=model.benchmark_amount_paise,
            benchmark_source=model.benchmark_source,
            is_verified_statutory=bool(model.is_verified_statutory),
            overall_percentage=model.overall_percentage,
            overall_materiality_paise=model.overall_materiality_paise,
            performance_percentage=model.performance_percentage,
            performance_materiality_paise=model.performance_materiality_paise,
            trivial_percentage=model.trivial_percentage,
            clearly_trivial_threshold_paise=model.clearly_trivial_threshold_paise,
            version=model.version,
            methodology_notes=model.methodology_notes or "",
            created_by=model.created_by,
            created_at=model.created_at,
        )

    def _to_procedure_entity(self, model: AuditProcedureModel) -> AuditProcedure:
        try:
            raw_assertions = json.loads(model.assertions_json)
            assertions = [AssertionEnum(a) for a in raw_assertions]
        except Exception:
            assertions = [AssertionEnum.COMPLETENESS]

        try:
            linked_risks = json.loads(model.linked_risks_json)
        except Exception:
            linked_risks = []

        return AuditProcedure(
            id=model.id,
            engagement_id=model.engagement_id,
            procedure_code=model.procedure_code,
            objective=model.objective,
            procedure_type=model.procedure_type,
            instructions=model.instructions,
            evidence_requirement=model.evidence_requirement or "",
            linked_risk_ids=linked_risks,
            assertions=assertions,
            status=ProcedureStatusEnum(model.status),
            result_summary=model.result_summary,
            conclusion=model.conclusion,
            preparer=model.preparer,
            reviewer=model.reviewer,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_finding_entity(self, model: AuditFindingModel) -> AuditFinding:
        source_val = (
            model.source
            if model.source in FindingSourceEnum._value2member_map_
            else FindingSourceEnum.MANUAL
        )
        return AuditFinding(
            id=model.id,
            engagement_id=model.engagement_id,
            procedure_id=model.procedure_id,
            risk_id=model.risk_id,
            title=model.title,
            description=model.description,
            category=model.category,
            severity=RiskSeverityEnum(model.severity),
            amount_paise=model.amount_paise,
            affected_account=model.affected_account,
            assertion=AssertionEnum(model.assertion)
            if model.assertion in AssertionEnum._value2member_map_
            else AssertionEnum.ACCURACY,
            recommendation=model.recommendation,
            status=FindingStatusEnum(model.status),
            preparer=model.preparer,
            reviewer=model.reviewer,
            source=FindingSourceEnum(source_val),
            is_ai_generated=bool(model.is_ai_generated),
            prior_engagement_finding_id=model.prior_engagement_finding_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_evidence_entity(self, model: AuditEvidenceModel) -> AuditEvidence:
        return AuditEvidence(
            id=model.id,
            engagement_id=model.engagement_id,
            finding_id=model.finding_id,
            procedure_id=model.procedure_id,
            document_id=model.document_id,
            dataset_id=model.dataset_id,
            row_index=model.row_index,
            page_number=model.page_number,
            bounding_box_json=model.bounding_box_json,
            title=model.title,
            excerpt_or_reference=model.excerpt_or_reference,
            created_at=model.created_at,
        )

    def add_risk(self, risk: AuditRisk) -> AuditRisk:
        model = AuditRiskModel(
            id=risk.id,
            engagement_id=risk.engagement_id,
            risk_code=risk.risk_code,
            title=risk.title,
            category=risk.category,
            description=risk.description,
            assertions_json=json.dumps([a.value for a in risk.assertions]),
            inherent_risk=risk.inherent_risk.value,
            control_risk=risk.control_risk.value,
            derived_romm=risk.derived_romm.value,
            is_significant_risk=risk.is_significant_risk,
            risk_response=risk.risk_response,
            created_at=risk.created_at,
            updated_at=risk.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_risk_entity(model)

    def get_risk_by_id(self, risk_id: str) -> AuditRisk | None:
        model = self.session.get(AuditRiskModel, risk_id)
        return self._to_risk_entity(model) if model else None

    def list_risks_for_engagement(self, engagement_id: str) -> list[AuditRisk]:
        stmt = (
            select(AuditRiskModel)
            .where(AuditRiskModel.engagement_id == engagement_id)
            .order_by(AuditRiskModel.risk_code.asc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_risk_entity(m) for m in models]

    def add_materiality(self, mat: MaterialityAssessment) -> MaterialityAssessment:
        model = MaterialityAssessmentModel(
            id=mat.id,
            engagement_id=mat.engagement_id,
            benchmark_type=mat.benchmark_type.value,
            benchmark_amount_paise=mat.benchmark_amount_paise,
            benchmark_source=mat.benchmark_source,
            is_verified_statutory=mat.is_verified_statutory,
            overall_percentage=mat.overall_percentage,
            overall_materiality_paise=mat.overall_materiality_paise,
            performance_percentage=mat.performance_percentage,
            performance_materiality_paise=mat.performance_materiality_paise,
            trivial_percentage=mat.trivial_percentage,
            clearly_trivial_threshold_paise=mat.clearly_trivial_threshold_paise,
            version=mat.version,
            methodology_notes=mat.methodology_notes,
            created_by=mat.created_by,
            created_at=mat.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_materiality_entity(model)

    add_materiality_assessment = add_materiality

    def get_latest_materiality(self, engagement_id: str) -> MaterialityAssessment | None:
        stmt = (
            select(MaterialityAssessmentModel)
            .where(MaterialityAssessmentModel.engagement_id == engagement_id)
            .order_by(MaterialityAssessmentModel.version.desc())
            .limit(1)
        )
        model = self.session.scalars(stmt).first()
        return self._to_materiality_entity(model) if model else None

    def list_materiality_history(self, engagement_id: str) -> list[MaterialityAssessment]:
        stmt = (
            select(MaterialityAssessmentModel)
            .where(MaterialityAssessmentModel.engagement_id == engagement_id)
            .order_by(MaterialityAssessmentModel.version.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_materiality_entity(m) for m in models]

    def add_procedure(self, proc: AuditProcedure) -> AuditProcedure:
        model = AuditProcedureModel(
            id=proc.id,
            engagement_id=proc.engagement_id,
            procedure_code=proc.procedure_code,
            objective=proc.objective,
            procedure_type=proc.procedure_type,
            instructions=proc.instructions,
            evidence_requirement=proc.evidence_requirement,
            linked_risks_json=json.dumps(proc.linked_risk_ids),
            assertions_json=json.dumps([a.value for a in proc.assertions]),
            status=proc.status.value,
            result_summary=proc.result_summary,
            conclusion=proc.conclusion,
            preparer=proc.preparer,
            reviewer=proc.reviewer,
            created_at=proc.created_at,
            updated_at=proc.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_procedure_entity(model)

    def update_procedure(self, proc: AuditProcedure) -> AuditProcedure:
        model = self.session.get(AuditProcedureModel, proc.id)
        if not model:
            raise ValueError(f"Procedure '{proc.id}' not found.")
        model.status = proc.status.value
        model.result_summary = proc.result_summary
        model.conclusion = proc.conclusion
        model.preparer = proc.preparer
        model.reviewer = proc.reviewer
        model.updated_at = utc_now()
        self.session.flush()
        return self._to_procedure_entity(model)

    def get_procedure_by_id(self, procedure_id: str) -> AuditProcedure | None:
        model = self.session.get(AuditProcedureModel, procedure_id)
        return self._to_procedure_entity(model) if model else None

    def list_procedures_for_engagement(self, engagement_id: str) -> list[AuditProcedure]:
        stmt = (
            select(AuditProcedureModel)
            .where(AuditProcedureModel.engagement_id == engagement_id)
            .order_by(AuditProcedureModel.procedure_code.asc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_procedure_entity(m) for m in models]

    def add_finding(self, finding: AuditFinding) -> AuditFinding:
        model = AuditFindingModel(
            id=finding.id,
            engagement_id=finding.engagement_id,
            procedure_id=finding.procedure_id,
            risk_id=finding.risk_id,
            title=finding.title,
            description=finding.description,
            category=finding.category,
            severity=finding.severity.value,
            amount_paise=finding.amount_paise,
            affected_account=finding.affected_account,
            assertion=finding.assertion.value,
            recommendation=finding.recommendation,
            status=finding.status.value,
            preparer=finding.preparer,
            reviewer=finding.reviewer,
            source=finding.source.value
            if hasattr(finding.source, "value")
            else str(finding.source),
            is_ai_generated=finding.is_ai_generated,
            prior_engagement_finding_id=finding.prior_engagement_finding_id,
            created_at=finding.created_at,
            updated_at=finding.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_finding_entity(model)

    def update_finding(self, finding: AuditFinding) -> AuditFinding:
        model = self.session.get(AuditFindingModel, finding.id)
        if not model:
            raise ValueError(f"Finding '{finding.id}' not found.")
        model.title = finding.title
        model.description = finding.description
        model.status = finding.status.value
        model.reviewer = finding.reviewer
        model.recommendation = finding.recommendation
        model.updated_at = utc_now()
        self.session.flush()
        return self._to_finding_entity(model)

    def get_finding_by_id(self, finding_id: str) -> AuditFinding | None:
        model = self.session.get(AuditFindingModel, finding_id)
        return self._to_finding_entity(model) if model else None

    def list_findings_for_engagement(self, engagement_id: str) -> list[AuditFinding]:
        stmt = (
            select(AuditFindingModel)
            .where(AuditFindingModel.engagement_id == engagement_id)
            .order_by(AuditFindingModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_finding_entity(m) for m in models]

    def add_evidence(self, evidence: AuditEvidence) -> AuditEvidence:
        model = AuditEvidenceModel(
            id=evidence.id,
            engagement_id=evidence.engagement_id,
            finding_id=evidence.finding_id,
            procedure_id=evidence.procedure_id,
            document_id=evidence.document_id,
            dataset_id=evidence.dataset_id,
            row_index=evidence.row_index,
            page_number=evidence.page_number,
            bounding_box_json=evidence.bounding_box_json,
            title=evidence.title,
            excerpt_or_reference=evidence.excerpt_or_reference,
            created_at=evidence.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_evidence_entity(model)

    def list_evidence_for_finding(self, finding_id: str) -> list[AuditEvidence]:
        stmt = (
            select(AuditEvidenceModel)
            .where(AuditEvidenceModel.finding_id == finding_id)
            .order_by(AuditEvidenceModel.created_at.asc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_evidence_entity(m) for m in models]

    def list_evidence_for_procedure(self, procedure_id: str) -> list[AuditEvidence]:
        stmt = (
            select(AuditEvidenceModel)
            .where(AuditEvidenceModel.procedure_id == procedure_id)
            .order_by(AuditEvidenceModel.created_at.asc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_evidence_entity(m) for m in models]

    def list_evidence_for_engagement(self, engagement_id: str) -> list[AuditEvidence]:
        stmt = (
            select(AuditEvidenceModel)
            .where(AuditEvidenceModel.engagement_id == engagement_id)
            .order_by(AuditEvidenceModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [self._to_evidence_entity(m) for m in models]
