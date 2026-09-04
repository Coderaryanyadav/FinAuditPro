"""Application service orchestrating the Core Audit Engine: Testing, Exceptions, Misstatements, and Quality Gates."""

from typing import Any
from uuid import uuid4

from sqlalchemy import select

from finauditpro.application.core_audit_dtos import (
    CalculateAuditCompletenessDTO,
    CreateMisstatementDTO,
    EvaluateProcedureConclusionDTO,
    ExecuteSampleItemTestDTO,
    GenerateAssertionCoverageDTO,
    LinkMisstatementToAJEDTO,
    LogAuditExceptionDTO,
    ResolveAuditExceptionDTO,
)
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.audit_evaluation_engine import (
    build_assertion_coverage_report,
    build_audit_completeness_report,
)
from finauditpro.domain.audit_execution_entities import (
    AssertionCoverageReport,
    AuditCompletenessReport,
    AuditException,
    AuditMisstatement,
    AuditSampleItemTest,
    AuditTestOutcomeEnum,
    ExceptionStatusEnum,
    MisstatementAggregationSummary,
    MisstatementStatusEnum,
    ProcedureConclusionEnum,
)
from finauditpro.domain.audit_matrix_entities import ProcedureStatusEnum
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError, ValidationError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import MaterialityAssessmentModel, UserModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    AuditMatrixRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.account_mapping_repository import (
    AccountMappingRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)


