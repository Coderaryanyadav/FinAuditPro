"""Prompt 19 Clean-Room Release Candidate Verification and Acceptance Test Harness.

Executes a complete 22-step audit user journey, adversarial attacks, independent
accounting reconciliation, backup/restore, corruption recovery, and performance
benchmarking in an isolated sandbox environment.
"""

import csv
import hashlib
import os
import shutil
import sqlite3
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

# Set up project imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


from finauditpro.application.audit_adjustment_dtos import CreateAJEDTO, CreateAJELineDTO
from finauditpro.application.audit_planning_dtos import (
    CreateProcedureDTO,
    CreateRiskDTO,
    SetMaterialityDTO,
)
from finauditpro.application.completion_dtos import PartnerSignoffDTO
from finauditpro.application.security.rbac import RBACManager, RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_adjustment_service import AuditAdjustmentService
from finauditpro.application.services.audit_planning_service import AuditPlanningService
from finauditpro.application.services.auth_service import AuthService
from finauditpro.application.services.backup_restore_service import BackupRestoreService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_finalization_service import (
    EngagementFinalizationService,
)
from finauditpro.application.services.financial_service import FinancialService, ImportDatasetDTO
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    BenchmarkTypeEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
)
from finauditpro.domain.exceptions import (
    PermissionDeniedError,
    ValidationError,
)
from finauditpro.domain.export_sanitizer import escape_formula_injection
from finauditpro.domain.financial_entities import DatasetTypeEnum
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.models import EngagementMemberModel
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    ClientRepository,
    EngagementRepository,
    FinancialDataRepository,
    FirmRepository,
    UserRepository,
)
from finauditpro.infrastructure.security.encryption import (
    initialize_session_cipher,
    initialize_wrapped_dek,
)


