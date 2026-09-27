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
    EvidenceStatusEnum,
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

    def _parse_assertions(self, raw_json: str | None) -> list[AssertionEnum]:
        if not raw_json:
            return [AssertionEnum.COMPLETENESS]
        try:
            raw_list = json.loads(raw_json)
            parsed = [
                AssertionEnum(a) if a in AssertionEnum._value2member_map_ else AssertionEnum[a]
                for a in raw_list
                if a in AssertionEnum._value2member_map_ or hasattr(AssertionEnum, a)
            ]
            return parsed if parsed else [AssertionEnum.COMPLETENESS]
        except Exception:
            return [AssertionEnum.COMPLETENESS]

    def _to_risk_entity(self, model: AuditRiskModel) -> AuditRisk:
        try:
            ev_ids = json.loads(getattr(model, "evidence_ids_json", "[]") or "[]")
        except Exception:
            ev_ids = []
        try:
            proc_ids = json.loads(getattr(model, "linked_procedures_json", "[]") or "[]")
        except Exception:
            proc_ids = []
        return AuditRisk(
            id=model.id, engagement_id=model.engagement_id, risk_code=model.risk_code,
            title=model.title or f"Risk {model.risk_code}", category=model.category, description=model.description,
            financial_statement_area=getattr(model, "financial_statement_area", "") or model.category,
            assertions=self._parse_assertions(model.assertions_json),
            inherent_risk=RiskSeverityEnum(model.inherent_risk), control_risk=RiskSeverityEnum(model.control_risk),
            derived_romm=RiskSeverityEnum(model.derived_romm), is_significant_risk=bool(model.is_significant_risk),
            planned_response=model.risk_response or "", status=getattr(model, "status", "Identified") or "Identified",
            evidence_ids=ev_ids, linked_procedure_ids=proc_ids,
            created_at=model.created_at, updated_at=model.updated_at,
        )

    def _to_materiality_entity(self, model: MaterialityAssessmentModel) -> MaterialityAssessment:
        return MaterialityAssessment(
            id=model.id, engagement_id=model.engagement_id, benchmark_type=BenchmarkTypeEnum(model.benchmark_type),
            benchmark_amount_paise=model.benchmark_amount_paise, benchmark_source=model.benchmark_source,
            is_verified_statutory=bool(model.is_verified_statutory), overall_percentage=model.overall_percentage,
            overall_materiality_paise=model.overall_materiality_paise, performance_percentage=model.performance_percentage,
            performance_materiality_paise=model.performance_materiality_paise, trivial_percentage=model.trivial_percentage,
            clearly_trivial_threshold_paise=model.clearly_trivial_threshold_paise, version=model.version,
            methodology_notes=model.methodology_notes or "", created_by=model.created_by, created_at=model.created_at,
        )

    def _to_procedure_entity(self, model: AuditProcedureModel) -> AuditProcedure:
        try:
            linked_risks = json.loads(model.linked_risks_json)
        except Exception:
            linked_risks = []
        nte = getattr(model, "nature_timing_extent", None) or ""
        account_area, population_def, meth = "", "", ""
        if nte.startswith("{"):
            try:
                data = json.loads(nte)
                account_area = data.get("account_area", "")
                population_def = data.get("population_definition", "")
                meth = data.get("methodology", "")
            except Exception:
                account_area = nte
        elif nte:
            account_area = nte

        return AuditProcedure(
            id=model.id, engagement_id=model.engagement_id, procedure_code=model.procedure_code,
            objective=model.objective, procedure_type=model.procedure_type, account_area=account_area,
            instructions=model.instructions, evidence_requirement=model.evidence_requirement or "",
            requires_evidence=(model.evidence_requirement != "NOT_REQUIRED"), population_definition=population_def,
            methodology=meth, linked_risk_ids=linked_risks, assertions=self._parse_assertions(model.assertions_json),
            status=ProcedureStatusEnum(model.status), result_summary=model.result_summary,
            conclusion=model.conclusion, preparer=model.preparer,
            prepared_date=model.updated_at if model.preparer else None, reviewer=model.reviewer,
            reviewed_date=model.updated_at if model.reviewer else None, created_at=model.created_at, updated_at=model.updated_at,
        )

    def _to_finding_entity(self, model: AuditFindingModel) -> AuditFinding:
        source_val = model.source if model.source in FindingSourceEnum._value2member_map_ else "manual"
        return AuditFinding(
            id=model.id, engagement_id=model.engagement_id, procedure_id=model.procedure_id, risk_id=model.risk_id,
            title=model.title, description=model.description, category=model.category,
            severity=RiskSeverityEnum(model.severity), amount_paise=model.amount_paise,
            affected_account=model.affected_account,
            assertion=AssertionEnum(model.assertion) if model.assertion in AssertionEnum._value2member_map_ else AssertionEnum.ACCURACY,
            recommendation=model.recommendation, status=FindingStatusEnum(model.status), preparer=model.preparer,
            reviewer=model.reviewer, source=FindingSourceEnum(source_val), is_ai_generated=bool(model.is_ai_generated),
            prior_engagement_finding_id=model.prior_engagement_finding_id, created_at=model.created_at, updated_at=model.updated_at,
        )

    def _to_evidence_entity(self, model: AuditEvidenceModel) -> AuditEvidence:
        meta = {}
        if model.bounding_box_json and model.bounding_box_json.startswith("{"):
            try:
                meta = json.loads(model.bounding_box_json)
            except Exception:
                meta = {}
        stat_str = meta.get("status", "UPLOADED")
        stat = EvidenceStatusEnum(stat_str) if stat_str in EvidenceStatusEnum._value2member_map_ else EvidenceStatusEnum.UPLOADED
        return AuditEvidence(
            id=model.id, engagement_id=model.engagement_id, evidence_code=meta.get("evidence_code", ""),
            finding_id=model.finding_id or meta.get("finding_id"), procedure_id=model.procedure_id or meta.get("procedure_id"),
            working_paper_id=meta.get("working_paper_id"), document_id=model.document_id, dataset_id=model.dataset_id,
            row_index=model.row_index, page_number=model.page_number, bounding_box_json=meta.get("raw_bbox"),
            title=model.title, excerpt_or_reference=model.excerpt_or_reference, source=meta.get("source", "Uploaded Document"),
            file_path=meta.get("file_path"), content_hash=meta.get("content_hash"), version=meta.get("version", 1),
            document_type=meta.get("document_type", "General"), location=meta.get("location"),
            uploaded_by=meta.get("uploaded_by", "Auditor"), status=stat, sample_ref=meta.get("sample_ref"),
            test_execution_id=meta.get("test_execution_id"), reviewed_by=meta.get("reviewed_by"),
            review_notes=meta.get("review_notes"), created_at=model.created_at,
        )

    def _evidence_meta_json(self, ev: AuditEvidence) -> str:
        return json.dumps({
            "evidence_code": ev.evidence_code, "finding_id": ev.finding_id, "procedure_id": ev.procedure_id,
            "working_paper_id": ev.working_paper_id, "source": ev.source, "file_path": ev.file_path,
            "content_hash": ev.content_hash, "version": ev.version, "document_type": ev.document_type,
            "location": ev.location, "uploaded_by": ev.uploaded_by, "status": ev.status.value,
            "sample_ref": ev.sample_ref, "test_execution_id": ev.test_execution_id,
            "reviewed_by": ev.reviewed_by, "review_notes": ev.review_notes, "raw_bbox": ev.bounding_box_json,
        })

    def add_risk(self, risk: AuditRisk) -> AuditRisk:
        model = AuditRiskModel(
            id=risk.id, engagement_id=risk.engagement_id, risk_code=risk.risk_code, title=risk.title,
            category=risk.category, financial_statement_area=risk.financial_statement_area or risk.area,
            description=risk.description, assertions_json=json.dumps([a.value for a in risk.assertions]),
            inherent_risk=risk.inherent_risk.value, control_risk=risk.control_risk.value,
            derived_romm=risk.derived_romm.value, is_significant_risk=risk.is_significant_risk,
            risk_response=risk.risk_response, status=risk.status,
            evidence_ids_json=json.dumps(risk.evidence_ids),
            linked_procedures_json=json.dumps(risk.linked_procedure_ids),
            created_at=risk.created_at, updated_at=risk.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_risk_entity(model)

    def get_risk_by_id(self, risk_id: str) -> AuditRisk | None:
        model = self.session.get(AuditRiskModel, risk_id)
        return self._to_risk_entity(model) if model else None

    def list_risks_for_engagement(self, engagement_id: str) -> list[AuditRisk]:
        stmt = select(AuditRiskModel).where(AuditRiskModel.engagement_id == engagement_id).order_by(AuditRiskModel.risk_code)
        return [self._to_risk_entity(m) for m in self.session.scalars(stmt).all()]

    def add_materiality(self, mat: MaterialityAssessment) -> MaterialityAssessment:
        model = MaterialityAssessmentModel(
            id=mat.id, engagement_id=mat.engagement_id, benchmark_type=mat.benchmark_type.value,
            benchmark_amount_paise=mat.benchmark_amount_paise, benchmark_source=mat.benchmark_source,
            is_verified_statutory=mat.is_verified_statutory, overall_percentage=mat.overall_percentage,
            overall_materiality_paise=mat.overall_materiality_paise, performance_percentage=mat.performance_percentage,
            performance_materiality_paise=mat.performance_materiality_paise, trivial_percentage=mat.trivial_percentage,
            clearly_trivial_threshold_paise=mat.clearly_trivial_threshold_paise, version=mat.version,
            methodology_notes=mat.methodology_notes, created_by=mat.created_by, created_at=mat.created_at,
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

    get_materiality = get_latest_materiality

    def list_materiality_history(self, engagement_id: str) -> list[MaterialityAssessment]:
        stmt = select(MaterialityAssessmentModel).where(MaterialityAssessmentModel.engagement_id == engagement_id).order_by(MaterialityAssessmentModel.version.desc())
        return [self._to_materiality_entity(m) for m in self.session.scalars(stmt).all()]

    def add_procedure(self, proc: AuditProcedure) -> AuditProcedure:
        meta_dict = {"account_area": proc.account_area, "population_definition": proc.population_definition, "methodology": proc.methodology}
        model = AuditProcedureModel(
            id=proc.id, engagement_id=proc.engagement_id, procedure_code=proc.procedure_code,
            objective=proc.objective, procedure_type=proc.procedure_type, instructions=proc.instructions,
            evidence_requirement=proc.evidence_requirement or ("REQUIRED" if proc.requires_evidence else "NOT_REQUIRED"),
            nature_timing_extent=json.dumps(meta_dict), linked_risks_json=json.dumps(proc.linked_risk_ids),
            assertions_json=json.dumps([a.value for a in proc.assertions]), status=proc.status.value,
            result_summary=proc.result_summary, conclusion=proc.conclusion, preparer=proc.preparer,
            reviewer=proc.reviewer, created_at=proc.created_at, updated_at=proc.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_procedure_entity(model)

    def update_procedure(self, proc: AuditProcedure) -> AuditProcedure:
        model = self.session.get(AuditProcedureModel, proc.id)
        if not model:
            raise ValueError(f"Procedure '{proc.id}' not found.")
        meta_dict = {"account_area": proc.account_area, "population_definition": proc.population_definition, "methodology": proc.methodology}
        model.nature_timing_extent = json.dumps(meta_dict)
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
        stmt = select(AuditProcedureModel).where(AuditProcedureModel.engagement_id == engagement_id).order_by(AuditProcedureModel.procedure_code)
        return [self._to_procedure_entity(m) for m in self.session.scalars(stmt).all()]

    def add_finding(self, finding: AuditFinding) -> AuditFinding:
        model = AuditFindingModel(
            id=finding.id, engagement_id=finding.engagement_id, procedure_id=finding.procedure_id,
            risk_id=finding.risk_id, title=finding.title, description=finding.description,
            category=finding.category, severity=finding.severity.value, amount_paise=finding.amount_paise,
            affected_account=finding.affected_account, assertion=finding.assertion.value,
            recommendation=finding.recommendation, status=finding.status.value, preparer=finding.preparer,
            reviewer=finding.reviewer, source=finding.source.value if hasattr(finding.source, "value") else str(finding.source),
            is_ai_generated=finding.is_ai_generated, prior_engagement_finding_id=finding.prior_engagement_finding_id,
            created_at=finding.created_at, updated_at=finding.updated_at,
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
        model.severity = finding.severity.value
        model.amount_paise = finding.amount_paise
        model.status = finding.status.value
        model.reviewer = finding.reviewer
        model.updated_at = utc_now()
        self.session.flush()
        return self._to_finding_entity(model)

    def get_finding_by_id(self, finding_id: str) -> AuditFinding | None:
        model = self.session.get(AuditFindingModel, finding_id)
        return self._to_finding_entity(model) if model else None

    def list_findings_for_engagement(self, engagement_id: str) -> list[AuditFinding]:
        stmt = select(AuditFindingModel).where(AuditFindingModel.engagement_id == engagement_id).order_by(AuditFindingModel.created_at.desc())
        return [self._to_finding_entity(m) for m in self.session.scalars(stmt).all()]

    def add_evidence(self, evidence: AuditEvidence) -> AuditEvidence:
        model = AuditEvidenceModel(
            id=evidence.id, engagement_id=evidence.engagement_id, finding_id=evidence.finding_id,
            procedure_id=evidence.procedure_id, document_id=evidence.document_id,
            dataset_id=evidence.dataset_id, row_index=evidence.row_index, page_number=evidence.page_number,
            bounding_box_json=self._evidence_meta_json(evidence), title=evidence.title,
            excerpt_or_reference=evidence.excerpt_or_reference, created_at=evidence.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_evidence_entity(model)

    def update_evidence(self, evidence: AuditEvidence) -> AuditEvidence:
        model = self.session.get(AuditEvidenceModel, evidence.id)
        if not model:
            raise ValueError(f"Evidence '{evidence.id}' not found.")
        model.title = evidence.title
        model.excerpt_or_reference = evidence.excerpt_or_reference
        model.finding_id = evidence.finding_id
        model.procedure_id = evidence.procedure_id
        model.bounding_box_json = self._evidence_meta_json(evidence)
        self.session.flush()
        return self._to_evidence_entity(model)

    def list_evidence_for_finding(self, finding_id: str) -> list[AuditEvidence]:
        stmt = select(AuditEvidenceModel).where(AuditEvidenceModel.finding_id == finding_id).order_by(AuditEvidenceModel.created_at.asc())
        return [self._to_evidence_entity(m) for m in self.session.scalars(stmt).all()]

    def get_evidence_by_id(self, evidence_id: str) -> AuditEvidence | None:
        model = self.session.get(AuditEvidenceModel, evidence_id)
        return self._to_evidence_entity(model) if model else None

    def list_evidence_for_procedure(self, procedure_id: str) -> list[AuditEvidence]:
        stmt = select(AuditEvidenceModel).where(AuditEvidenceModel.procedure_id == procedure_id).order_by(AuditEvidenceModel.created_at.asc())
        return [self._to_evidence_entity(m) for m in self.session.scalars(stmt).all()]

    def list_evidence_for_engagement(self, engagement_id: str) -> list[AuditEvidence]:
        stmt = select(AuditEvidenceModel).where(AuditEvidenceModel.engagement_id == engagement_id).order_by(AuditEvidenceModel.created_at.asc())
        return [self._to_evidence_entity(m) for m in self.session.scalars(stmt).all()]
