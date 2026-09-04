"""Comprehensive Realistic Audit Workflow, 9-Area Chain, Performance, and Regression Tests for Phase B."""

import time

import pytest

from finauditpro.application.account_mapping_dtos import MapAccountDTO, SyncTrialBalanceAccountsDTO
from finauditpro.application.audit_adjustment_dtos import (
    ApplyAJEDTO,
    CreateAJEDTO,
    CreateAJELineDTO,
    ReviewAJEDTO,
    SubmitAJEDTO,
)
from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.core_audit_dtos import (
    CalculateAuditCompletenessDTO,
    CreateMisstatementDTO,
    EvaluateProcedureConclusionDTO,
    ExecuteSampleItemTestDTO,
    LinkMisstatementToAJEDTO,
    LogAuditExceptionDTO,
)
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_execution_entities import (
    AuditTestOutcomeEnum,
    MisstatementTypeEnum,
    ProcedureConclusionEnum,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    MaterialityAssessment,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    RoleEnum,
    User,
)
from finauditpro.domain.financial_entities import (
    DatasetTypeEnum,
    FinancialDataset,
    TrialBalanceLine,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.repositories import (
    AuditMatrixRepository,
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture(autouse=True)
def clean_security_context():
    SecurityContext.clear()
    yield
    SecurityContext.clear()


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_phase_b_full.db"
    return initialize_database(db_path)


@pytest.fixture
def seed_environment(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(id="firm-1", name="CA Audit Firm"))
        user_repo = UserRepository(session)
        user_repo.add(
            User(id="user-assoc", username="assoc1", password_hash="h", salt="s", role="Associate")
        )
        user_repo.add(
            User(id="user-mgr", username="mgr1", password_hash="h", salt="s", role="Manager")
        )
        client = ClientRepository(session).add(
            Client(id="client-1", firm_id=firm.id, name="ABC Manufacturing Pvt Ltd")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                id="eng-1",
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )
        # Materiality: Overall ₹10L, Performance ₹7.5L, Trivial ₹50K
        mat = MaterialityAssessment(
            engagement_id=eng.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount_paise=1000000000,
            overall_materiality_paise=100000000,
            performance_materiality_paise=75000000,
            clearly_trivial_threshold_paise=5000000,
        )
        AuditMatrixRepository(session).add_materiality(mat)
        return eng


def test_abc_manufacturing_9_area_realistic_workflow(db_manager, seed_environment):
    """End-to-end audit execution for ABC Manufacturing Pvt Ltd across 9 financial areas."""
    eng = seed_environment
    map_svc = AccountMappingService(db_manager)
    adj_svc = AuditAdjustmentService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)

    SecurityContext.set_current_session(
        UserSession(user_id="user-assoc", username="assoc1", role=RoleEnum.ASSOCIATE)
    )

    # Step 1: Trial Balance Ingestion (9 Balanced Areas)
    ds = FinancialDataset(
        id="ds-abc",
        engagement_id=eng.id,
        dataset_name="ABC_TB_2026.xlsx",
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
    )
    tb_lines = [
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=1,
            account_code="1010",
            account_name="Plant & Machinery",
            closing_dr_paise=500000000,
        ),  # 1. PPE
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=2,
            account_code="1020",
            account_name="Finished Goods Stock",
            closing_dr_paise=300000000,
        ),  # 2. Inventory
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=3,
            account_code="1030",
            account_name="Trade Debtors",
            closing_dr_paise=200000000,
        ),  # 3. Receivables
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=4,
            account_code="1040",
            account_name="State Bank of India",
            closing_dr_paise=100000000,
        ),  # 4. Cash & Bank
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=5,
            account_code="2010",
            account_name="Term Loan SBI",
            closing_cr_paise=400000000,
        ),  # 5. Loans
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=6,
            account_code="2020",
            account_name="Trade Creditors",
            closing_cr_paise=300000000,
        ),  # 6. Payables
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=7,
            account_code="2030",
            account_name="GST & TDS Payable",
            closing_cr_paise=100000000,
        ),  # 7. Tax
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=8,
            account_code="3010",
            account_name="Revenue from Sales",
            closing_cr_paise=500000000,
        ),  # 8. Revenue
        TrialBalanceLine(
            dataset_id="ds-abc",
            source_row_no=9,
            account_code="4010",
            account_name="Salaries & Wages",
            closing_dr_paise=200000000,
        ),  # 9. Payroll
    ]
    with db_manager.session_scope() as session:
        fin_repo = FinancialDataRepository(session)
        fin_repo.add_dataset(ds)
        fin_repo.add_trial_balance_lines(tb_lines)

    # Step 2: Schedule III Mapping
    map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id="ds-abc")
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1010",
            schedule_iii_category="Property, Plant and Equipment",
            schedule_iii_line_item="Plant",
            lead_schedule_ref="WP-D1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1020",
            schedule_iii_category="Inventories",
            schedule_iii_line_item="Finished Goods",
            lead_schedule_ref="WP-F1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1030",
            schedule_iii_category="Trade Receivables",
            schedule_iii_line_item="Debtors",
            lead_schedule_ref="WP-G1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1040",
            schedule_iii_category="Cash and Cash Equivalents",
            schedule_iii_line_item="Bank",
            lead_schedule_ref="WP-H1",
            account_type=AccountTypeEnum.ASSET,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="2010",
            schedule_iii_category="Long-Term Borrowings",
            schedule_iii_line_item="Term Loan",
            lead_schedule_ref="WP-B1",
            account_type=AccountTypeEnum.LIABILITY,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="2020",
            schedule_iii_category="Trade Payables",
            schedule_iii_line_item="Creditors",
            lead_schedule_ref="WP-C2",
            account_type=AccountTypeEnum.LIABILITY,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="2030",
            schedule_iii_category="Other Current Liabilities",
            schedule_iii_line_item="Statutory Dues",
            lead_schedule_ref="WP-C3",
            account_type=AccountTypeEnum.LIABILITY,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="3010",
            schedule_iii_category="Revenue from Operations",
            schedule_iii_line_item="Sales",
            lead_schedule_ref="WP-P1",
            account_type=AccountTypeEnum.INCOME,
        )
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="4010",
            schedule_iii_category="Employee Benefits Expense",
            schedule_iii_line_item="Salaries",
            lead_schedule_ref="WP-P4",
            account_type=AccountTypeEnum.EXPENSE,
        )
    )

    # Step 3: Identify Risks & Plan Procedures
    risk_rev = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-REV-01",
            title="Fictitious Sales Cutoff",
            category="Revenue from Operations",
            description="Premature revenue booking",
            assertions=[AssertionEnum.CUT_OFF],
            severity=RiskSeverityEnum.HIGH,
        )
    )
    risk_inv = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-INV-01",
            title="Slow Moving Stock NRV",
            category="Inventories",
            description="Valuation below cost",
            assertions=[AssertionEnum.VALUATION],
            severity=RiskSeverityEnum.MEDIUM,
        )
    )

    proc_rev = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            linked_risk_ids=[risk_rev.id],
            procedure_code="PRC-REV-01",
            objective="Testing sales cutoff 5 days pre and post March 31",
            assertions=[AssertionEnum.CUT_OFF],
            procedure_type="Substantive Test",
        )
    )
    proc_inv = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            linked_risk_ids=[risk_inv.id],
            procedure_code="PRC-INV-01",
            objective="Test NRV vs Cost for top 10 inventory batches",
            assertions=[AssertionEnum.VALUATION],
            procedure_type="Substantive Test",
        )
    )

    # Step 4: Sample Item Testing & Exception Logging
    test_1 = core_svc.execute_sample_item_test(
        ExecuteSampleItemTestDTO(
            procedure_id=proc_rev.id,
            item_identifier="INV-2026-889",
            expected_value_paise=10000000,
            actual_value_paise=10000000,
            explanation="Valid invoice",
        )
    )
    assert test_1.test_result == AuditTestOutcomeEnum.PASS

    test_2 = core_svc.execute_sample_item_test(
        ExecuteSampleItemTestDTO(
            procedure_id=proc_rev.id,
            item_identifier="INV-2026-905",
            expected_value_paise=25000000,
            actual_value_paise=20000000,
            explanation="Post year-end invoice recorded in March",
        )
    )
    assert test_2.test_result == AuditTestOutcomeEnum.EXCEPTION

    exc = core_svc.log_audit_exception(
        LogAuditExceptionDTO(
            engagement_id=eng.id,
            procedure_id=proc_rev.id,
            sample_item_id=test_2.id,
            exception_code="EXC-REV-01",
            title="Cutoff Overstatement ₹50,000",
            description="Invoice dated April 2 booked in FY 25-26",
            amount_paise=5000000,
        )
    )

    # Step 5: Escalate to Misstatement & Post Balanced AJE
    misst = core_svc.create_misstatement(
        CreateMisstatementDTO(
            engagement_id=eng.id,
            exception_id=exc.id,
            procedure_id=proc_rev.id,
            account_code="3010",
            account_name="Revenue from Sales",
            schedule_iii_category="Revenue from Operations",
            misstatement_type=MisstatementTypeEnum.FACTUAL,
            amount_paise=5000000,
            rationale="Sales cutoff adjustment",
        )
    )

    # Create & Approve AJE: Dr Sales ₹50,000, Cr Debtors ₹50,000
    aje = adj_svc.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng.id,
            aje_number="AJE-REV-001",
            entry_date="2026-03-31",
            title="Sales Cutoff Correction",
            narration="Reverse April sales from March accounts",
            reason="Cutoff misstatement",
            lines=[
                CreateAJELineDTO(
                    account_code="3010",
                    account_name="Revenue from Sales",
                    debit_paise=5000000,
                    credit_paise=0,
                ),
                CreateAJELineDTO(
                    account_code="1030",
                    account_name="Trade Debtors",
                    debit_paise=0,
                    credit_paise=5000000,
                ),
            ],
        )
    )
    adj_svc.submit_adjustment(SubmitAJEDTO(engagement_id=eng.id, entry_id=aje.id))
    SecurityContext.set_current_session(
        UserSession(user_id="user-mgr", username="mgr1", role=RoleEnum.MANAGER)
    )
    adj_svc.review_adjustment(
        ReviewAJEDTO(engagement_id=eng.id, entry_id=aje.id, decision="APPROVE")
    )
    adj_svc.apply_adjustment(ApplyAJEDTO(engagement_id=eng.id, entry_id=aje.id))

    # Link misstatement to AJE
    core_svc.link_misstatement_to_aje(
        LinkMisstatementToAJEDTO(
            engagement_id=eng.id, misstatement_id=misst.id, aje_id=aje.id, aje_number=aje.aje_number
        )
    )

    # Step 6: Attach Evidence & Document Conclusion with Override
    matrix_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=eng.id,
            procedure_id=proc_rev.id,
            title="Dispatch_Lorry_Receipt_905.pdf",
            excerpt_or_reference="Lorry receipt date April 2 2026 confirms goods exited factory post year-end",
        )
    )
    core_svc.evaluate_procedure_conclusion(
        EvaluateProcedureConclusionDTO(
            engagement_id=eng.id,
            procedure_id=proc_rev.id,
            conclusion=ProcedureConclusionEnum.PASS,
            result_summary="Sample testing completed. Exception rectified via AJE-REV-001.",
            override_reason="Management posted AJE-REV-001 adjusting the ₹50,000 variance.",
        )
    )

    # Step 7: Complete Procedure 2 (Inventory)
    matrix_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=eng.id,
            procedure_id=proc_inv.id,
            title="NRV_Test_Working.xlsx",
            excerpt_or_reference="NRV exceeds cost for all sampled items",
        )
    )
    core_svc.evaluate_procedure_conclusion(
        EvaluateProcedureConclusionDTO(
            engagement_id=eng.id,
            procedure_id=proc_inv.id,
            conclusion=ProcedureConclusionEnum.PASS,
            result_summary="Inventory valuation substantiated at lower of cost or NRV.",
        )
    )

    # Step 8: Verify Accounting Invariants
    adj_tb = adj_svc.calculate_adjusted_trial_balance(eng.id, "ds-abc")
    assert adj_tb.is_fully_balanced is True
    lead_scheds = adj_svc.calculate_lead_schedules(eng.id, "ds-abc")
    assert len(lead_scheds) >= 8

    # Step 9: Verify Completeness Score
    comp_rep = core_svc.calculate_audit_completeness(
        CalculateAuditCompletenessDTO(engagement_id=eng.id)
    )
    assert comp_rep.risk_coverage_pct == 100.0
    assert comp_rep.procedure_execution_pct == 100.0
    assert comp_rep.composite_completeness_score >= 95.0
    assert comp_rep.is_ready_for_finalization is True


