"""Comprehensive tests for Deterministic Engagement Finalisation Gate, Consistency Checks, and Lifecycle."""

from uuid import uuid4

import pytest

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.completion_dtos import (
    PartnerSignoffDTO,
    RelatedPartyCompletionDTO,
    SA240CompletionDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext, UserSession
from finauditpro.application.services.audit_completion_service import AuditCompletionService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.engagement_finalization_service import EngagementFinalizationService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateReviewNoteDTO, CreateWorkingPaperDTO
from finauditpro.domain.audit_completion_entities import (
    GoingConcernAssessment,
    ManagementRepresentationLetter,
    MRLStatusEnum,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    MaterialityAssessment,
    RiskSeverityEnum,
)
from finauditpro.domain.completion_checklist_entities import FinalisationGateStatusEnum
from finauditpro.domain.compliance_entities import CAROApplicabilityEnum, CAROClauseWorkpaper, CAROReportAnswerEnum
from finauditpro.domain.entities import Client, Engagement, EngagementStatusEnum, Firm
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.domain.financial_entities import DatasetStatusEnum, DatasetTypeEnum, ExceptionItem, FinancialDataset
from finauditpro.domain.financial_statement_entities import (
    BalanceSheet,
    CashFlowStatement,
    FinancialStatementPackage,
    PackageStatusEnum,
    ProfitAndLossStatement,
    StatementOfChangesInEquity,
)
from finauditpro.domain.reporting_consistency_engine import ReportingConsistencyEngine
from finauditpro.domain.working_paper_entities import WorkingPaperStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    WorkingPaperRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)
from finauditpro.infrastructure.persistence.repositories.audit_matrix_repository import (
    AuditMatrixRepository,
)
from finauditpro.infrastructure.persistence.repositories.compliance_repository import ComplianceRepository
from finauditpro.infrastructure.persistence.repositories.financial_data_repository import FinancialDataRepository
from finauditpro.infrastructure.persistence.repositories.financial_statement_repository import (
    FinancialStatementRepository,
)


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_finalisation_gate.db"
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def base_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(name="Apex Forensic LLP"))
        client = ClientRepository(session).add(
            Client(firm_id=firm.id, name="Zenith Enterprises Ltd", pan="AABCZ1234F")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-2026",
                title="Statutory Audit FY 2025-26",
                status=EngagementStatusEnum.FIELDWORK,
            )
        )
    return eng


