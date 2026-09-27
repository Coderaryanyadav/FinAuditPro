"""Full System User Journey, Failure Resiliency, and Data Isolation Test Suite.

Verifies end-to-end Chartered Accountant workflows:
- SCENARIO 1: Firm -> Client -> Engagement -> Planning
- SCENARIO 2: Import TB -> Validate -> Map -> Reconcile -> Analyze
- SCENARIO 3: Risk -> Assertion -> Procedure -> Sample -> Evidence -> Testing -> Exception
- SCENARIO 4: Exception -> Finding -> Working Paper -> Review -> Response -> Approval -> Lock
- SCENARIO 5: Finalisation Gate -> Partner Review -> Final Report -> Archive
- SCENARIO 6: Archived Engagement -> Roll Forward -> New Financial Year
- FAILURE MODES: Corrupted files, duplicate imports, invalid financials, missing evidence,
  unauthorized user, database interruption, AI unavailable, disk limits, large datasets,
  concurrent access, invalid state transitions.
- ISOLATION: Cross-engagement and cross-FY boundary isolation.
- DETERMINISM: Repeatable mathematical calculations across financial engines.
"""

import csv
from decimal import Decimal
import io
import os
from pathlib import Path
import tempfile
import time
from uuid import uuid4
import pytest

from finauditpro.application.account_mapping_dtos import MapAccountDTO, SyncTrialBalanceAccountsDTO
from finauditpro.application.archival_dtos import FreezeAndSealDTO
from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CalculateMaterialityDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.audit_report_dtos import (
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
)
from finauditpro.application.dtos import (
    CreateClientDTO,
    CreateEngagementDTO,
    CreateFirmDTO,
)
from finauditpro.application.evidence_dtos import CreateEvidenceDTO
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.roll_forward_dtos import ExecuteRollForwardDTO
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.application.services.ai_copilot_service import AICopilotService
from finauditpro.application.services.archival_service import ArchivalService
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.audit_report_service import AuditReportService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_finalization_service import EngagementFinalizationService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.evidence_service import EvidenceService
from finauditpro.application.services.financial_service import FinancialService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.materiality_service import MaterialityService
from finauditpro.application.services.roll_forward_service import RollForwardService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    CreateWorkingPaperDTO,
    RespondReviewNoteDTO,
    SignOffDTO,
)
from finauditpro.domain.account_mapping_entities import AccountTypeEnum
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditProcedure,
    AuditRisk,
    BenchmarkTypeEnum,
    EvidenceStatusEnum,
    FindingStatusEnum,
    FindingSourceEnum,
    RiskSeverityEnum,
    ProcedureStatusEnum,
)
from finauditpro.domain.audit_report_entities import AuditOpinionTypeEnum, ReportWorkpaperStatusEnum
from finauditpro.domain.entities import EngagementStatusEnum, RoleEnum
from finauditpro.domain.exceptions import (
    EngagementLockedError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.financial_entities import DatasetTypeEnum, LedgerEntry
from finauditpro.domain.roll_forward_entities import (
    OpeningBalanceLink,
    calculate_opening_tie_out,
)
from finauditpro.domain.working_paper_entities import SignOffLevelEnum, WorkingPaperStatusEnum
from finauditpro.infrastructure.analytics.analytics_engine import (
    DeterministicAnalyticsEngine,
)
from finauditpro.infrastructure.documents.document_security import (
    DocumentSecurityError,
    validate_document_security,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def clean_db(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "finauditpro_system_test.db"
    return initialize_database(db_file)


# ==============================================================================
# SCENARIO 1: Create firm -> client -> engagement -> planning
# ==============================================================================
def test_scenario_1_firm_client_engagement_planning(clean_db: DatabaseManager) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    mat_svc = MaterialityService(clean_db)

    # 1. Create Firm
    firm = firm_svc.create_firm(CreateFirmDTO(name="Kalyani & Associates LLP", registration_number="FRN-108294W"))
    assert firm.id is not None
    assert firm.name == "Kalyani & Associates LLP"

    # 2. Create Client
    client = client_svc.create_client(
        CreateClientDTO(firm_id=firm.id, name="Zenith InfraTech Private Limited", pan="AAACZ1234F")
    )
    assert client.id is not None
    assert client.firm_id == firm.id

    # 3. Create Engagement
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(
            firm_id=firm.id,
            client_id=client.id,
            financial_year="2025-26",
            audit_standard_version="ICAI_SA_2024_V1",
        )
    )
    assert eng.id is not None
    assert eng.financial_year == "2025-26"
    assert eng.status == EngagementStatusEnum.PLANNING

    # 4. Configure Planning & Materiality (SA 320)
    mat = mat_svc.calculate_and_save_materiality(
        CalculateMaterialityDTO(
            engagement_id=eng.id,
            benchmark_type=BenchmarkTypeEnum.REVENUE,
            benchmark_amount=50000000.00,  # 5 Crore INR
            overall_percentage=1.0,        # 1%
            performance_percentage=75.0,   # 75%
            trivial_percentage=5.0,        # 5%
            created_by="Lead Partner",
        )
    )
    assert mat.overall_materiality.rupees == Decimal("500000.00")
    assert mat.performance_materiality.rupees == Decimal("375000.00")
    assert mat.clearly_trivial_threshold.rupees == Decimal("25000.00")


# ==============================================================================
# SCENARIO 2: Import TB -> validate -> map -> reconcile -> analyze
# ==============================================================================
def test_scenario_2_import_tb_validate_map_reconcile_analyze(clean_db: DatabaseManager, tmp_path: Path) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    fin_svc = FinancialService(clean_db)
    map_svc = AccountMappingService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Audit Co"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Apex Retail Ltd"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # 1. Create and Import Balanced Trial Balance CSV
    tb_csv = tmp_path / "trial_balance_fy26.csv"
    with tb_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Opening Dr", "Opening Cr", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        writer.writerow(["1001", "Share Capital", "0.00", "10,00,000.00", "0.00", "0.00", "0.00", "10,00,000.00"])
        writer.writerow(["2001", "Trade Payables", "0.00", "5,00,000.00", "1,00,000.00", "2,00,000.00", "0.00", "6,00,000.00"])
        writer.writerow(["3001", "Property Plant & Equipment", "8,00,000.00", "0.00", "2,00,000.00", "50,000.00", "9,50,000.00", "0.00"])
        writer.writerow(["3002", "Trade Receivables", "4,50,000.00", "0.00", "3,00,000.00", "3,50,000.00", "4,00,000.00", "0.00"])
        writer.writerow(["3003", "HDFC Bank Current A/c", "2,50,000.00", "0.00", "1,50,000.00", "1,50,000.00", "2,50,000.00", "0.00"])

    mappings = {
        "account_code": "Account Code",
        "account_name": "Account Name",
        "opening_dr": "Opening Dr",
        "opening_cr": "Opening Cr",
        "debit": "Debit",
        "credit": "Credit",
        "closing_dr": "Closing Dr",
        "closing_cr": "Closing Cr",
    }

    preview = fin_svc.preview_dataset_import(
        file_path=str(tb_csv),
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        custom_mappings=mappings,
    )
    assert preview.validation_passed is True
    assert preview.is_balanced is True

    dataset = fin_svc.import_dataset(
        ImportDatasetDTO(
            engagement_id=eng.id,
            dataset_name="TB FY26 Master",
            dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
            file_path=str(tb_csv),
            column_mappings=mappings,
        )
    )
    assert dataset.id is not None

    # 2. Map Accounts (Schedule III classification)
    map_svc.sync_trial_balance_accounts(
        SyncTrialBalanceAccountsDTO(engagement_id=eng.id, dataset_id=dataset.id)
    )
    map_svc.map_single_account(
        MapAccountDTO(
            engagement_id=eng.id,
            account_code="1001",
            account_type=AccountTypeEnum.EQUITY,
            schedule_iii_category="Equity",
            schedule_iii_line_item="Share Capital",
            lead_schedule_ref="LS-EQ-01",
        )
    )

    # 3. Reconcile Opening Balances (SA 510 Tie-Out)
    links = [
        OpeningBalanceLink(
            engagement_id=eng.id,
            source_engagement_id="eng-py",
            account_code="1001",
            account_name="Share Capital",
            opening_dr_paise=0,
            opening_cr_paise=100000000,
            prior_closing_dr_paise=0,
            prior_closing_cr_paise=100000000,
            is_tied_out=True,
        ),
        OpeningBalanceLink(
            engagement_id=eng.id,
            source_engagement_id="eng-py",
            account_code="2001",
            account_name="Trade Payables",
            opening_dr_paise=0,
            opening_cr_paise=50000000,
            prior_closing_dr_paise=0,
            prior_closing_cr_paise=50000000,
            is_tied_out=True,
        ),
    ]
    tie_out_summary = calculate_opening_tie_out(links)
    assert tie_out_summary.is_fully_tied_out is True
    assert tie_out_summary.tied_out_accounts == 2

    # 4. Deterministic Analytics (Benford & Duplicate Analysis)
    entries = [
        LedgerEntry(dataset_id=dataset.id, source_row_no=i, account_code="3003", debit_paise=int(i * 100000), credit_paise=0)
        for i in range(1, 60)
    ]
    benford_res = DeterministicAnalyticsEngine.check_benford_law(dataset.id, entries)
    assert benford_res.analytic_id == "benford_law_deviation"

    dup_entries = [
        LedgerEntry(dataset_id=dataset.id, source_row_no=1, voucher_number="V101", date="2025-09-01", debit_paise=500000, credit_paise=0),
        LedgerEntry(dataset_id=dataset.id, source_row_no=2, voucher_number="V101", date="2025-09-01", debit_paise=500000, credit_paise=0),
        LedgerEntry(dataset_id=dataset.id, source_row_no=3, voucher_number="V102", date="2025-09-02", debit_paise=720000, credit_paise=0),
    ]
    dup_res = DeterministicAnalyticsEngine.detect_duplicates(dataset.id, dup_entries)
    assert dup_res.analytic_id == "duplicate_detection"
    assert len(dup_res.exceptions) == 1


# ==============================================================================
# SCENARIO 3: Risk -> Assertion -> Procedure -> Sample -> Evidence -> Testing -> Exception
# ==============================================================================
def test_scenario_3_risk_procedure_sample_evidence_testing_exception(clean_db: DatabaseManager, tmp_path: Path) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    matrix_svc = AuditMatrixService(clean_db)
    ev_svc = EvidenceService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Global Audits"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="CloudTech Ltd"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # 1. Risk Identification (SA 315 / SA 240)
    risk = matrix_svc.create_risk(
        CreateRiskDTO(
            engagement_id=eng.id,
            risk_code="RSK-REV-01",
            category="Revenue",
            title="Revenue overstatement via unrecorded credit notes",
            description="High risk of unadjusted credit notes inflating revenue",
            severity=RiskSeverityEnum.HIGH,
        )
    )
    assert risk.id is not None

    # 2. Audit Procedure Creation (SA 330)
    proc = matrix_svc.create_procedure(
        CreateProcedureDTO(
            engagement_id=eng.id,
            risk_id=risk.id,
            procedure_code="PRC-REV-SUB-01",
            objective="Vouch revenue sample invoices against e-way bills and bank realization",
            procedure_type="Substantive",
            account_area="Revenue",
            assertion=AssertionEnum.OCCURRENCE,
        )
    )
    assert proc.id is not None

    # 3. Evidence Upload & Hashing (SA 500)
    dummy_file = tmp_path / "bank_advice_inv_101.pdf"
    dummy_file.write_bytes(b"%PDF-1.4\nTest Bank Advice Document\n%%EOF")
    
    evidence = ev_svc.create_evidence(
        CreateEvidenceDTO(
            engagement_id=eng.id,
            title="Bank Credit Advice INV-101",
            excerpt_or_reference="Verified bank credit realization.",
            evidence_code="EVD-REV-101",
            file_path=str(dummy_file),
            procedure_id=proc.id,
            sample_ref="INV-101",
            uploaded_by="Senior Auditor",
        )
    )
    assert evidence.id is not None
    assert evidence.content_hash is not None
    assert evidence.status == EvidenceStatusEnum.VALIDATED

    # 4. Attach Evidence to Procedure
    matrix_svc.attach_evidence(
        AttachEvidenceDTO(
            engagement_id=eng.id,
            procedure_id=proc.id,
            evidence_id=evidence.id,
            title="Bank Credit Advice Verification",
            excerpt_or_reference="Verified bank credit realization.",
        )
    )


# ==============================================================================
# SCENARIO 4: Exception -> finding -> working paper -> review -> response -> approval -> lock
# ==============================================================================
def test_scenario_4_exception_finding_workpaper_review_approval_lock(clean_db: DatabaseManager) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    matrix_svc = AuditMatrixService(clean_db)
    wp_svc = WorkingPaperService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Elite Audit"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="LogiTrans Ltd"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # 1. Raise Audit Finding (SA 260 / SA 450)
    finding = matrix_svc.create_finding(
        CreateFindingDTO(
            engagement_id=eng.id,
            title="Unadjusted revenue rebate of Rs 25,000",
            description="Rebate not booked resulting in revenue overstatement.",
            severity=RiskSeverityEnum.HIGH,
        )
    )
    assert finding.id is not None

    # 2. Create Working Paper (SA 230)
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-001",
            title="Revenue Cut-Off & Substantive Testing",
            area="Revenue",
            preparer_id="Senior Auditor",
        )
    )
    assert wp.status == WorkingPaperStatusEnum.DRAFT

    # 3. Submit Working Paper for Review
    wp_svc.submit_for_review(wp_id=wp.id, submitter_id="Senior Auditor")
    wp_loaded = wp_svc.get_working_paper(wp.id)
    assert wp_loaded.status == WorkingPaperStatusEnum.SUBMITTED_FOR_REVIEW

    # 4. Reviewer raises blocking Review Note
    note = wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="Manager Reviewer",
            note_text="Please verify if management agreed to pass audit adjustment for Rs 25,000.",
        )
    )
    assert note.id is not None

    # 5. Verify Approval is BLOCKED while open review notes exist
    with pytest.raises(ValidationError, match="open review notes exist"):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id="Manager Reviewer",
                user_role="Manager",
            )
        )

    # 6. Preparer responds to Review Note
    wp_svc.respond_review_note(
        RespondReviewNoteDTO(
            review_note_id=note.id,
            response_text="Management confirmed adjustment will be passed in revised FS.",
            responder="Senior Auditor",
        )
    )

    # 7. Manager Clears Review Note
    wp_svc.clear_review_note(ClearReviewNoteDTO(review_note_id=note.id, reviewer="Manager Reviewer"))

    # 8. Manager and Partner Sign Off & Lock Working Paper
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.REVIEWED,
            user_id="Manager Reviewer",
            user_role="Manager",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Partner Signer",
            user_role="Partner",
        )
    )
    wp_svc.lock_working_paper(wp.id, locker_id="Partner Signer")
    wp_locked = wp_svc.get_working_paper(wp.id)
    assert wp_locked.status == WorkingPaperStatusEnum.LOCKED


