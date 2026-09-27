"""Application service orchestrating Audit Planning, SA 320 Materiality, Risks, Procedures, Findings & Evidence."""

from uuid import uuid4

from finauditpro.application.audit_matrix_dtos import CalculateMaterialityDTO
from finauditpro.application.audit_planning_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
    SetMaterialityDTO,
    UpdateFindingStatusDTO,
    UpdateProcedureStatusDTO,
)
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    FindingStatusEnum,
    MaterialityAssessment,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, InvalidStateTransitionError
from finauditpro.domain.risk_procedure_engine import ProcedureTemplate, RiskProcedureEngine
from finauditpro.domain.working_paper_entities import (
    FileCategoryEnum,
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    EngagementRepository,
    WorkingPaperRepository,
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
        mat_service = MaterialityService(self.db_manager)
        return mat_service.calculate_and_save_materiality(
            CalculateMaterialityDTO(
                engagement_id=dto.engagement_id,
                benchmark_type=dto.benchmark_type,
                benchmark_amount=dto.benchmark_amount_paise / 100.0,
                overall_percentage=dto.overall_percentage,
                performance_percentage=dto.performance_percentage,
                trivial_percentage=dto.trivial_percentage,
                created_by=dto.created_by,
            )
        )

    def get_latest_materiality(self, engagement_id: str) -> MaterialityAssessment | None:
        return MaterialityService(self.db_manager).get_latest_materiality(engagement_id)

    def list_materiality_history(self, engagement_id: str) -> list[MaterialityAssessment]:
        return MaterialityService(self.db_manager).list_materiality_history(engagement_id)

    def create_risk(self, dto: CreateRiskDTO) -> AuditRisk:
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
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

            created = AuditMatrixRepository(session).add_risk(risk)
            AuditEventRepository(session).add(
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
            return AuditMatrixRepository(session).list_risks_for_engagement(engagement_id)

    def create_procedure(self, dto: CreateProcedureDTO) -> AuditProcedure:
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
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
            created = AuditMatrixRepository(session).add_procedure(proc)
            AuditEventRepository(session).add(
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
            AuditEventRepository(session).add(
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
            return AuditMatrixRepository(session).list_procedures_for_engagement(engagement_id)

    def create_finding(self, dto: CreateFindingDTO) -> AuditFinding:
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
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
            created = AuditMatrixRepository(session).add_finding(finding)
            AuditEventRepository(session).add(
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

            current_status, target_status = existing.status, dto.new_status
            allowed_targets = VALID_FINDING_TRANSITIONS.get(current_status, set())
            if target_status not in allowed_targets and target_status != current_status:
                raise InvalidStateTransitionError("AuditFinding", current_status.value, target_status.value)

            existing.status = target_status
            if dto.reviewer is not None:
                existing.reviewer = dto.reviewer
            if dto.recommendation is not None:
                existing.recommendation = dto.recommendation

            updated = matrix_repo.update_finding(existing)
            AuditEventRepository(session).add(
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
            return AuditMatrixRepository(session).list_findings_for_engagement(engagement_id)

    def attach_evidence(self, dto: AttachEvidenceDTO) -> AuditEvidence:
        with self.db_manager.session_scope() as session:
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
            created = AuditMatrixRepository(session).add_evidence(evidence)
            AuditEventRepository(session).add(
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
            return AuditMatrixRepository(session).list_evidence_for_finding(finding_id)

    def get_relevant_assertions_for_area(self, area: str, category: str = "") -> list[AssertionEnum]:
        return RiskProcedureEngine.get_relevant_assertions(area, category)

    def get_recommended_procedures(
        self,
        area: str,
        risk_category: str = "",
        assertions: list[AssertionEnum] | None = None,
        romm: RiskSeverityEnum = RiskSeverityEnum.MEDIUM,
    ) -> list[ProcedureTemplate]:
        return RiskProcedureEngine.get_recommended_procedures(area, risk_category, assertions, romm)

    def generate_procedures_for_risk(
        self,
        engagement_id: str,
        risk_id: str,
        selected_templates: list[str] | None = None,
        preparer: str = "Auditor",
    ) -> list[AuditProcedure]:
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(engagement_id):
                raise EntityNotFoundError("Engagement", engagement_id)
            matrix_repo = AuditMatrixRepository(session)
            wp_repo = WorkingPaperRepository(session)
            audit_repo = AuditEventRepository(session)
            risk = matrix_repo.get_risk_by_id(risk_id)
            if not risk or risk.engagement_id != engagement_id:
                raise EntityNotFoundError("AuditRisk", risk_id)

            candidates = RiskProcedureEngine.get_recommended_procedures(
                risk.financial_statement_area, risk.category, risk.assertions, risk.derived_romm
            )
            templates = [t for t in candidates if not selected_templates or t.code_prefix in selected_templates]
            generated_procs = []
            for tmpl in templates:
                p_code = f"{tmpl.code_prefix}-{risk.risk_code}"
                proc = AuditProcedure(
                    engagement_id=engagement_id,
                    procedure_code=p_code,
                    objective=tmpl.objective,
                    procedure_type=tmpl.procedure_type,
                    instructions=tmpl.instructions,
                    account_area=risk.financial_statement_area,
                    evidence_requirement=tmpl.evidence_requirement,
                    population_definition=tmpl.population_definition,
                    methodology=tmpl.methodology,
                    linked_risk_ids=[risk.id],
                    assertions=risk.assertions or tmpl.assertions,
                    preparer=preparer,
                )
                saved_proc = matrix_repo.add_procedure(proc)
                wp = wp_repo.add_working_paper(
                    WorkingPaper(
                        engagement_id=engagement_id,
                        index_reference=f"{tmpl.working_paper_ref}-{risk.risk_code}",
                        title=f"{tmpl.working_paper_title} ({risk.risk_code})",
                        area=risk.financial_statement_area,
                        file_category=FileCategoryEnum.CURRENT_FILE,
                        status=WorkingPaperStatusEnum.DRAFT,
                        preparer_id=preparer,
                    )
                )
                for order, s_title, s_content in tmpl.wp_sections:
                    wp_repo.add_section(
                        WorkingPaperSection(
                            working_paper_id=wp.id,
                            section_order=order,
                            title=s_title,
                            content_markdown=s_content,
                        )
                    )
                wp_repo.add_link(str(uuid4()), wp.id, "PROCEDURE", saved_proc.id)
                wp_repo.add_link(str(uuid4()), wp.id, "RISK", risk.id)
                audit_repo.add(
                    AuditEvent(
                        id=str(uuid4()),
                        engagement_id=engagement_id,
                        entity_name="AuditProcedure",
                        entity_id=saved_proc.id,
                        action="PROCEDURE_GENERATED_FROM_RISK",
                        payload={"risk_id": risk.id, "procedure_code": saved_proc.procedure_code, "wp_id": wp.id},
                        user_id=preparer,
                    )
                )
                generated_procs.append(saved_proc)
            return generated_procs
