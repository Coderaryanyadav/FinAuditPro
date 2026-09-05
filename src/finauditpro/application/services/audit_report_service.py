"""Service managing the lifecycle, opinion decisions, and partner approvals of Audit Reports (Phase E)."""

import json
from typing import Any
from uuid import uuid4

from finauditpro.application.audit_report_dtos import (
    AddBasisOfOpinionItemDTO,
    AddEmphasisOrOtherMatterDTO,
    AddKeyAuditMatterDTO,
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
    UpdateAuditReportWorkpaperDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    AuditReportWorkpaper,
    BasisOfOpinionItem,
    EmphasisOrOtherMatter,
    KeyAuditMatter,
    ReportWorkpaperStatusEnum,
)
from finauditpro.domain.clock import utc_now
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import (
    EntityNotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.opinion_consistency_engine import (
    OpinionConsistencyEngine,
    OpinionEvaluationResult,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    EngagementRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_adjustment_repository import (
    AuditAdjustmentRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_report_repository import (
    AuditReportRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import (
    ComplianceRepository,
)
from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
    CoreAuditEngineRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import (
    FinancialDataRepository,
)
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)


class AuditReportService:
    """Orchestrates AuditReportWorkpaper lifecycle, opinion validation, and partner sign-off."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def get_or_create_report_workpaper(
        self, dto: CreateAuditReportWorkpaperDTO
    ) -> AuditReportWorkpaper:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            existing = repo.get_report_workpaper_for_engagement(dto.engagement_id)
            if existing:
                return existing

            eng = EngagementRepository(session).get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)

            cli = ClientRepository(session).get_by_id(eng.client_id)
            client_name = cli.name if cli else "Client Entity"
            mat = AuditMatrixRepository(session).get_materiality(dto.engagement_id)
            mat_paise = mat.overall_materiality_paise if mat else 0

            compl_repo = AuditCompletionRepository(session)
            gc = compl_repo.get_going_concern_assessment(dto.engagement_id)
            gc_raw = getattr(gc, "audit_conclusion", getattr(gc, "conclusion", "Not Evaluated")) if gc else "Not Evaluated"
            gc_concl = getattr(gc_raw, "value", str(gc_raw))
            mrls = compl_repo.list_mrls(dto.engagement_id)
            mrl_status = getattr(mrls[0].status, "value", str(mrls[0].status)) if mrls else "Missing"

            current_user = SecurityContext.get_current_session()
            preparer = current_user.username if current_user else "auditor"

            wp = AuditReportWorkpaper(
                engagement_id=dto.engagement_id,
                reporting_framework=dto.reporting_framework,
                financial_year=str(eng.financial_year),
                entity_name=client_name,
                applicable_companies_act_framework=dto.applicable_companies_act_framework,
                applicable_auditing_framework=dto.applicable_auditing_framework,
                materiality_paise=mat_paise,
                proposed_opinion=dto.proposed_opinion,
                final_opinion=dto.final_opinion,
                opinion_rationale=dto.opinion_rationale,
                kam_applicable=dto.kam_applicable,
                caro_applicable=dto.caro_applicable,
                tax_audit_applicable=dto.tax_audit_applicable,
                going_concern_conclusion=gc_concl,
                management_rep_status=mrl_status,
                preparer_id=preparer,
            )
            created = repo.add_report_workpaper(wp)
            self._log_audit_event(session, dto.engagement_id, "AUDIT_REPORT_WORKPAPER_CREATED", f"Created report workpaper {created.id}")
            return created

    def update_report_workpaper(
        self, wp_id: str, dto: UpdateAuditReportWorkpaperDTO
    ) -> AuditReportWorkpaper:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(wp_id)
            if not wp:
                raise EntityNotFoundError("AuditReportWorkpaper", wp_id)
            if wp.is_locked:
                raise ValidationError("Cannot modify locked audit report workpaper.")

            for field in (
                "reporting_framework", "proposed_opinion", "final_opinion",
                "opinion_rationale", "kam_applicable", "caro_applicable",
                "tax_audit_applicable", "udin",
            ):
                val = getattr(dto, field)
                if val is not None:
                    setattr(wp, field, val)

            wp.updated_at = utc_now()
            updated = repo.update_report_workpaper(wp)
            self._log_audit_event(session, wp.engagement_id, "AUDIT_REPORT_WORKPAPER_UPDATED", f"Updated report workpaper {wp_id}")
            return updated

    def add_basis_of_opinion_item(
        self, wp_id: str, dto: AddBasisOfOpinionItemDTO
    ) -> AuditReportWorkpaper:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(wp_id)
            if not wp or wp.is_locked:
                raise ValidationError("Audit report workpaper not found or locked.")
            wp.basis_of_opinion_items.append(BasisOfOpinionItem(**dto.model_dump()))
            wp.updated_at = utc_now()
            return repo.update_report_workpaper(wp)

    def add_key_audit_matter(
        self, wp_id: str, dto: AddKeyAuditMatterDTO
    ) -> AuditReportWorkpaper:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(wp_id)
            if not wp or wp.is_locked:
                raise ValidationError("Audit report workpaper not found or locked.")
            wp.key_audit_matters.append(KeyAuditMatter(**dto.model_dump()))
            wp.updated_at = utc_now()
            return repo.update_report_workpaper(wp)

    def add_emphasis_or_other_matter(
        self, wp_id: str, dto: AddEmphasisOrOtherMatterDTO
    ) -> AuditReportWorkpaper:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(wp_id)
            if not wp or wp.is_locked:
                raise ValidationError("Audit report workpaper not found or locked.")
            wp.emphasis_other_matters.append(EmphasisOrOtherMatter(**dto.model_dump()))
            wp.updated_at = utc_now()
            return repo.update_report_workpaper(wp)

    def suggest_candidate_kams(self, engagement_id: str) -> list[KeyAuditMatter]:
        """Detect potential KAM candidates based on significant risks and major adjustments."""
        with self.db_manager.session_scope() as session:
            matrix_repo = AuditMatrixRepository(session)
            risks = matrix_repo.list_risks_for_engagement(engagement_id)
            risk_dicts = [
                {
                    "id": r.id,
                    "title": r.title,
                    "risk_level": getattr(r.inherent_risk, "value", str(r.inherent_risk)),
                    "area": getattr(r, "account_group", "General"),
                    "assertion": getattr(r, "assertion", "Valuation / Allocation"),
                }
                for r in risks
            ]
            ajes = AuditAdjustmentRepository(session).list_entries_for_engagement(engagement_id)
            aje_dicts = [
                {"id": a.id, "amount_paise": abs(a.total_debit_paise), "description": a.title or a.narration}
                for a in ajes
            ]
            mat = matrix_repo.get_materiality(engagement_id)
            mat_paise = mat.overall_materiality_paise if mat else 0
            return OpinionConsistencyEngine.detect_candidate_kams(
                significant_risks=risk_dicts,
                major_audit_adjustments=aje_dicts,
                materiality_paise=mat_paise,
            )

    def evaluate_opinion_decision_support(
        self, engagement_id: str
    ) -> OpinionEvaluationResult:
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper_for_engagement(engagement_id)
            proposed = wp.proposed_opinion if wp else AuditOpinionTypeEnum.UNMODIFIED
            mat_paise = wp.materiality_paise if wp else 0

            misstatements = CoreAuditEngineRepository(session).list_misstatements_for_engagement(engagement_id)
            uncorrected = sum(
                abs(m.amount_paise) for m in misstatements if getattr(m.status, "value", str(m.status)) != "Corrected"
            )
            gc = AuditCompletionRepository(session).get_going_concern_assessment(engagement_id)
            has_gc_unc = False
            if gc:
                gc_raw = getattr(gc, "audit_conclusion", getattr(gc, "conclusion", ""))
                concl_str = getattr(gc_raw, "value", str(gc_raw)).lower()
                has_gc_unc = "material uncertainty" in concl_str

            return OpinionConsistencyEngine.evaluate_opinion_consistency(
                proposed_opinion=proposed,
                materiality_paise=mat_paise,
                uncorrected_misstatements_paise=uncorrected,
                has_scope_limitation=False,
                is_scope_limitation_pervasive=False,
                has_going_concern_uncertainty=has_gc_unc,
                is_going_concern_disclosed=True,
            )

    def get_report_workpaper(self, report_workpaper_id: str) -> AuditReportWorkpaper | None:
        with self.db_manager.session_scope() as session:
            return AuditReportRepository(session).get_report_workpaper(report_workpaper_id)

    def check_consistency(self, engagement_id: str) -> dict[str, Any]:
        with self.db_manager.session_scope() as session:
            pkg = FinancialStatementRepository(session).get_latest_package(engagement_id)
            fin_repo = FinancialDataRepository(session)
            datasets = [d for d in fin_repo.list_datasets_by_engagement(engagement_id) if "trial" in str(getattr(d.dataset_type, "value", d.dataset_type)).lower()]
            tb_lines = [l for d in datasets for l in fin_repo.get_trial_balance_lines(d.id)]
            tb_rev = sum(l.closing_cr_paise - l.closing_dr_paise for l in tb_lines if l.account_code.startswith("4"))
            pnl = getattr(pkg, "profit_and_loss", getattr(pkg, "profit_loss", None)) if pkg else None
            fs_rev = getattr(pnl, "total_revenue_paise", 0) if pnl else 0
            pnl_profit = getattr(pnl, "profit_after_tax_paise", 0) if pnl else 0
            bs_eq = sum(l.current_period_paise for l in getattr(getattr(pkg, "balance_sheet", None), "equity_and_liabilities_lines", []) if getattr(l, "line_code", "").startswith("EQ"))
            mrls = AuditCompletionRepository(session).list_mrls(engagement_id)
            mrl_signed = bool(mrls and "Signed" in getattr(mrls[0].status, "value", str(mrls[0].status)))
            issues = OpinionConsistencyEngine.check_cross_document_consistency(
                fs_revenue_paise=fs_rev, tb_revenue_paise=tb_rev, fs_profit_paise=pnl_profit,
                pnl_profit_paise=pnl_profit, fs_net_worth_paise=bs_eq, bs_net_worth_paise=bs_eq,
                caro_report_answers={}, caro_workpaper_answers={}, going_concern_memo_uncertainty=False,
                fs_has_going_concern_note=True, mrl_signed=mrl_signed,
            )
            return {"is_consistent": len(issues) == 0, "inconsistencies": [i.description for i in issues]}

    def partner_approve_report(self, dto: PartnerApproveReportDTO) -> AuditReportWorkpaper:
        session_user = SecurityContext.get_current_session()
        if not session_user:
            raise PermissionDeniedError("Authentication required for partner approval.")
        role_str = getattr(session_user.role, "value", str(session_user.role))
        if role_str not in ("Partner", RoleEnum.PARTNER.value, "Administrator", RoleEnum.ADMINISTRATOR.value):
            raise PermissionDeniedError(f"Partner role required for audit report approval. Current role: {role_str}")

        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(dto.report_workpaper_id)
            if not wp or wp.engagement_id != dto.engagement_id:
                raise EntityNotFoundError("AuditReportWorkpaper", dto.report_workpaper_id)
            if wp.is_locked:
                raise ValidationError("Audit report is already finalized and locked.")

            dep_hash = self._compute_engagement_dependency_hash(session, dto.engagement_id)
            wp.dependency_hash = dep_hash
            wp.approved_by_partner_id = session_user.username
            wp.approved_at = utc_now()
            if dto.udin:
                wp.udin = dto.udin
            if wp.status == ReportWorkpaperStatusEnum.INVALIDATED_STALE:
                wp.version += 1
            wp.transition_to(ReportWorkpaperStatusEnum.PARTNER_APPROVED)

            snap_json = json.dumps(wp.model_dump(), default=str)
            repo.add_version_snapshot(
                wp_id=wp.id,
                version=wp.version,
                status=wp.status.value,
                snapshot_json=snap_json,
                dep_hash=dep_hash,
                user=session_user.username,
            )

            updated = repo.update_report_workpaper(wp)
            self._log_audit_event(
                session,
                dto.engagement_id,
                "AUDIT_REPORT_PARTNER_APPROVED",
                f"Partner {session_user.username} approved audit report v{wp.version} (Opinion: {wp.final_opinion.value})",
            )
            return updated

    def check_and_invalidate_stale_report(self, engagement_id: str) -> bool:
        """Check if approved report dependencies changed; if so, invalidate partner approval."""
        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper_for_engagement(engagement_id)
            if not wp or wp.status not in (
                ReportWorkpaperStatusEnum.PARTNER_APPROVED,
                ReportWorkpaperStatusEnum.FINAL,
                ReportWorkpaperStatusEnum.LOCKED,
            ):
                return False

            current_dep_hash = self._compute_engagement_dependency_hash(session, engagement_id)
            if current_dep_hash != wp.dependency_hash:
                wp.transition_to(ReportWorkpaperStatusEnum.INVALIDATED_STALE)
                wp.opinion_rationale += " [CRITICAL WARNING: Underlying financial dependencies modified after partner approval. Re-review required.]"
                repo.update_report_workpaper(wp)
                self._log_audit_event(
                    session,
                    engagement_id,
                    "AUDIT_REPORT_INVALIDATED_STALE",
                    f"Report {wp.id} invalidated: underlying trial balance or financial statements changed.",
                )
                return True
            return False

    def lock_final_report(self, report_workpaper_id: str) -> AuditReportWorkpaper:
        session_user = SecurityContext.get_current_session()
        if not session_user:
            raise PermissionDeniedError("Authentication required.")

        with self.db_manager.session_scope() as session:
            repo = AuditReportRepository(session)
            wp = repo.get_report_workpaper(report_workpaper_id)
            if not wp:
                raise EntityNotFoundError("AuditReportWorkpaper", report_workpaper_id)

            wp.transition_to(ReportWorkpaperStatusEnum.LOCKED)
            updated = repo.update_report_workpaper(wp)
            self._log_audit_event(session, wp.engagement_id, "AUDIT_REPORT_LOCKED", f"Report {wp.id} locked.")
            return updated

    def _compute_engagement_dependency_hash(self, session: Any, engagement_id: str) -> str:
        pkg = FinancialStatementRepository(session).get_latest_package(engagement_id)
        fs_hash = getattr(pkg, "content_hash", "NO_FS") if pkg else "NO_FS"
        fin_repo = FinancialDataRepository(session)
        datasets = fin_repo.list_datasets_by_engagement(engagement_id)
        tb_lines = []
        for ds in datasets:
            ds_type = getattr(ds.dataset_type, "value", str(ds.dataset_type)).lower()
            if "trial" in ds_type and "balance" in ds_type:
                tb_lines.extend(fin_repo.get_trial_balance_lines(ds.id))
        caro_wps = ComplianceRepository(session).list_caro_workpapers_for_engagement(engagement_id)
        caro_digest = ";".join(f"{c.clause_code}:{c.report_answer.value}" for c in sorted(caro_wps, key=lambda x: x.clause_code))
        gc = AuditCompletionRepository(session).get_going_concern_assessment(engagement_id)
        gc_raw = getattr(gc, "audit_conclusion", getattr(gc, "conclusion", "None")) if gc else "None"
        gc_concl = getattr(gc_raw, "value", str(gc_raw))
        return OpinionConsistencyEngine.calculate_dependency_hash(
            fs_package_hash=fs_hash,
            tb_line_count=len(tb_lines),
            total_debit_paise=sum(l.closing_dr_paise for l in tb_lines),
            total_credit_paise=sum(l.closing_cr_paise for l in tb_lines),
            caro_conclusions_digest=caro_digest,
            going_concern_conclusion=gc_concl,
        )

    def _log_audit_event(self, session: Any, engagement_id: str, action: str, details: str) -> None:
        user = SecurityContext.get_current_session()
        actor = user.username if user else "system"
        AuditEventRepository(session).add(
            AuditEvent(
                id=str(uuid4()),
                engagement_id=engagement_id,
                user_id=actor,
                action=action,
                details=details,
            )
        )