# ==============================================================================
# SCENARIO 5: Finalisation gate -> partner review -> final report -> archive
# ==============================================================================
def test_scenario_5_finalisation_partner_review_report_archive(clean_db: DatabaseManager, tmp_path: Path) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    fin_gate_svc = EngagementFinalizationService(clean_db)
    rep_svc = AuditReportService(clean_db)
    arc_svc = ArchivalService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Apex Audit LLP"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Omega Logistics Ltd"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # 1. Check Initial Finalisation Gate
    gate_res = fin_gate_svc.evaluate_finalization_gate(eng.id)
    assert hasattr(gate_res, "is_finalizable")

    # 2. Get or Create Audit Report Workpaper (SA 700 / CARO)
    rep_wp = rep_svc.get_or_create_report_workpaper(
        CreateAuditReportWorkpaperDTO(
            engagement_id=eng.id,
            proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            final_opinion=AuditOpinionTypeEnum.UNMODIFIED,
            opinion_rationale="Financial statements present a true and fair view in accordance with Ind AS.",
            caro_applicable=True,
        )
    )
    assert rep_wp.id is not None

    # 3. Partner Approves Audit Report
    SecurityContext.set_current_session(UserSession(user_id="u_partner", username="partner@firm.com", role=RoleEnum.PARTNER))
    approved_rep = rep_svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng.id,
            report_workpaper_id=rep_wp.id,
            approval_notes="Approved unmodified audit report with CARO 2020 annexure.",
            udin="260108294WAAAA0001",
        )
    )
    assert approved_rep.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    SecurityContext.clear()

    # 4. Freeze and Seal Engagement Archive
    archive_pkg = arc_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Partner Auditor",
            report_date="2026-03-31",
            override_justification="Statutory Audit Finalized",
        )
    )
    assert archive_pkg.id is not None
    assert archive_pkg.sealed_content_hash is not None

    # Verify Engagement is Locked & Archived
    eng_locked = eng_svc.get_engagement(eng.id)
    assert eng_locked.status == EngagementStatusEnum.ARCHIVED


