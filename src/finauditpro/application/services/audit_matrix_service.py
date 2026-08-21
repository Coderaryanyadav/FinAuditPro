"""Audit Matrix application service for Risks, Procedures, Findings, and Evidence."""

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
    UpdateProcedureStatusDTO,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    EngagementRepository,
)


class AuditMatrixService:
    """Service handling Risk Register, Audit Procedures, Findings logging, and Evidence linking."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def create_risk(self, dto: CreateRiskDTO) -> AuditRisk:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

        assertions_list = getattr(dto, "assertions", None) or ([dto.assertion] if hasattr(dto, "assertion") else [AssertionEnum.COMPLETENESS])

        risk = AuditRisk(
            engagement_id=dto.engagement_id,
            risk_code=dto.risk_code,
            title=getattr(dto, "title", f"Risk {dto.risk_code}"),
            category=dto.category,
            description=dto.description,
            assertions=assertions_list,
            inherent_risk=dto.inherent_risk,
            control_risk=dto.control_risk,
            severity=getattr(dto, "severity", RiskSeverityEnum.HIGH),
            risk_response=dto.risk_response,
        )
        risk.calculate_romm()

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            saved_risk = repo.add_risk(risk)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="Auditor",
                    action="Audit Risk Identified",
                    details=f"Identified Risk '{saved_risk.risk_code}': {saved_risk.description} (Assertion: {saved_risk.assertion.value})",
                )
            )

        return saved_risk

    def list_risks_for_engagement(self, engagement_id: str) -> list[AuditRisk]:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_risks_for_engagement(engagement_id)

    def create_procedure(self, dto: CreateProcedureDTO) -> AuditProcedure:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

        linked_risks = getattr(dto, "linked_risk_ids", None) or ([dto.risk_id] if getattr(dto, "risk_id", None) else [])
        assertions_list = getattr(dto, "assertions", None) or ([dto.assertion] if hasattr(dto, "assertion") else [AssertionEnum.COMPLETENESS])

        proc = AuditProcedure(
            engagement_id=dto.engagement_id,
            linked_risk_ids=linked_risks,
            procedure_code=dto.procedure_code,
            objective=dto.objective,
            assertions=assertions_list,
            procedure_type=dto.procedure_type,
            instructions=dto.instructions,
            status=ProcedureStatusEnum.NOT_STARTED,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            saved_proc = repo.add_procedure(proc)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="Auditor",
                    action="Audit Procedure Created",
                    details=f"Created Procedure '{saved_proc.procedure_code}': {saved_proc.objective}",
                )
            )

        return saved_proc

    def list_procedures_for_engagement(self, engagement_id: str) -> list[AuditProcedure]:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_procedures_for_engagement(engagement_id)

    def update_procedure_status(self, dto: UpdateProcedureStatusDTO) -> AuditProcedure:
        proc = AuditProcedure(
            id=dto.procedure_id,
            engagement_id="",
            procedure_code="",
            objective="",
            status=dto.status,
            result_summary=dto.result_summary,
            conclusion=dto.conclusion,
            preparer=dto.preparer,
            reviewer=dto.reviewer,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            updated_proc = repo.update_procedure(proc)
            return updated_proc

    def create_finding(self, dto: CreateFindingDTO) -> AuditFinding:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

        finding = AuditFinding(
            engagement_id=dto.engagement_id,
            procedure_id=dto.procedure_id,
            risk_id=dto.risk_id,
            title=dto.title,
            description=dto.description,
            category=dto.category,
            severity=dto.severity,
            monetary_amount=dto.monetary_amount,
            affected_account=dto.affected_account,
            assertion=dto.assertion,
            recommendation=dto.recommendation,
            status=dto.status,
            preparer=dto.preparer,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            saved_finding = repo.add_finding(finding)

            audit_repo = AuditEventRepository(session)
            amt_display = saved_finding.monetary_amount.formatted if hasattr(saved_finding.monetary_amount, "formatted") else (f"INR {saved_finding.monetary_amount:,.2f}" if saved_finding.monetary_amount is not None else "INR 0.00")
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.preparer,
                    action="Audit Finding Logged",
                    details=f"Logged Audit Finding '{saved_finding.title}' ({amt_display}, Severity: {saved_finding.severity.value})",
                )
            )

        return saved_finding

    def list_findings_for_engagement(self, engagement_id: str) -> list[AuditFinding]:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_findings_for_engagement(engagement_id)

    def attach_evidence(self, dto: AttachEvidenceDTO) -> AuditEvidence:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

        ev = AuditEvidence(
            engagement_id=dto.engagement_id,
            finding_id=dto.finding_id,
            procedure_id=dto.procedure_id,
            document_id=dto.document_id,
            dataset_id=dto.dataset_id,
            row_index=dto.row_index,
            page_number=dto.page_number,
            title=dto.title,
            excerpt_or_reference=dto.excerpt_or_reference,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            saved_ev = repo.add_evidence(ev)

            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor="Auditor",
                    action="Evidence Item Attached",
                    details=f"Attached evidence '{saved_ev.title}' to matrix",
                )
            )

        return saved_ev

    def list_evidence_for_engagement(self, engagement_id: str) -> list[AuditEvidence]:
        with self.db_manager.session_scope() as session:
            repo = AuditMatrixRepository(session)
            return repo.list_evidence_for_engagement(engagement_id)