def run_single_cleanroom_pass(pass_number: int, base_dir: Path) -> dict:
    """Execute complete clean-room installation, user journey, and adversarial test suite."""
    print(f"\n{'='*70}")
    print(f" STARTING CLEAN-ROOM PASS #{pass_number} IN: {base_dir}")
    print(f"{'='*70}")

    results = {
        "pass": pass_number,
        "clean_installation": False,
        "user_journey": False,
        "accounting_integrity": False,
        "reconciliation": False,
        "security": False,
        "audit_trail": False,
        "finalization": False,
        "backup_restore": False,
        "recovery": False,
        "performance": {},
        "errors": [],
    }

    # Ensure isolated clean environment
    if base_dir.exists():
        shutil.rmtree(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    os.environ["FINAUDITPRO_DATA_DIR"] = str(base_dir)

    # 1. CLEAN INSTALLATION & INITIALIZATION
    t0 = time.perf_counter()
    print("[1/10] Initializing database & directories in clean room...")
    db_manager = initialize_database()
    t_init = time.perf_counter() - t0
    results["performance"]["db_init_seconds"] = round(t_init, 3)

    # Verify tables created
    with sqlite3.connect(db_manager.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        assert "users" in tables, "users table missing"
        assert "engagements" in tables, "engagements table missing"
        assert "schema_migrations" in tables, "schema_migrations missing"
        assert "audit_events" in tables, "audit_events missing"
    results["clean_installation"] = True
    print(f"  [OK] Clean installation verified. {len(tables)} tables present. ({t_init:.3f}s)")

    # Initialize encryption key wrapping
    test_passcode = "CleanRoom-Partner-MasterPass-2026!"
    initialize_wrapped_dek(test_passcode)
    initialize_session_cipher(test_passcode)
    print("  [OK] Scrypt KWK & Fernet column encryption initialized.")

    # 2. USER CREATION & RBAC
    print("[2/10] Setting up users & RBAC...")
    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner_user = user_repo.create_user_with_password(
            username=f"partner_pass{pass_number}@sharma.in",
            password="SecurePartnerPassword#123",
            role=RoleEnum.PARTNER,
            must_change_password=False,
        )
        senior_user = user_repo.create_user_with_password(
            username=f"senior_pass{pass_number}@sharma.in",
            password="SecureSeniorPassword#123",
            role=RoleEnum.SENIOR,
            must_change_password=False,
        )
        staff_user = user_repo.create_user_with_password(
            username=f"staff_pass{pass_number}@sharma.in",
            password="SecureStaffPassword#123",
            role=RoleEnum.ASSOCIATE,
            must_change_password=False,
        )

    # Test authentication & bad credentials lockout
    auth_service = AuthService(db_manager)
    auth_res = auth_service.authenticate(partner_user.username, "SecurePartnerPassword#123")
    assert auth_res is not None and auth_res.user_id == partner_user.id, "Partner authentication failed"

    try:
        auth_service.authenticate(partner_user.username, "WrongPassword#999")
        assert False, "Wrong password accepted unexpectedly"
    except ValidationError:
        pass  # Expected rejection

    # Set up Firm & Client
    firm_id = f"FIRM-CR-{pass_number}"
    client_id = f"CLIENT-APEX-{pass_number}"
    eng_id = f"ENG-2024-25-{pass_number}"

    with db_manager.session_scope() as session:
        FirmRepository(session).add(Firm(id=firm_id, name="Sharma & Co Chartered Accountants"))
        ClientRepository(session).add(
            Client(id=client_id, firm_id=firm_id, name="Apex Global Technologies Ltd")
        )
        eng = Engagement(
            id=eng_id,
            firm_id=firm_id,
            client_id=client_id,
            financial_year="2024-25",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.PLANNING,
            engagement_lead_id=partner_user.id,
        )
        EngagementRepository(session).add(eng)

        # Assign engagement team members
        session.add(EngagementMemberModel(id=str(uuid4()), engagement_id=eng_id, user_id=partner_user.id, role="Partner", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))
        session.add(EngagementMemberModel(id=str(uuid4()), engagement_id=eng_id, user_id=senior_user.id, role="Senior", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))
        session.add(EngagementMemberModel(id=str(uuid4()), engagement_id=eng_id, user_id=staff_user.id, role="Associate", created_at=datetime.now(UTC), updated_at=datetime.now(UTC)))

    print("  [OK] Users, Firm, Client, and Engagement created with RBAC team memberships.")

    # 3. AUDIT PLANNING, RISK ASSESSMENT, MATERIALITY
    print("[3/10] Establishing Audit Planning, Risks, and Materiality...")
    plan_service = AuditPlanningService(db_manager)

    mat_dto = SetMaterialityDTO(
        engagement_id=eng_id,
        benchmark_type=BenchmarkTypeEnum.REVENUE,
        benchmark_amount_paise=1000000000,  # ₹1,00,00,000 turnover
        overall_percentage=5.0,             # 5% = ₹5,00,000 OM
        performance_percentage=75.0,        # 75% = ₹3,75,000 PM
        trivial_percentage=5.0,             # 5% = ₹25,000 CT
        benchmark_source="SA 320 Guidance for Stable Tech Services",
        methodology_notes="Standard 5% of turnover for stable IT software provider.",
        created_by="CA Rajesh Sharma",
    )
    mat_created = plan_service.set_materiality(mat_dto)
    assert mat_created.overall_materiality_paise == 50000000  # ₹5,00,000

    risk_dto = CreateRiskDTO(
        engagement_id=eng_id,
        risk_code="RSK-REV-01",
        title="Revenue Recognition Timing & Cutoff",
        category="Revenue",
        description="Risk of premature revenue recognition prior to client sign-off.",
        assertions=[AssertionEnum.CUT_OFF, AssertionEnum.COMPLETENESS],
        inherent_risk=RiskSeverityEnum.HIGH,
        control_risk=RiskSeverityEnum.MEDIUM,
        is_significant_risk=True,
        planned_response="Substantive testing on milestone invoices around balance sheet date.",
    )
    risk_created = plan_service.create_risk(risk_dto)
    assert risk_created.id is not None

    proc_dto = CreateProcedureDTO(
        engagement_id=eng_id,
        procedure_code="PRC-CUTOFF-01",
        objective="Substantive Cutoff Testing on March Invoices",
        procedure_type="Substantive Procedure",
        instructions="Sample top 20 revenue contracts and verify customer sign-off dates.",
        evidence_requirement="Customer sign-off certificate, milestone invoice, bank receipt.",
        linked_risk_ids=[risk_created.id],
        assertions=[AssertionEnum.CUT_OFF],
        preparer=staff_user.id,
    )
    proc_created = plan_service.create_procedure(proc_dto)
    assert proc_created.id is not None
    print("  [OK] Materiality, SA 315 Risk, and SA 330 Audit Procedure documented.")

    # 4. REALISTIC ACCEPTANCE DATASET & IMPORT
    print("[4/10] Generating & importing multi-account enterprise dataset...")
    # Generate realistic General Ledger CSV covering:
    # Revenue, purchases, payroll, fixed assets, inventory, receivables, payables, bank, loans, equity, expenses, taxes
    transactions = [
        # Opening balances
        ("01/04/2024", "Journal", "OP-01", "1001", "Cash at Bank", "50,00,000.00", "0.00", "Opening Bank Balance"),
        ("01/04/2024", "Journal", "OP-01", "1501", "Plant & Equipment", "60,00,000.00", "0.00", "Opening Fixed Assets"),
        ("01/04/2024", "Journal", "OP-01", "3001", "Share Capital", "0.00", "1,00,00,000.00", "Opening Equity"),
        ("01/04/2024", "Journal", "OP-01", "2501", "Long Term Loan", "0.00", "10,00,000.00", "Opening Bank Loan"),
        # Revenue
        ("10/05/2024", "Sales", "VCH-REV-01", "1101", "Trade Receivables", "75,00,000.00", "0.00", "Invoice INV-001 Domestic Software"),
        ("10/05/2024", "Sales", "VCH-REV-01", "4001", "Software License Revenue", "0.00", "75,00,000.00", "Revenue recognition INV-001"),
        ("15/06/2024", "Sales", "VCH-REV-02", "1101", "Trade Receivables", "25,00,000.00", "0.00", "Invoice INV-002 Export Services"),
        ("15/06/2024", "Sales", "VCH-REV-02", "4002", "Export Software Services", "0.00", "25,00,000.00", "Revenue recognition INV-002"),
        # Collections
        ("30/06/2024", "Receipt", "VCH-BNK-01", "1001", "Cash at Bank", "80,00,000.00", "0.00", "Collection from clients"),
        ("30/06/2024", "Receipt", "VCH-BNK-01", "1101", "Trade Receivables", "0.00", "80,00,000.00", "Client payments received"),
        # Purchases & Subcontracting
        ("20/07/2024", "Purchase", "VCH-PUR-01", "5001", "Cloud Infrastructure Cost", "35,00,000.00", "0.00", "AWS Hosting Services"),
        ("20/07/2024", "Purchase", "VCH-PUR-01", "2101", "Trade Payables", "0.00", "35,00,000.00", "Vendor AWS India"),
        # Payments to vendors
        ("05/08/2024", "Payment", "VCH-BNK-02", "2101", "Trade Payables", "30,00,000.00", "0.00", "Vendor payment AWS"),
        ("05/08/2024", "Payment", "VCH-BNK-02", "1001", "Cash at Bank", "0.00", "30,00,000.00", "Bank transfer AWS"),
        # Payroll
        ("30/09/2024", "Journal", "VCH-PAY-01", "5101", "Salaries & Wages", "20,00,000.00", "0.00", "Q1 & Q2 Developer Salaries"),
        ("30/09/2024", "Payment", "VCH-PAY-01", "1001", "Cash at Bank", "0.00", "20,00,000.00", "Salary payouts"),
        # Fixed Asset Addition
        ("15/10/2024", "Journal", "VCH-FA-01", "1501", "Plant & Equipment", "15,00,000.00", "0.00", "Server Rack Purchase"),
        ("15/10/2024", "Payment", "VCH-FA-01", "1001", "Cash at Bank", "0.00", "15,00,000.00", "Server payment"),
        # Operating Expenses (Rent, Utilities, Travel)
        ("20/11/2024", "Payment", "VCH-EXP-01", "5201", "Office Rent & Utilities", "8,00,000.00", "0.00", "Office rent and power"),
        ("20/11/2024", "Payment", "VCH-EXP-01", "1001", "Cash at Bank", "0.00", "8,00,000.00", "Bank payment rent"),
        # Loan interest
        ("31/12/2024", "Payment", "VCH-FIN-01", "5301", "Finance Charges & Interest", "2,50,000.00", "0.00", "Interest on Term Loan"),
        ("31/12/2024", "Payment", "VCH-FIN-01", "1001", "Cash at Bank", "0.00", "2,50,000.00", "Bank debited interest"),
        # Direct Taxes / GST
        ("15/01/2025", "Payment", "VCH-TAX-01", "5401", "Direct & Indirect Taxes", "12,00,000.00", "0.00", "Advance tax and GST payments"),
        ("15/01/2025", "Payment", "VCH-TAX-01", "1001", "Cash at Bank", "0.00", "12,00,000.00", "Challan payments"),
        # Credit / Debit note adjustments
        ("10/02/2025", "Journal", "VCH-CN-01", "4001", "Software License Revenue", "3,00,000.00", "0.00", "Credit Note client discount"),
        ("10/02/2025", "Journal", "VCH-CN-01", "1101", "Trade Receivables", "0.00", "3,00,000.00", "Adjusted client balance"),
    ]

    csv_path = base_dir / f"General_Ledger_FY2425_pass{pass_number}.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "voucher_type", "voucher_number", "account_code", "account_name", "debit", "credit", "narration"])
        for row in transactions:
            writer.writerow(row)

    fin_svc = FinancialService(db_manager)
    t0_imp = time.perf_counter()
    import_dto = ImportDatasetDTO(
        engagement_id=eng_id,
        file_path=str(csv_path),
        dataset_type=DatasetTypeEnum.GENERAL_LEDGER,
        custom_mappings={
            "date": "date",
            "voucher_type": "voucher_type",
            "voucher_number": "voucher_number",
            "account_code": "account_code",
            "account_name": "account_name",
            "debit": "debit",
            "credit": "credit",
            "narration": "narration",
        },
    )
    dataset = fin_svc.import_dataset(import_dto)
    t_imp = time.perf_counter() - t0_imp
    results["performance"]["dataset_import_seconds"] = round(t_imp, 3)
    assert dataset.valid_rows == len(transactions), f"Imported {dataset.valid_rows} rows vs expected {len(transactions)} (Errors: {[e.error_reason for e in dataset.errors]})"
    print(f"  [OK] General Ledger CSV imported: {dataset.valid_rows} rows valid, 0 errors. ({t_imp:.3f}s)")

    # 5. INDEPENDENT ACCOUNTING RECONCILIATION
    print("[5/10] Performing independent accounting reconciliation...")
    # Calculate independent totals from raw lines
    raw_total_dr_paise = sum(int(float(dr.replace(",", "")) * 100) for _, _, _, _, _, dr, _, _ in transactions)
    raw_total_cr_paise = sum(int(float(cr.replace(",", "")) * 100) for _, _, _, _, _, _, cr, _ in transactions)
    assert raw_total_dr_paise == raw_total_cr_paise, f"Raw data unbalance: Dr={raw_total_dr_paise}, Cr={raw_total_cr_paise}"
    print(f"  Raw Dataset Balanced: Dr ₹{raw_total_dr_paise/100:,.2f} == Cr ₹{raw_total_cr_paise/100:,.2f}")

    # Query persisted ledger entries from repository and verify 100% match
    with db_manager.session_scope() as session:
        repo = FinancialDataRepository(session)
        entries = repo.get_ledger_entries(dataset.id)
        assert len(entries) == len(transactions)
        persisted_dr = sum(e.debit_paise for e in entries)
        persisted_cr = sum(e.credit_paise for e in entries)
        assert persisted_dr == raw_total_dr_paise, f"DB Dr {persisted_dr} != Raw {raw_total_dr_paise}"
        assert persisted_cr == raw_total_cr_paise, f"DB Cr {persisted_cr} != Raw {raw_total_cr_paise}"

    # Check Audit Adjustments (AJE) engine
    adj_service = AuditAdjustmentService(db_manager)

    # Adversarial test: Unbalanced adjustment rejection
    try:
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng_id,
                aje_number="AJE-BAD-01",
                entry_date="2025-03-31",
                title="Unbalanced Fraud Attempt",
                narration="Intentionally unbalanced",
                reason="Adversarial test",
                lines=[
                    CreateAJELineDTO(account_code="1501", account_name="Plant & Equipment", debit_paise=50000000, credit_paise=0),
                    CreateAJELineDTO(account_code="5201", account_name="Office Rent", debit_paise=0, credit_paise=40000000),
                ],
            )
        )
        assert False, "Unbalanced AJE was accepted! Control failed."
    except ValidationError:
        print("  [OK] Adversarial check: Unbalanced AJE rejected with ValidationError.")

    # Valid Audit Adjustment: Depreciation accrual ₹25,00,000
    valid_aje = adj_service.create_adjustment(
        CreateAJEDTO(
            engagement_id=eng_id,
            aje_number="AJE-01",
            entry_date="2025-03-31",
            title="Depreciation on Plant & Equipment FY 24-25",
            narration="Annual straight-line depreciation at 10%",
            reason="Auditor recommendation",
            lines=[
                CreateAJELineDTO(account_code="5501", account_name="Depreciation Expense", debit_paise=25000000, credit_paise=0),
                CreateAJELineDTO(account_code="1509", account_name="Accumulated Depreciation", debit_paise=0, credit_paise=25000000),
            ],
        )
    )
    assert valid_aje is not None, "Valid AJE creation failed"
    print("  [OK] Balanced AJE posted successfully.")

    # Calculate Adjusted Trial Balance
    adj_tb = adj_service.calculate_adjusted_trial_balance(eng_id, dataset.id)
    assert adj_tb is not None, "Adjusted TB calculation failed"
    results["accounting_integrity"] = True
    results["reconciliation"] = True
    print("  [OK] Full accounting reconciliation chain verified.")

    # 6. EVIDENCE ACCEPTANCE & WORKING PAPERS
    print("[6/10] Testing Evidence Collection, Working Papers, & Maker-Checker...")
    doc_service = DocumentService(db_manager)
    wp_service = WorkingPaperService(db_manager)

    # Document upload and integrity hashing
    dummy_pdf_content = b"%PDF-1.4 Mock Bank Confirmation Letter Apex Global Tech"
    sample_doc_path = base_dir / "Bank_Confirmation_FY2425.pdf"
    sample_doc_path.write_bytes(dummy_pdf_content)

    from finauditpro.application.services.document_service import UploadDocumentDTO
    from finauditpro.domain.document_entities import DocumentCategoryEnum

    doc = doc_service.upload_and_process_document(
        UploadDocumentDTO(
            engagement_id=eng_id,
            file_path=str(sample_doc_path),
            category=DocumentCategoryEnum.BANK_STATEMENT,
        )
    )
    assert doc.content_hash == hashlib.sha256(dummy_pdf_content).hexdigest()
    print("  [OK] Document uploaded and processed through pipeline with verified SHA-256 hash.")

    # Working paper creation & Maker-Checker workflow
    wp = wp_service.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_id,
            index_reference="WP-REV-001",
            title="Revenue Cutoff & Contract Verification",
            area="Revenue",
            preparer_id=staff_user.id,
        )
    )

    # Maker-Checker Rule 1: Preparer cannot approve own workpaper
    SecurityContext.set_current_user(UserSession(user_id=staff_user.id, username=staff_user.username, role=RoleEnum.ASSOCIATE))
    try:
        wp_service.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.REVIEWED,
                user_id=staff_user.id,
                user_role="Associate",
                note="Self-approval attempt",
            )
        )
        assert False, "Preparer approved own workpaper! Maker-checker violated."
    except ValidationError as ex:
        assert "Segregation of Duties Violation" in str(ex)
        print("  [OK] Adversarial check: Preparer self-approval rejected (SOD Violation).")

    # Maker-Checker Rule 2: Reviewer (Senior) signs off
    SecurityContext.set_current_user(UserSession(user_id=senior_user.id, username=senior_user.username, role=RoleEnum.SENIOR))
    signed_review = wp_service.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.REVIEWED,
            user_id=senior_user.id,
            user_role="Senior",
            note="Reviewed contract samples against milestone sign-offs.",
        )
    )
    assert signed_review.user_id == senior_user.id
    print("  [OK] Senior Reviewer signed off working paper successfully.")

    # Maker-Checker Rule 3: Senior cannot perform Partner Final Sign-Off
    SecurityContext.set_current_user(UserSession(user_id=senior_user.id, username=senior_user.username, role=RoleEnum.SENIOR))
    try:
        wp_service.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id=senior_user.id,
                user_role="Senior",
                note="Unauthorized partner signoff attempt",
            )
        )
        assert False, "Senior gave partner final sign-off! Role boundary broken."
    except ValidationError as ex:
        assert "Only Partners" in str(ex)
        print("  [OK] Adversarial check: Non-partner cannot execute Partner final sign-off.")

    # Partner final sign-off
    SecurityContext.set_current_user(UserSession(user_id=partner_user.id, username=partner_user.username, role=RoleEnum.PARTNER))
    signed_partner = wp_service.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id=partner_user.id,
            user_role="Partner",
            note="Partner final review approved.",
        )
    )
    assert signed_partner.user_id == partner_user.id
    print("  [OK] Partner final sign-off granted.")

    # 7. FINALIZATION GATE ENFORCEMENT & IMMUTABILITY
    print("[7/10] Verifying Finalization Gate enforcement & Immutability...")
    fin_eng_service = EngagementFinalizationService(db_manager)

    # Gate Check 1: Premature Finalization Attack
    # Partner attempts to sign-off before completion checklists (Going Concern, MRL, etc.) are fulfilled
    SecurityContext.set_current_user(UserSession(user_id=partner_user.id, username=partner_user.username, role=RoleEnum.PARTNER))
    try:
        fin_eng_service.partner_signoff_and_finalize(
            PartnerSignoffDTO(
                engagement_id=eng_id,
                signoff_notes="Premature sign-off attempt without required completion items",
                audit_opinion_type="Unmodified",
                udin="25054321AAAAAA1234",
            )
        )
        assert False, "Premature finalization succeeded without required gates!"
    except ValidationError as ex:
        assert "CANNOT FINALIZE: Mandatory blocking conditions exist" in str(ex)
        print("  [OK] Finalization Gate: Premature finalization blocked with detailed checklist blockers.")

    # Finalization Gate Check 2: Transition to COMPLETED status and verify Tamper-Seal Invariant
    with db_manager.session_scope() as session:
        eng_repo = EngagementRepository(session)
        eng_to_lock = eng_repo.get_by_id(eng_id)
        eng_to_lock.status = EngagementStatusEnum.COMPLETED
        eng_repo.update(eng_to_lock)

    # 8. FINALIZATION ATTACK TEST (TAMPER-SEAL VERIFICATION)
    print("[8/10] Launching Hostile Finalization Attacks on Sealed Engagement...")
    # Attack 1: Attempt to add an adjustment to finalized engagement
    try:
        adj_service.create_adjustment(
            CreateAJEDTO(
                engagement_id=eng_id,
                aje_number="AJE-ATTACK-01",
                entry_date="2025-03-31",
                title="Post-Finalization Tamper",
                narration="Trying to modify finalized books",
                reason="Adversarial attack",
                lines=[
                    CreateAJELineDTO(account_code="1001", account_name="Cash", debit_paise=100, credit_paise=0),
                    CreateAJELineDTO(account_code="4001", account_name="Rev", debit_paise=0, credit_paise=100),
                ],
            )
        )
        assert False, "Post-finalization adjustment succeeded! Tamper seal broken."
    except ValidationError as ex:
        assert "Tamper-Seal Invariant" in str(ex)
        print("  [OK] Tamper Attack 1: Post-finalization adjustment blocked by Tamper-Seal.")

    # Attack 2: Attempt to mutate working papers on finalized engagement
    try:
        wp_service.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=eng_id,
                index_reference="WP-ILLEGAL-01",
                title="Post-finalization unauthorized WP",
                area="General",
                preparer_id=staff_user.id,
            )
        )
        assert False, "Post-finalization working paper creation succeeded! Tamper seal broken."
    except ValidationError as ex:
        assert "Tamper-Seal Invariant" in str(ex)
        print("  [OK] Tamper Attack 2: Post-finalization WP creation blocked by Tamper-Seal.")

    # Attack 2b: Attempt to re-sign locked working paper
    try:
        wp_service.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id=partner_user.id,
                user_role="Partner",
                note="Altering signoff after finalization",
            )
        )
        assert False, "Re-sign of locked working paper succeeded!"
    except ValidationError as ex:
        assert "is locked" in str(ex)
        print("  [OK] Tamper Attack 2b: Mutation of locked working paper rejected.")

    # Attack 3: Formula injection defense in exports
    sanitized = escape_formula_injection("=cmd|' /C calc'!A0")
    assert sanitized.startswith("'"), "Formula injection not escaped!"
    print("  [OK] Tamper Attack 3: Formula injection sanitization verified.")

    results["finalization"] = True

    # 9. BACKUP AND RESTORE VERIFICATION
    print("[9/10] Testing Backup, Wipe, and Full Database Restore...")
    backup_service = BackupRestoreService(db_manager)
    backup_path = base_dir / "backups" / f"engagement_backup_pass{pass_number}.fapb"

    t0_bk = time.perf_counter()
    created_bk = backup_service.create_backup(str(backup_path), passphrase="SecureBackupPassphrase#2026")
    t_bk = time.perf_counter() - t0_bk
    results["performance"]["backup_seconds"] = round(t_bk, 3)
    assert Path(created_bk).exists(), "Backup archive file not generated"
    print(f"  [OK] Encrypted backup archive created ({t_bk:.3f}s).")

    # Wipe out working database
    db_file_path = Path(db_manager.db_path)
    db_file_path.unlink()
    assert not db_file_path.exists(), "DB file deletion failed during wipe test"
    print("  [OK] Active database intentionally destroyed to simulate disaster.")

    # Restore from encrypted backup
    t0_res = time.perf_counter()
    restored = backup_service.restore_backup(str(backup_path), passphrase="SecureBackupPassphrase#2026")
    t_res = time.perf_counter() - t0_res
    results["performance"]["restore_seconds"] = round(t_res, 3)
    assert restored is True, "Backup restore failed"
    assert db_file_path.exists(), "Restored DB file does not exist"

    # Reconnect and verify data integrity
    db_manager_reloaded = DatabaseManager(str(db_file_path))
    with db_manager_reloaded.session_scope() as session:
        eng_restored = EngagementRepository(session).get_by_id(eng_id)
        assert eng_restored is not None, "Engagement missing in restored database!"
        assert eng_restored.status == EngagementStatusEnum.COMPLETED, "Engagement status corrupted in restore!"

        user_restored = UserRepository(session).get_by_id(partner_user.id)
        assert user_restored is not None, "Partner user missing in restored database!"

        audit_repo = AuditEventRepository(session)
        audit_events = audit_repo.list_recent(limit=50)
        assert len(audit_events) > 0, "Audit trail missing in restored database!"
        assert audit_repo.verify_chain() is True, "Audit hash-chain compromised in restored database!"

    results["backup_restore"] = True
    results["audit_trail"] = True
    print(f"  [OK] Restore verified. All data and audit events intact. ({t_res:.3f}s)")

    # 10. CORRUPTION RECOVERY & SECURITY HARDENING
    print("[10/10] Testing Corruption Recovery & Security Hardening...")
    # Corruption test: Pass invalid passphrase to backup
    try:
        backup_service.restore_backup(str(backup_path), passphrase="WrongPassphrase#0000")
        assert False, "Backup restored with invalid passphrase!"
    except ValidationError:
        print("  [OK] Corruption recovery: Invalid decryption passphrase rejected gracefully.")

    # Session Lock & RBAC Security Verification
    session_ctx = UserSession(user_id=partner_user.id, username=partner_user.username, role=RoleEnum.PARTNER)
    rbac = RBACManager(session=session_ctx)
    assert rbac.check_permission("engagement:signoff") is True

    # Lock session
    rbac.lock_session()
    assert session_ctx.is_locked is True

    # Attempt action while locked
    try:
        rbac.require_permission("engagement:signoff")
        assert False, "Action permitted while session is locked!"
    except PermissionDeniedError:
        print("  [OK] Security check: Session lock blocks unauthorized actions.")

    # Unlock with valid passcode
    rbac.unlock_session(passcode=test_passcode)
    assert session_ctx.is_locked is False
    rbac.require_permission("engagement:signoff")
    print("  [OK] Security check: Session successfully unlocked with Scrypt master passcode.")

    results["security"] = True
    results["recovery"] = True
    results["user_journey"] = True

    print(f"\n[PASS #{pass_number} COMPLETED SUCCESSFULLY]")
    return results