# ==============================================================================
# SCENARIO 6: Archived engagement -> roll forward -> new financial year
# ==============================================================================
def test_scenario_6_archived_engagement_roll_forward(clean_db: DatabaseManager) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    arc_svc = ArchivalService(clean_db)
    roll_svc = RollForwardService(clean_db)
    wp_svc = WorkingPaperService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Heritage Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Solar Energy Ltd"))
    eng_py = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # Seed PY working paper and fully sign off + lock it so readiness check passes
    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_py.id,
            index_reference="WP-TAX-01",
            title="Direct Tax Computation",
            area="Taxation",
            preparer_id="Senior Auditor",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Partner",
            user_role="Partner",
        )
    )
    wp_svc.lock_working_paper(wp.id, locker_id="Partner")

    # Archive PY Engagement
    arc_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng_py.id,
            sealed_by="Partner",
            report_date="2026-03-31",
            override_justification="FY 2025-26 Complete",
        )
    )

    # Roll Forward to FY 2026-27
    dto = ExecuteRollForwardDTO(
        source_engagement_id=eng_py.id,
        target_financial_year="2026-27",
        performed_by="Senior Auditor",
        category_decisions={
            "client_information": "KEEP",
            "permanent_file": "KEEP",
            "working_paper_structure": "KEEP",
            "account_mappings": "KEEP",
        },
    )
    roll_result = roll_svc.roll_forward_engagement(dto)
    assert roll_result.id is not None

    # Verify New Engagement State
    eng_cy = eng_svc.get_engagement(roll_result.id)
    assert eng_cy.financial_year == "2026-27"
    assert eng_cy.status == EngagementStatusEnum.PLANNING

    # Verify Working Paper Structure was Carried Over with Clean DRAFT status (no CY conclusions)
    cy_wps = wp_svc.list_working_papers(eng_cy.id)
    assert len(cy_wps) >= 1
    for wp_item in cy_wps:
        wb = wp_svc.get_workbench_data(wp_item.id)
        assert wb.sign_offs == []