def test_scalability_performance_5000_items(db_manager, seed_environment):
    """Performance test validating 5,000 sample test lines and completeness scoring in < 2.5s."""
    eng = seed_environment
    matrix_svc = AuditMatrixService(db_manager)
    core_svc = CoreAuditService(db_manager)
    SecurityContext.set_current_session(
        UserSession(user_id="user-mgr", username="mgr1", role=RoleEnum.MANAGER)
    )

    # 1. Create Risk and Procedure
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-PERF",
            title="Scale Test Risk",
            category="Scale",
            description="Perf test",
        )
    )
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            linked_risk_ids=[risk.id],
            procedure_code="PRC-PERF",
            objective="Large sample test",
            assertions=[AssertionEnum.ACCURACY],
        )
    )

    # 2. Bulk insert 5,000 sample test items
    t0 = time.perf_counter()
    from finauditpro.domain.audit_execution_entities import AuditSampleItemTest
    from finauditpro.infrastructure.persistence.repositories.core_audit_engine_repository import (
        CoreAuditEngineRepository,
    )

    items = [
        AuditSampleItemTest(
            procedure_id=proc.id,
            item_identifier=f"TXN-{i}",
            expected_value_paise=100000,
            actual_value_paise=100000,
            test_result=AuditTestOutcomeEnum.PASS,
        )
        for i in range(1, 5001)
    ]
    with db_manager.session_scope() as session:
        CoreAuditEngineRepository(session).add_sample_items_bulk(items)
    t_insert = time.perf_counter() - t0

    # 3. Completeness Calculation
    t0 = time.perf_counter()
    comp_rep = core_svc.calculate_audit_completeness(
        CalculateAuditCompletenessDTO(engagement_id=eng.id)
    )
    t_comp = time.perf_counter() - t0

    # Assert performance threshold (< 2.5 seconds total)
    assert (t_insert + t_comp) < 2.5
    assert comp_rep.risk_coverage_pct == 100.0