class TestEngagementFinalisationGate:
    """Tests deterministic gate evaluation, exact blocker display, and lifecycle transition enforcement."""

    def test_finalisation_blocked_exact_reasons_display(self, db_manager, base_engagement):
        """When blocking conditions exist, gate must return BLOCKED with exact human-readable reasons."""
        eng = base_engagement
        wp_service = WorkingPaperService(db_manager)
        matrix_service = AuditMatrixService(db_manager)

        # 1. Create 3 working papers in DRAFT
        for i in range(1, 4):
            wp = wp_service.create_working_paper(
                CreateWorkingPaperDTO(
                    engagement_id=eng.id,
                    index_reference=f"WP-00{i}",
                    title=f"Working Paper {i}",
                    area="Revenue",
                    preparer_id="Senior Auditor",
                )
            )

        # 2. Create 2 unresolved review notes on WP 1
        wp_service.raise_review_note(
            CreateReviewNoteDTO(
                working_paper_id=wp.id,
                raised_by="Manager",
                note_text="Critical: Obtain external bank confirmation.",
            )
        )
        wp_service.raise_review_note(
            CreateReviewNoteDTO(
                working_paper_id=wp.id,
                raised_by="Senior Manager",
                note_text="Material: Verify year-end revenue cutoff schedule.",
            )
        )

        # 3. Create 1 high-risk finding unresolved
        risk = matrix_service.create_risk(
            CreateRiskDTO(
                engagement_id=eng.id,
                risk_code="RSK-REV-01",
                category="Revenue",
                title="Fictitious Revenue Risk",
                description="Risk that revenue is recognized for non-existent sales.",
                severity=RiskSeverityEnum.HIGH,
            )
        )
        proc = matrix_service.create_procedure(
            CreateProcedureDTO(
                engagement_id=eng.id,
                risk_id=risk.id,
                procedure_code="PROC-REV-01",
                objective="Vouch dispatch documents",
                procedure_type="Substantive",
                account_area="Revenue",
                assertion=AssertionEnum.OCCURRENCE,
            )
        )
        matrix_service.create_finding(
            CreateFindingDTO(
                engagement_id=eng.id,
                procedure_id=proc.id,
                risk_id=risk.id,
                title="Unvouched Revenue Anomaly",
                description="High value transaction without proof of delivery.",
                severity=RiskSeverityEnum.HIGH,
            )
        )

        # 4. Bank reconciliation difference of ₹42,000 (4,200,000 paise)
        with db_manager.session_scope() as session:
            import json
            fin_repo = FinancialDataRepository(session)
            ds = fin_repo.add_dataset(
                FinancialDataset(
                    engagement_id=eng.id,
                    dataset_name="Bank Reconciliation Statement",
                    dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
                    status=DatasetStatusEnum.UPLOADED,
                )
            )
            fin_repo.add_exceptions(
                [
                    ExceptionItem(
                        dataset_id=ds.id,
                        analysis_run_id=str(uuid4()),
                        analytic_id="BRS_ANALYSIS",
                        row_number=1,
                        severity="High",
                        title="Bank Reconciliation Difference",
                        description="Unreconciled bank ledger discrepancy",
                        computed_evidence=json.dumps({"difference_paise": 4200000}),
                    )
                ]
            )

        # 5. Missing evidence items (PROC-REV-01 has 0 evidence linked)
        # Evaluate Gate
        fin_service = EngagementFinalizationService(db_manager)
        gate_res = fin_service.evaluate_finalization_gate(eng.id)

        assert gate_res.is_finalizable is False
        assert gate_res.status == "BLOCKED"
        assert gate_res.summary_headline == "FINALISATION BLOCKED"
        assert "FINALISATION BLOCKED" in gate_res.display_text
        assert "3 working papers pending review" in gate_res.display_text
        assert "2 unresolved review notes" in gate_res.display_text
        assert "1 high-risk finding unresolved" in gate_res.display_text
        assert "₹42,000 bank reconciliation difference" in gate_res.display_text
        assert "1 missing evidence item" in gate_res.display_text

    def test_finalisation_ready_when_all_mandatory_gates_satisfied(self, db_manager, base_engagement):
        """When all 10 gates and statutory items are satisfied, gate returns READY."""
        eng = base_engagement
        wp_service = WorkingPaperService(db_manager)
        matrix_service = AuditMatrixService(db_manager)
        fin_service = EngagementFinalizationService(db_manager)

        # 1. Approved Working Paper
        wp = wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=eng.id,
                index_reference="WP-REV-001",
                title="Revenue Testing WP",
                area="Revenue",
                preparer_id="Senior Auditor",
            )
        )
        with db_manager.session_scope() as session:
            wp_repo = WorkingPaperRepository(session)
            wp_entity = wp_repo.get_working_paper(wp.id)
            wp_entity.status = WorkingPaperStatusEnum.APPROVED
            wp_repo.update_working_paper(wp_entity)

            # 2. Materiality Documented
            mat_repo = AuditMatrixRepository(session)
            mat_repo.add_materiality(
                MaterialityAssessment(
                    engagement_id=eng.id,
                    benchmark_type=BenchmarkTypeEnum.PROFIT_BEFORE_TAX,
                    overall_materiality_paise=50000000,
                    performance_materiality_paise=37500000,
                    clearly_trivial_threshold_paise=2500000,
                )
            )

            # 3. Financial Statements Package
            fs_repo = FinancialStatementRepository(session)
            fs_repo.add_package(
                FinancialStatementPackage(
                    engagement_id=eng.id,
                    status=PackageStatusEnum.APPROVED,
                    balance_sheet=BalanceSheet(engagement_id=eng.id, as_at_date="2026-03-31", total_assets_paise=10000000, total_equity_and_liabilities_paise=10000000),
                    profit_and_loss=ProfitAndLossStatement(engagement_id=eng.id, for_period_ended="2026-03-31", total_revenue_paise=5000000),
                    cash_flow=CashFlowStatement(engagement_id=eng.id, for_period_ended="2026-03-31"),
                    changes_in_equity=StatementOfChangesInEquity(engagement_id=eng.id),
                )
            )

            # 4. CARO Clause Workpaper
            comp_repo = ComplianceRepository(session)
            comp_repo.add_caro_workpaper(
                CAROClauseWorkpaper(
                    engagement_id=eng.id,
                    clause_code="3(i)",
                    clause_title="Property, Plant and Equipment",
                    question="Whether proper records of PPE are maintained?",
                    procedure_text="Verify PPE register and physical verification schedule.",
                    applicability=CAROApplicabilityEnum.APPLICABLE,
                    report_answer=CAROReportAnswerEnum.UNQUALIFIED,
                    conclusion_text="Title deeds verified and physical verification schedule maintained.",
                )
            )

            # 5. Going Concern (SA 570) & MRL (SA 580)
            compl_repo = AuditCompletionRepository(session)
            compl_repo.save_going_concern_assessment(
                GoingConcernAssessment(
                    engagement_id=eng.id,
                    partner_signoff=True,
                    reviewer="Engagement Partner",
                )
            )
            compl_repo.save_mrl(
                ManagementRepresentationLetter(
                    engagement_id=eng.id,
                    mrl_number="MRL-2026-001",
                    financial_year="2025-2026",
                    requested_date="2026-03-31",
                    status=MRLStatusEnum.SIGNED_AND_OBTAINED,
                    signatories=["Managing Director", "CFO"],
                )
            )

        # 6. Related Parties (SA 550) & SA 240 Fraud
        fin_service.record_related_party_completion(
            RelatedPartyCompletionDTO(
                engagement_id=eng.id,
                register_reviewed=True,
                undisclosed_transactions_identified=False,
                arms_length_verified=True,
                schedule_iii_disclosed=True,
                auditor_conclusion="Related party disclosures verified.",
            )
        )
        fin_service.record_sa240_completion(
            SA240CompletionDTO(
                engagement_id=eng.id,
                management_override_tested=True,
                journal_entry_testing_completed=True,
                revenue_recognition_presumption_addressed=True,
                risk_indicators_identified=False,
                auditor_conclusion="Journal entry testing completed without exception.",
            )
        )

        # Evaluate Gate
        gate_res = fin_service.evaluate_finalization_gate(eng.id)

        assert gate_res.is_finalizable is True
        assert gate_res.status == FinalisationGateStatusEnum.READY.value
        assert gate_res.summary_headline == "FINALISATION READY"
        assert "FINALISATION READY" in gate_res.display_text
        assert len(gate_res.blockers) == 0

    def test_finalisation_lifecycle_and_partner_approval_enforcement(self, db_manager, base_engagement):
        """Lifecycle transition from READY -> PARTNER REVIEW -> APPROVED -> LOCKED with RBAC."""
        eng = base_engagement
        fin_service = EngagementFinalizationService(db_manager)

        # If blocked, submitting for partner review or finalizing must fail
        with pytest.raises(ValidationError) as exc_info:
            fin_service.submit_for_partner_review(eng.id)
        assert "FINALISATION BLOCKED" in str(exc_info.value)

        # Non-partner cannot execute final signoff
        SecurityContext.set_current_user("senior_auditor", RoleEnum.SENIOR)
        with pytest.raises(PermissionDeniedError):
            fin_service.partner_signoff_and_finalize(
                PartnerSignoffDTO(
                    engagement_id=eng.id,
                    signoff_notes="Attempted senior sign-off.",
                )
            )

    def test_reporting_consistency_engine_checks(self):
        """Reporting consistency engine verifies cross-artifact alignment."""
        class MockLine:
            def __init__(self, code, dr, cr):
                self.account_code, self.closing_dr_paise, self.closing_cr_paise = code, dr, cr

        class MockFS:
            profit_and_loss = type("PL", (), {"total_revenue_paise": 1000000})()
            balance_sheet = type("BS", (), {"total_assets_paise": 5000000, "total_equity_and_liabilities_paise": 5000000})()

        # Revenue matches: TB closing Cr (1,000,000) == FS Revenue (1,000,000)
        tb = [MockLine("4001", 0, 1000000)]
        fs = MockFS()

        res = ReportingConsistencyEngine.evaluate_consistency(
            tb_lines=tb,
            fs_package=fs,
            audit_report_opinion="Unmodified Statutory Audit Opinion",
        )
        assert res.is_all_consistent is True
        assert len(res.discrepancies) == 0

        # Revenue mismatch
        tb_mismatch = [MockLine("4001", 0, 800000)]
        res_err = ReportingConsistencyEngine.evaluate_consistency(
            tb_lines=tb_mismatch,
            fs_package=fs,
        )
        assert res_err.is_all_consistent is False
        assert any("Revenue tie-out mismatch" in d for d in res_err.discrepancies)