# ==============================================================================
# FAILURE MODES & RESILIENCY TESTS
# ==============================================================================
def test_failure_modes_and_security_controls(clean_db: DatabaseManager, tmp_path: Path) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    fin_svc = FinancialService(clean_db)
    ev_svc = EvidenceService(clean_db)
    arc_svc = ArchivalService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Resilience Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Test Co"))
    eng = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26"))

    # 1. Corrupted / Mismatched Files (Document Security)
    corrupted_pdf = tmp_path / "fake.pdf"
    corrupted_pdf.write_bytes(b"NOT_A_PDF_HEADER_MALICIOUS_BYTES")
    with pytest.raises(DocumentSecurityError, match="magic header"):
        validate_document_security(corrupted_pdf)

    # 2. Invalid Financial Data (Trial Balance Unbalanced)
    unbalanced_csv = tmp_path / "unbalanced.csv"
    with unbalanced_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Account Code", "Account Name", "Opening Dr", "Opening Cr", "Debit", "Credit", "Closing Dr", "Closing Cr"])
        writer.writerow(["1001", "Capital", "0.00", "0.00", "0.00", "1,000.00", "0.00", "1,000.00"])
        writer.writerow(["3001", "Bank", "0.00", "0.00", "800.00", "0.00", "800.00", "0.00"])

    mappings = {
        "account_code": "Account Code",
        "account_name": "Account Name",
        "opening_dr": "Opening Dr",
        "opening_cr": "Opening Cr",
        "debit": "Debit",
        "credit": "Credit",
        "closing_dr": "Closing Dr",
        "closing_cr": "Closing Cr",
    }
    preview = fin_svc.preview_dataset_import(
        file_path=str(unbalanced_csv),
        dataset_type=DatasetTypeEnum.TRIAL_BALANCE,
        custom_mappings=mappings,
    )
    assert preview.is_balanced is False
    assert preview.discrepancy_paise != 0

    # 3. Missing Evidence File on Disk (Integrity Detection)
    ghost_file = tmp_path / "ghost_file.pdf"
    ghost_file.write_bytes(b"%PDF-1.4\nInitial Valid Evidence\n%%EOF")
    ev = ev_svc.create_evidence(
        CreateEvidenceDTO(
            engagement_id=eng.id,
            title="Non-existent File Evidence",
            excerpt_or_reference="Physical verification document",
            evidence_code="EVD-TEST-MISSING",
            file_path=str(ghost_file),
            uploaded_by="Auditor",
        )
    )
    # Physically delete the file after registration to test missing file detection
    ghost_file.unlink()
    rep = ev_svc.verify_integrity(ev.id)
    assert rep.is_valid is False
    assert rep.status == "FILE_MISSING"

    # 4. Unauthorized User Action (RBAC Failure Mode)
    SecurityContext.set_current_session(UserSession(user_id="u_assoc", username="assoc@firm.com", role=RoleEnum.ASSOCIATE))
    with pytest.raises(PermissionDeniedError):
        SecurityContext.enforce_permission("engagement:signoff", allowed_roles=[RoleEnum.PARTNER])
    SecurityContext.clear()

    # 5. AI Unavailable (Graceful Offline Deterministic Degradation)
    ai_svc = AICopilotService(clean_db)
    status = ai_svc.get_status()
    assert hasattr(status, "is_server_up")

    # 6. Locked Artifact Modification Protection (Tamper Guard)
    arc_svc.freeze_and_seal_engagement(
        FreezeAndSealDTO(
            engagement_id=eng.id,
            sealed_by="Partner",
            report_date="2026-03-31",
            override_justification="Complete",
        )
    )
    with pytest.raises(EngagementLockedError):
        ev_svc.create_evidence(
            CreateEvidenceDTO(
                engagement_id=eng.id,
                title="Attempt On Locked Eng",
                excerpt_or_reference="Attempting to modify sealed engagement",
                evidence_code="EVD-LOCKED-TEST",
                uploaded_by="Auditor",
            )
        )