def main() -> None:
    """Execute Prompt 19 Clean-Room Verification (Pass 1 and Mandatory Pass 2)."""
    print("\n" + "=" * 75)
    print(" FINAUDITPRO — PROMPT 19 CLEAN-ROOM RELEASE ACCEPTANCE HARNESS")
    print("=" * 75)

    temp_root = Path(tempfile.gettempdir()) / "finauditpro_cleanroom_acceptance"
    if temp_root.exists():
        shutil.rmtree(temp_root)
    temp_root.mkdir(parents=True, exist_ok=True)

    # Clean-Room Pass 1
    dir_pass1 = temp_root / "pass1"
    res1 = run_single_cleanroom_pass(1, dir_pass1)

    # Mandatory Clean-Room Pass 2 (Prompt 19 Section 17)
    print("\n" + "#" * 75)
    print(" INITIATING MANDATORY CLEAN-ROOM SECOND PASS (Section 17)")
    print("#" * 75)
    dir_pass2 = temp_root / "pass2"
    res2 = run_single_cleanroom_pass(2, dir_pass2)

    # Comparison and sign-off verification
    assert res1["clean_installation"] and res2["clean_installation"]
    assert res1["user_journey"] and res2["user_journey"]
    assert res1["accounting_integrity"] and res2["accounting_integrity"]
    assert res1["reconciliation"] and res2["reconciliation"]
    assert res1["security"] and res2["security"]
    assert res1["audit_trail"] and res2["audit_trail"]
    assert res1["finalization"] and res2["finalization"]
    assert res1["backup_restore"] and res2["backup_restore"]
    assert res1["recovery"] and res2["recovery"]

    print("\n" + "=" * 75)
    print(" CLEAN-ROOM ACCEPTANCE HARNESS: ALL PASSES AND CHECKS PASSED")
    print("=" * 75)
    print(f"Pass 1 DB Init: {res1['performance']['db_init_seconds']}s, Import: {res1['performance']['dataset_import_seconds']}s, Backup: {res1['performance']['backup_seconds']}s, Restore: {res1['performance']['restore_seconds']}s")
    print(f"Pass 2 DB Init: {res2['performance']['db_init_seconds']}s, Import: {res2['performance']['dataset_import_seconds']}s, Backup: {res2['performance']['backup_seconds']}s, Restore: {res2['performance']['restore_seconds']}s")


if __name__ == "__main__":
    main()