class CoreAuditService:
    """Service managing the complete core audit chain from Risk/Assertion to Testing, Exceptions, and Misstatements."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def _get_current_user_name(self, session: Any) -> str:
        uid = SecurityContext.get_current_user_id()
        if not uid:
            return "Auditor"
        user = session.get(UserModel, uid)
        return user.username if user else uid

    def _get_current_user_and_role(self, session: Any) -> tuple[str, str]:
        sess = SecurityContext.get_current_session()
        uid = sess.user_id if sess else None
        role = sess.role.value if sess and sess.role else "Associate"
        if not uid:
            return "Auditor", role
        user = session.get(UserModel, uid)
        username = user.username if user else uid
        user_role = user.role if user else role
        return username, user_role

    def execute_sample_item_test(self, dto: ExecuteSampleItemTestDTO) -> AuditSampleItemTest:
        """Execute and record substantive testing on an individual sampled transaction."""
        diff = dto.actual_value_paise - dto.expected_value_paise
        test_outcome = dto.test_result
        if diff != 0 and test_outcome == AuditTestOutcomeEnum.PASS:
            test_outcome = AuditTestOutcomeEnum.EXCEPTION

        item = AuditSampleItemTest(
            id=str(uuid4()),
            procedure_id=dto.procedure_id,
            sample_plan_id=dto.sample_plan_id,
            item_identifier=dto.item_identifier,
            account_code=dto.account_code,
            expected_value_paise=dto.expected_value_paise,
            actual_value_paise=dto.actual_value_paise,
            difference_paise=diff,
            test_result=test_outcome,
            explanation=dto.explanation,
            evidence_ref=dto.evidence_ref,
        )

        with self.db_manager.session_scope() as session:
            repo = CoreAuditEngineRepository(session)
            item.tested_by = self._get_current_user_name(session)
            return repo.add_sample_item(item)

    def log_audit_exception(self, dto: LogAuditExceptionDTO) -> AuditException:
        """Log a formal audit exception arising from test failures or anomalous items."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            exc = AuditException(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                procedure_id=dto.procedure_id,
                sample_item_id=dto.sample_item_id,
                exception_code=dto.exception_code,
                title=dto.title,
                description=dto.description,
                amount_paise=dto.amount_paise,
                root_cause=dto.root_cause,
                evidence_id=dto.evidence_id,
                status=ExceptionStatusEnum.OPEN,
            )
            saved = CoreAuditEngineRepository(session).add_exception(exc)
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="AuditException",
                    entity_id=saved.id,
                    action="AUDIT_EXCEPTION_LOGGED",
                    payload={"code": saved.exception_code, "amount_paise": saved.amount_paise},
                    user_id=self._get_current_user_name(session),
                )
            )
            return saved

    def list_exceptions(self, engagement_id: str) -> list[AuditException]:
        """List all audit exceptions for an engagement."""
        with self.db_manager.session_scope() as session:
            return CoreAuditEngineRepository(session).list_exceptions_for_engagement(engagement_id)

    def resolve_audit_exception(self, dto: ResolveAuditExceptionDTO) -> AuditException:
        """Record management response and resolution for an audit exception."""
        with self.db_manager.session_scope() as session:
            repo = CoreAuditEngineRepository(session)
            exc = repo.get_exception_by_id(dto.exception_id)
            if not exc or exc.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditException", dto.exception_id)

            exc.management_response = dto.management_response
            exc.resolution = dto.resolution
            exc.is_resolved = dto.is_resolved
            exc.status = dto.status
            exc.reviewer = self._get_current_user_name(session)
            return repo.update_exception(exc)

    def create_misstatement(self, dto: CreateMisstatementDTO) -> AuditMisstatement:
        """Create a financial misstatement under SA 450 evaluation."""
        with self.db_manager.session_scope() as session:
            if not EngagementRepository(session).get_by_id(dto.engagement_id):
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            repo = CoreAuditEngineRepository(session)
            misst = AuditMisstatement(
                id=str(uuid4()),
                engagement_id=dto.engagement_id,
                exception_id=dto.exception_id,
                procedure_id=dto.procedure_id,
                account_code=dto.account_code,
                account_name=dto.account_name,
                schedule_iii_category=dto.schedule_iii_category,
                misstatement_type=dto.misstatement_type,
                status=MisstatementStatusEnum.UNCORRECTED,
                amount_paise=dto.amount_paise,
                is_corrected=False,
                rationale=dto.rationale,
                created_by=self._get_current_user_name(session),
            )
            saved = repo.add_misstatement(misst)

            if dto.exception_id:
                exc = repo.get_exception_by_id(dto.exception_id)
                if exc:
                    exc.status = ExceptionStatusEnum.ESCALATED_TO_MISSTATEMENT
                    repo.update_exception(exc)

            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    entity_name="AuditMisstatement",
                    entity_id=saved.id,
                    action="MISSTATEMENT_CREATED",
                    payload={"account": saved.account_code, "amount_paise": saved.amount_paise},
                    user_id=saved.created_by,
                )
            )
            return saved

    def link_misstatement_to_aje(self, dto: LinkMisstatementToAJEDTO) -> AuditMisstatement:
        """Link a corrected misstatement to an approved Audit Adjusting Journal Entry (AJE)."""
        with self.db_manager.session_scope() as session:
            repo = CoreAuditEngineRepository(session)
            misst = repo.get_misstatement_by_id(dto.misstatement_id)
            if not misst or misst.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditMisstatement", dto.misstatement_id)

            misst.linked_aje_id = dto.aje_id
            misst.linked_aje_number = dto.aje_number
            misst.is_corrected = True
            misst.status = MisstatementStatusEnum.CORRECTED
            return repo.update_misstatement(misst)

    def aggregate_misstatements(self, engagement_id: str) -> MisstatementAggregationSummary:
        """Aggregate misstatements against configured SA 320 engagement materiality thresholds."""
        with self.db_manager.session_scope() as session:
            stmt = (
                select(MaterialityAssessmentModel)
                .where(MaterialityAssessmentModel.engagement_id == engagement_id)
                .order_by(MaterialityAssessmentModel.created_at.desc())
            )
            mat_model = session.scalars(stmt).first()
            overall_mat = mat_model.overall_materiality_paise if mat_model else 100000000
            perf_mat = mat_model.performance_materiality_paise if mat_model else 75000000
            trivial_thr = mat_model.clearly_trivial_threshold_paise if mat_model else 5000000

            misstatements = CoreAuditEngineRepository(session).list_misstatements_for_engagement(
                engagement_id
            )

            tot_factual = sum(
                m.amount_paise for m in misstatements if m.misstatement_type == "Factual"
            )
            tot_judgmental = sum(
                m.amount_paise for m in misstatements if m.misstatement_type == "Judgmental"
            )
            tot_projected = sum(
                m.amount_paise for m in misstatements if m.misstatement_type == "Projected"
            )
            tot_known = tot_factual + tot_judgmental
            tot_uncorrected = sum(m.amount_paise for m in misstatements if not m.is_corrected)
            tot_corrected = sum(m.amount_paise for m in misstatements if m.is_corrected)
            headroom = max(0, overall_mat - tot_uncorrected)

            return MisstatementAggregationSummary(
                overall_materiality_paise=overall_mat,
                performance_materiality_paise=perf_mat,
                clearly_trivial_threshold_paise=trivial_thr,
                total_factual_paise=tot_factual,
                total_judgmental_paise=tot_judgmental,
                total_projected_paise=tot_projected,
                total_known_misstatement_paise=tot_known,
                total_uncorrected_misstatement_paise=tot_uncorrected,
                total_corrected_misstatement_paise=tot_corrected,
                remaining_materiality_headroom_paise=headroom,
                is_material_misstatement_present=tot_uncorrected >= perf_mat,
                requires_modified_opinion=tot_uncorrected >= overall_mat,
            )

    def evaluate_procedure_conclusion(self, dto: EvaluateProcedureConclusionDTO) -> Any:
        """Enforce conclusion consistency guardrails: Test = FAIL/EXCEPTION cannot have Conclusion = PASS without override."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            proc = matrix_repo.get_procedure_by_id(dto.procedure_id)
            if not proc or proc.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditProcedure", dto.procedure_id)

            sample_items = CoreAuditEngineRepository(session).list_sample_items_for_procedure(
                dto.procedure_id
            )
            has_failures = any(
                item.test_result in (AuditTestOutcomeEnum.FAIL, AuditTestOutcomeEnum.EXCEPTION)
                for item in sample_items
            )

            if (
                has_failures
                and dto.conclusion == ProcedureConclusionEnum.PASS
                and (not dto.override_reason or not dto.override_reason.strip())
            ):
                raise ValidationError(
                    f"Inconsistent Conclusion Violation: Procedure '{proc.procedure_code}' has failed sample items or exceptions. "
                    f"Cannot mark conclusion as PASS without an explicit documented override rationale."
                )

            if getattr(proc, "requires_evidence", True):
                evidences = matrix_repo.list_evidence_for_engagement(dto.engagement_id)
                has_ev = any(e.procedure_id == dto.procedure_id for e in evidences)
                if not has_ev and (not dto.override_reason or not dto.override_reason.strip()):
                    raise ValidationError(
                        f"Evidence Requirement Violation: Procedure '{proc.procedure_code}' requires audit evidence attachments before marking Completed."
                    )

            proc.conclusion = dto.conclusion.value
            proc.result_summary = dto.result_summary
            proc.status = ProcedureStatusEnum.COMPLETED
            proc.preparer = self._get_current_user_name(session)
            proc.prepared_date = utc_now()
            return matrix_repo.update_procedure(proc)

    def review_procedure(
        self, engagement_id: str, procedure_id: str, decision: str = "CLEAR"
    ) -> Any:
        """Review and sign-off on an audit procedure enforcing Maker-Checker segregation of duties."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            proc = matrix_repo.get_procedure_by_id(procedure_id)
            if not proc or proc.engagement_id != engagement_id:
                raise EntityNotFoundError("AuditProcedure", procedure_id)

            reviewer_name, reviewer_role = self._get_current_user_and_role(session)
            if proc.preparer and proc.preparer == reviewer_name:
                raise ValidationError(
                    f"Segregation of Duties Violation: Preparer '{proc.preparer}' cannot review or approve their own audit procedure '{proc.procedure_code}'."
                )

            if reviewer_role not in ("Senior", "Manager", "Partner", "Administrator"):
                raise ValidationError(
                    f"Unauthorized: Role '{reviewer_role}' does not have authority to review audit procedures. Must be Senior, Manager, or Partner."
                )

            proc.reviewer = reviewer_name
            proc.reviewed_date = utc_now()
            if decision.upper() in ("CLEAR", "CLEARED"):
                proc.status = ProcedureStatusEnum.CLEARED
            else:
                proc.status = ProcedureStatusEnum.REVIEWED
            return matrix_repo.update_procedure(proc)

    def generate_assertion_coverage_matrix(
        self, dto: GenerateAssertionCoverageDTO
    ) -> AssertionCoverageReport:
        """Generate comprehensive Assertion Coverage Matrix and identify gaps across all audit areas."""
        with self.db_manager.session_scope() as session:
            mappings = AccountMappingRepository(session).list_mappings_for_engagement(
                dto.engagement_id
            )
            matrix_repo = AuditMatrixRepository(session)
            risks = matrix_repo.list_risks_for_engagement(dto.engagement_id)
            procs = matrix_repo.list_procedures_for_engagement(dto.engagement_id)
            evidences = matrix_repo.list_evidence_for_engagement(dto.engagement_id)

            areas = sorted(
                {m.schedule_iii_category for m in mappings if m.schedule_iii_category}
                or {
                    "Revenue from Operations",
                    "Trade Receivables",
                    "Inventories",
                    "Property, Plant and Equipment",
                    "Trade Payables",
                    "Cash and Cash Equivalents",
                    "Long-Term Borrowings",
                    "Employee Benefits Expense",
                }
            )
            return build_assertion_coverage_report(areas, risks, procs, evidences)

    def calculate_audit_completeness(
        self, dto: CalculateAuditCompletenessDTO
    ) -> AuditCompletenessReport:
        """Deterministic 6-factor audit completeness calculation and orphan detector."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            core_repo = CoreAuditEngineRepository(session)
            return build_audit_completeness_report(
                engagement_id=dto.engagement_id,
                risks=matrix_repo.list_risks_for_engagement(dto.engagement_id),
                procs=matrix_repo.list_procedures_for_engagement(dto.engagement_id),
                evidences=matrix_repo.list_evidence_for_engagement(dto.engagement_id),
                exceptions=core_repo.list_exceptions_for_engagement(dto.engagement_id),
                misstatements=core_repo.list_misstatements_for_engagement(dto.engagement_id),
            )