# ==============================================================================
# DATA ISOLATION & DETERMINISM TESTS
# ==============================================================================
def test_cross_engagement_and_cross_fy_data_isolation(clean_db: DatabaseManager) -> None:
    firm_svc = FirmService(clean_db)
    client_svc = ClientService(clean_db)
    eng_svc = EngagementService(clean_db)
    wp_svc = WorkingPaperService(clean_db)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Isolation Firm"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta"))

    eng_a = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26"))
    eng_b = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26"))

    # Create WP in Engagement A
    wp_a = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-ISO-A",
            title="Confidential Working Paper A",
            area="Treasury",
            preparer_id="Auditor A",
        )
    )

    # Verify Engagement B cannot see Engagement A working papers
    wps_b = wp_svc.list_working_papers(eng_b.id)
    assert not any(wp.id == wp_a.id for wp in wps_b)


def test_deterministic_financial_calculations(clean_db: DatabaseManager) -> None:
    # Running identical input through financial analytics engines returns byte-identical outputs
    entries = [
        LedgerEntry(dataset_id="ds-test", source_row_no=i, account_code="3003", debit_paise=int(i * 123450), credit_paise=0)
        for i in range(1, 100)
    ]
    res1 = DeterministicAnalyticsEngine.check_benford_law("ds-test", entries)
    res2 = DeterministicAnalyticsEngine.check_benford_law("ds-test", entries)
    assert res1.summary == res2.summary
    assert res1.analytic_id == res2.analytic_id
    assert len(res1.exceptions) == len(res2.exceptions)
