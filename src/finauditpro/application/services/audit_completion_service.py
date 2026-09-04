"""Application Service for Phase D Audit Completion Workflows under Standards on Auditing (SA 450, SA 570, SA 520, SA 580, SA 560)."""

import json
from uuid import uuid4

from finauditpro.application.audit_completion_dtos import (
    CreateGoingConcernAssessmentDTO,
    CreateSubsequentEventDTO,
    FinalAnalyticalReviewDTO,
    FinancialMisstatementDTO,
    GoingConcernAssessmentDTO,
    GoingConcernMitigationDTO,
    ManagementRepresentationLetterDTO,
    RatioComparisonLineDTO,
    SA450EvaluationSummaryDTO,
    SubsequentEventDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.representation_and_events_service import (
    RepresentationAndEventsService,
)
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.domain.audit_completion_entities import (
    FinancialMisstatement,
    GoingConcernAssessment,
    GoingConcernMitigation,
    MisstatementStatusEnum,
    MisstatementTypeEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    ProfitAndLossStatement,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)


class AuditCompletionService:
    """Orchestrates comprehensive Audit Completion procedures across SA 450, SA 570, SA 520, SA 580, and SA 560."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager
        self._rep_service = RepresentationAndEventsService(db_manager)

    # -------------------------------------------------------------
    # 1. SA 450: Evaluation of Misstatements
    # -------------------------------------------------------------

    def evaluate_sa450_misstatements(self, engagement_id: str) -> SA450EvaluationSummaryDTO:
        with self.db_manager.session_scope() as session:
            core_repo = CoreAuditEngineRepository(session)
            mat_repo = AuditMatrixRepository(session)

            core_misstatements = core_repo.list_misstatements_for_engagement(engagement_id)
            mat_assessment = mat_repo.get_materiality(engagement_id)

            overall_mat_paise = mat_assessment.overall_materiality_paise if mat_assessment else 0
            perf_mat_paise = (
                mat_assessment.performance_materiality_paise if mat_assessment else 0
            )
            trivial_paise = (
                mat_assessment.clearly_trivial_threshold_paise if mat_assessment else 0
            )

            converted_misstatements = []
            for m in core_misstatements:
                m_type = MisstatementTypeEnum.FACTUAL
                if hasattr(m.misstatement_type, "value"):
                    for t in MisstatementTypeEnum:
                        if t.value == m.misstatement_type.value or t.name == m.misstatement_type.value:
                            m_type = t
                            break

                status_enum = (
                    MisstatementStatusEnum.CORRECTED
                    if m.is_corrected
                    else MisstatementStatusEnum.UNCORRECTED
                )
                converted_misstatements.append(
                    FinancialMisstatement(
                        id=m.id,
                        engagement_id=m.engagement_id,
                        misstatement_number=f"MISST-{m.id[:6]}",
                        misstatement_type=m_type,
                        status=status_enum,
                        title=m.account_name or m.account_code,
                        description=m.rationale or "Audit Misstatement",
                        affected_fs_area=m.schedule_iii_category or "Financial Statements",
                        amount_paise=m.amount_paise,
                    )
                )

            summary = AuditCompletionEngine.evaluate_sa450_misstatements(
                engagement_id=engagement_id,
                misstatements=converted_misstatements,
                overall_materiality_paise=overall_mat_paise,
                performance_materiality_paise=perf_mat_paise,
                clearly_trivial_threshold_paise=trivial_paise,
            )

            return SA450EvaluationSummaryDTO(
                engagement_id=engagement_id,
                overall_materiality_paise=summary.overall_materiality_paise,
                performance_materiality_paise=summary.performance_materiality_paise,
                clearly_trivial_threshold_paise=summary.clearly_trivial_threshold_paise,
                total_identified_misstatements=summary.total_identified_misstatements,
                total_corrected_misstatements=summary.total_corrected_misstatements,
                total_uncorrected_misstatements=summary.total_uncorrected_misstatements,
                total_uncorrected_amount_paise=summary.total_uncorrected_amount_paise,
                total_uncorrected_pnl_impact_paise=summary.total_uncorrected_pnl_impact_paise,
                total_uncorrected_bs_impact_paise=summary.total_uncorrected_bs_impact_paise,
                is_material_individually=summary.is_material_individually,
                is_material_in_aggregate=summary.is_material_in_aggregate,
                requires_opinion_modification=summary.requires_opinion_modification,
                audit_conclusion=summary.audit_conclusion.value,
                misstatements=[
                    FinancialMisstatementDTO(
                        id=m.id,
                        engagement_id=m.engagement_id,
                        misstatement_number=m.misstatement_number,
                        misstatement_type=m.misstatement_type.value,
                        status=m.status.value,
                        title=m.title,
                        description=m.description,
                        affected_fs_area=m.affected_fs_area,
                        amount_paise=m.amount_paise,
                        is_pnl_impact=m.is_pnl_impact,
                        pnl_overstatement_paise=m.pnl_overstatement_paise,
                        is_balance_sheet_impact=m.is_balance_sheet_impact,
                        balance_sheet_overstatement_paise=m.balance_sheet_overstatement_paise,
                        is_clearly_trivial=m.is_clearly_trivial,
                        working_paper_ref=m.working_paper_ref,
                        linked_aje_id=m.linked_aje_id,
                        management_response=m.management_response,
                        created_at=m.created_at,
                    )
                    for m in converted_misstatements
                ],
            )

    # -------------------------------------------------------------
    # 2. SA 570: Going Concern Assessment & Partner Sign-off
    # -------------------------------------------------------------

    def create_or_update_going_concern_assessment(
        self,
        engagement_id: str,
        dto: CreateGoingConcernAssessmentDTO,
    ) -> GoingConcernAssessmentDTO:
        if dto.partner_signoff:
            SecurityContext.enforce_permission("going_concern:partner_signoff", [RoleEnum.PARTNER, RoleEnum.ADMIN])
        else:
            SecurityContext.enforce_permission(
                "going_concern:update", [RoleEnum.SENIOR, RoleEnum.MANAGER, RoleEnum.PARTNER, RoleEnum.ADMIN]
            )

        mitigations = [
            GoingConcernMitigation(
                factor_title=m.factor_title,
                management_plan=m.management_plan,
                auditor_evaluation=m.auditor_evaluation,
                is_feasible=m.is_feasible,
            )
            for m in dto.mitigations
        ]

        risk_level, material_uncertainty, conclusion, rationale = (
            AuditCompletionEngine.evaluate_sa570_going_concern(
                has_operating_losses=dto.has_operating_losses,
                has_negative_operating_cashflow=dto.has_negative_operating_cashflow,
                has_negative_net_worth=dto.has_negative_net_worth,
                has_covenant_breaches=dto.has_covenant_breaches,
                has_delayed_statutory_dues=dto.has_delayed_statutory_dues,
                has_debt_maturity_unfunded=dto.has_debt_maturity_unfunded,
                current_ratio=dto.current_ratio,
                debt_equity_ratio=dto.debt_equity_ratio,
                mitigations=mitigations,
            )
        )

        entity = GoingConcernAssessment(
            engagement_id=engagement_id,
            has_operating_losses=dto.has_operating_losses,
            has_negative_operating_cashflow=dto.has_negative_operating_cashflow,
            has_negative_net_worth=dto.has_negative_net_worth,
            has_covenant_breaches=dto.has_covenant_breaches,
            has_delayed_statutory_dues=dto.has_delayed_statutory_dues,
            has_debt_maturity_unfunded=dto.has_debt_maturity_unfunded,
            current_ratio=dto.current_ratio,
            debt_equity_ratio=dto.debt_equity_ratio,
            solvency_risk_level=risk_level,
            material_uncertainty_identified=material_uncertainty,
            mitigations=mitigations,
            audit_conclusion=conclusion,
            conclusion_rationale=rationale,
            preparer=dto.preparer,
            reviewer=dto.reviewer,
            partner_signoff=dto.partner_signoff,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            saved = repo.save_going_concern_assessment(entity)
            return self._to_gc_dto(saved)

    def get_going_concern_assessment(self, engagement_id: str) -> GoingConcernAssessmentDTO | None:
        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            entity = repo.get_going_concern_assessment(engagement_id)
            return self._to_gc_dto(entity) if entity else None

    # -------------------------------------------------------------
    # 3. SA 520: Final Analytical Review
    # -------------------------------------------------------------

    def perform_final_analytical_review(
        self,
        engagement_id: str,
    ) -> FinalAnalyticalReviewDTO:
        with self.db_manager.session_scope() as session:
            fs_repo = FinancialStatementRepository(session)
            pkg = fs_repo.get_latest_package(engagement_id)
            if not pkg:
                raise ValueError(f"No financial statement package found for engagement {engagement_id}")

            if hasattr(pkg, "balance_sheet") and pkg.balance_sheet:
                bs = pkg.balance_sheet
            elif getattr(pkg, "balance_sheet_json", None) and pkg.balance_sheet_json != "{}":
                bs = BalanceSheet.model_validate_json(pkg.balance_sheet_json)
            else:
                bs = BalanceSheet(
                    engagement_id=engagement_id,
                    as_at_date="2024-03-31",
                )

            if hasattr(pkg, "profit_loss") and pkg.profit_loss:
                pnl = pkg.profit_loss
            elif getattr(pkg, "profit_loss_json", None) and pkg.profit_loss_json != "{}":
                pnl = ProfitAndLossStatement.model_validate_json(pkg.profit_loss_json)
            else:
                pnl = ProfitAndLossStatement(
                    engagement_id=engagement_id,
                    for_period_ended="2024-03-31",
                )

            ratio_lines = AuditCompletionEngine.compute_sa520_analytical_ratios(bs, pnl)
            has_unexplained = any(r.is_significant_variance for r in ratio_lines)

            return FinalAnalyticalReviewDTO(
                id=str(uuid4()),
                engagement_id=engagement_id,
                ratio_lines=[
                    RatioComparisonLineDTO(
                        ratio_name=r.ratio_name,
                        category=r.category.value,
                        current_year_value=r.current_year_value,
                        previous_year_value=r.previous_year_value,
                        variance_percentage=r.variance_percentage,
                        is_significant_variance=r.is_significant_variance,
                        auditor_explanation=r.auditor_explanation,
                    )
                    for r in ratio_lines
                ],
                has_unexplained_significant_variances=has_unexplained,
                overall_consistency_conclusion=(
                    "Financial statement relationships conform with audit findings."
                    if not has_unexplained
                    else "Significant variances noted; explanations documented in working papers."
                ),
                completed_by=SecurityContext.get_current_user_id() or "Auditor",
                reviewed_by=None,
                created_at=utc_now().isoformat(),
            )

    # -------------------------------------------------------------
    # 4. SA 580 & SA 560 Delegated Methods
    # -------------------------------------------------------------

    def generate_default_mrl(
        self,
        engagement_id: str,
        financial_year: str,
        requested_date: str | None = None,
    ) -> ManagementRepresentationLetterDTO:
        return self._rep_service.generate_default_mrl(engagement_id, financial_year, requested_date)

    def update_mrl_status(
        self,
        engagement_id: str,
        mrl_id: str,
        status: str,
        signed_date: str | None = None,
        signatory_name: str | None = None,
        signatory_designation: str | None = None,
        audit_report_date: str | None = None,
    ) -> ManagementRepresentationLetterDTO:
        return self._rep_service.update_mrl_status(
            engagement_id, mrl_id, status, signed_date, signatory_name, signatory_designation, audit_report_date
        )

    def get_mrl(self, engagement_id: str) -> ManagementRepresentationLetterDTO | None:
        return self._rep_service.get_mrl(engagement_id)

    def list_mrls(self, engagement_id: str) -> list[ManagementRepresentationLetterDTO]:
        return self._rep_service.list_mrls(engagement_id)

    def record_subsequent_event(
        self,
        engagement_id: str,
        dto: CreateSubsequentEventDTO,
    ) -> SubsequentEventDTO:
        return self._rep_service.record_subsequent_event(engagement_id, dto)

    def list_subsequent_events(self, engagement_id: str) -> list[SubsequentEventDTO]:
        return self._rep_service.list_subsequent_events(engagement_id)

    # -------------------------------------------------------------
    # Helper mappers
    # -------------------------------------------------------------

    def _to_gc_dto(self, entity: GoingConcernAssessment) -> GoingConcernAssessmentDTO:
        return GoingConcernAssessmentDTO(
            id=entity.id,
            engagement_id=entity.engagement_id,
            assessment_period_months=entity.assessment_period_months,
            has_operating_losses=entity.has_operating_losses,
            has_negative_operating_cashflow=entity.has_negative_operating_cashflow,
            has_negative_net_worth=entity.has_negative_net_worth,
            has_covenant_breaches=entity.has_covenant_breaches,
            has_delayed_statutory_dues=entity.has_delayed_statutory_dues,
            has_debt_maturity_unfunded=entity.has_debt_maturity_unfunded,
            current_ratio=entity.current_ratio,
            debt_equity_ratio=entity.debt_equity_ratio,
            solvency_risk_level=entity.solvency_risk_level.value,
            material_uncertainty_identified=entity.material_uncertainty_identified,
            mitigations=[
                GoingConcernMitigationDTO(
                    id=m.id,
                    factor_title=m.factor_title,
                    management_plan=m.management_plan,
                    auditor_evaluation=m.auditor_evaluation,
                    is_feasible=m.is_feasible,
                )
                for m in entity.mitigations
            ],
            audit_conclusion=entity.audit_conclusion.value,
            conclusion_rationale=entity.conclusion_rationale,
            preparer=entity.preparer,
            reviewer=entity.reviewer,
            partner_signoff=entity.partner_signoff,
            created_at=entity.created_at,
        )
