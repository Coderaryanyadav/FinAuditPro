"""Application service orchestrating Audit Planning, SA 320 Materiality, Risks, Procedures, Findings & Evidence."""

from uuid import uuid4

from finauditpro.application.audit_planning_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
    SetMaterialityDTO,
    UpdateFindingStatusDTO,
    UpdateProcedureStatusDTO,
)
from finauditpro.domain.audit_matrix_entities import (
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    FindingStatusEnum,
    MaterialityAssessment,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, InvalidStateTransitionError
from finauditpro.domain.materiality_engine import MaterialityEngine
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_event_repository import (
    AuditEventRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.engagement_repository import (
    EngagementRepository,
)

VALID_FINDING_TRANSITIONS: dict[FindingStatusEnum, set[FindingStatusEnum]] = {
    FindingStatusEnum.OPEN: {FindingStatusEnum.UNDER_REVIEW, FindingStatusEnum.REJECTED},
    FindingStatusEnum.UNDER_REVIEW: {
        FindingStatusEnum.ACCEPTED,
        FindingStatusEnum.RESOLVED,
        FindingStatusEnum.REJECTED,
        FindingStatusEnum.CARRIED_FORWARD,
        FindingStatusEnum.OPEN,
    },
    FindingStatusEnum.ACCEPTED: {
        FindingStatusEnum.RESOLVED,
        FindingStatusEnum.CARRIED_FORWARD,
        FindingStatusEnum.UNDER_REVIEW,
    },
    FindingStatusEnum.RESOLVED: {FindingStatusEnum.UNDER_REVIEW},
    FindingStatusEnum.REJECTED: {FindingStatusEnum.UNDER_REVIEW},
    FindingStatusEnum.CARRIED_FORWARD: {FindingStatusEnum.UNDER_REVIEW},
}


class AuditPlanningService:
    """Service orchestrating SA 320 Materiality, Qualitative Risk Register, Procedures & Unified Findings."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def set_materiality(self, dto: SetMaterialityDTO) -> MaterialityAssessment:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            matrix_repo = AuditMatrixRepository(session)
            latest = matrix_repo.get_latest_materiality(dto.engagement_id)
            next_version = (latest.version + 1) if latest else 1

            assessment = MaterialityEngine.calculate(
                engagement_id=dto.engagement_id,
                benchmark_type=dto.benchmark_type,
                benchmark_amount_paise=dto.benchmark_amount_paise,
                overall_percentage=dto.overall_percentage,
                performance_percentage=dto.performance_percentage,
                trivial_percentage=dto.trivial_percentage,
                benchmark_source=dto.benchmark_source,
                methodology_notes=dto.methodology_notes,
                version=next_version,
                created_by=dto.created_by,
            )

            created = matrix_repo.add_materiality(assessment)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="MaterialityAssessment",
                    entity_id=created.id,
                    action="MATERIALITY_SET",
                    payload={"version": created.version, "om_paise": created.overall_materiality_paise},
                    user_id=dto.created_by,
                )
            )
            return created

    def get_latest_materiality(self, engagement_id: str) -> MaterialityAssessment | None:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.get_latest_materiality(engagement_id)

    def list_materiality_history(self, engagement_id: str) -> list[MaterialityAssessment]:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.list_materiality_history(engagement_id)

    def create_risk(self, dto: CreateRiskDTO) -> AuditRisk:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            risk = AuditRisk(
                engagement_id=dto.engagement_id,
                risk_code=dto.risk_code,
                title=dto.title,
                category=dto.category,
                description=dto.description,
                assertions=dto.assertions,
                inherent_risk=dto.inherent_risk,
                control_risk=dto.control_risk,
                is_significant_risk=dto.is_significant_risk,
                planned_response=dto.planned_response,
            )
            risk.calculate_romm()

            matrix_repo = AuditMatrixRepository(session)
            created = matrix_repo.add_risk(risk)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditRisk",
                    entity_id=created.id,
                    action="RISK_CREATED",
                    payload={"risk_code": created.risk_code, "derived_romm": created.derived_romm.value},
                    user_id="Auditor",
                )
            )
            return created

    def list_risks(self, engagement_id: str) -> list[AuditRisk]:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.list_risks_for_engagement(engagement_id)

    def create_procedure(self, dto: CreateProcedureDTO) -> AuditProcedure:
        with self.db_manager.session_scope() as session:
            eng_repo = EngagementRepository(session)
            if not eng_repo.get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            proc = AuditProcedure(
                engagement_id=dto.engagement_id,
                procedure_code=dto.procedure_code,
                objective=dto.objective,
                procedure_type=dto.procedure_type,
                instructions=dto.instructions,
                evidence_requirement=dto.evidence_requirement,
                linked_risk_ids=dto.linked_risk_ids,
                assertions=dto.assertions,
                preparer=dto.preparer,
            )

            matrix_repo = AuditMatrixRepository(session)
            created = matrix_repo.add_procedure(proc)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditProcedure",
                    entity_id=created.id,
                    action="PROCEDURE_CREATED",
                    payload={"code": created.procedure_code},
                    user_id=dto.preparer,
                )
            )
            return created

    def update_procedure_status(self, dto: UpdateProcedureStatusDTO) -> AuditProcedure:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            existing = matrix_repo.get_procedure_by_id(dto.procedure_id)
            if not existing:
                raise EntityNotFoundError("AuditProcedure", dto.procedure_id)

            existing.status = dto.status
            if dto.result_summary is not None:
                existing.result_summary = dto.result_summary
            if dto.conclusion is not None:
                existing.conclusion = dto.conclusion
            if dto.reviewer is not None:
                existing.reviewer = dto.reviewer

            updated = matrix_repo.update_procedure(existing)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=existing.engagement_id,
                    entity_name="AuditProcedure",
                    entity_id=updated.id,
                    action="PROCEDURE_STATUS_UPDATED",
                    payload={"status": updated.status.value},
                    user_id=dto.reviewer or "Auditor",
                )
            )
            return updated

    def list_procedures(self, engagement_id: str) -> list[AuditProcedure]:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.list_procedures_for_engagement(engagement_id)

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
                amount_paise=dto.amount_paise,
                affected_account=dto.affected_account,
                assertion=dto.assertion,
                recommendation=dto.recommendation,
                status=FindingStatusEnum.OPEN,
                preparer=dto.preparer,
                source=dto.source,
                is_ai_generated=dto.is_ai_generated,
                prior_engagement_finding_id=dto.prior_engagement_finding_id,
            )

            matrix_repo = AuditMatrixRepository(session)
            created = matrix_repo.add_finding(finding)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditFinding",
                    entity_id=created.id,
                    action="FINDING_CREATED",
                    payload={"title": created.title, "source": created.source.value},
                    user_id=dto.preparer,
                )
            )
            return created

    def update_finding_status(self, dto: UpdateFindingStatusDTO) -> AuditFinding:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            existing = matrix_repo.get_finding_by_id(dto.finding_id)
            if not existing:
                raise EntityNotFoundError("AuditFinding", dto.finding_id)

            current_status = existing.status
            target_status = dto.new_status

            allowed_targets = VALID_FINDING_TRANSITIONS.get(current_status, set())
            if target_status not in allowed_targets and target_status != current_status:
                raise InvalidStateTransitionError("AuditFinding", current_status.value, target_status.value)

            existing.status = target_status
            if dto.reviewer is not None:
                existing.reviewer = dto.reviewer
            if dto.recommendation is not None:
                existing.recommendation = dto.recommendation

            updated = matrix_repo.update_finding(existing)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=existing.engagement_id,
                    entity_name="AuditFinding",
                    entity_id=updated.id,
                    action="FINDING_STATUS_TRANSITION",
                    payload={"from": current_status.value, "to": updated.status.value},
                    user_id=dto.reviewer or "Auditor",
                )
            )
            return updated

    def list_findings(self, engagement_id: str) -> list[AuditFinding]:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.list_findings_for_engagement(engagement_id)

    def attach_evidence(self, dto: AttachEvidenceDTO) -> AuditEvidence:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            evidence = AuditEvidence(
                engagement_id=dto.engagement_id,
                finding_id=dto.finding_id,
                procedure_id=dto.procedure_id,
                document_id=dto.document_id,
                dataset_id=dto.dataset_id,
                page_number=dto.page_number,
                row_index=dto.row_index,
                bounding_box_json=dto.bounding_box_json,
                title=dto.title,
                excerpt_or_reference=dto.excerpt_or_reference,
            )
            created = matrix_repo.add_evidence(evidence)
            audit_repo = AuditEventRepository(session)
            audit_repo.add(
                AuditEvent(
                    id=str(uuid4()),
                    engagement_id=dto.engagement_id,
                    entity_name="AuditEvidence",
                    entity_id=created.id,
                    action="EVIDENCE_ATTACHED",
                    payload={"title": created.title},
                    user_id="Auditor",
                )
            )
            return created

    def list_evidence_for_finding(self, finding_id: str) -> list[AuditEvidence]:
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            return matrix_repo.list_evidence_for_finding(finding_id)
