"""Test suite for Capstone features: 3-Tier Demo Governance, 12 IFC Controls, Dynamic Sampling, 5x5 Heatmap, Tax 3-Way Reconciler, and Knowledge Centre."""

from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.auth_service import AuthService
from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.standard_ifc_controls import (
    ControlTestingResultStatusEnum,
    get_all_standard_controls,
    get_control_by_id,
)
from finauditpro.infrastructure.analytics.ifc_automated_testing_engine import (
    DynamicSampleSizingEngine,
    IFCAutomatedTestingEngine,
)
from finauditpro.infrastructure.analytics.risk_matrix_5x5_engine import (
    RiskMatrix5x5Engine,
    RiskRatingBandEnum,
)
from finauditpro.infrastructure.analytics.tax_gstr2b_reconciler import (
    ITCEligibilityEnum,
    MatchCategoryEnum,
    TaxGSTR2BReconciler,
)
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.knowledge.icai_knowledge_centre import (
    search_knowledge_centre,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.user_repository import UserRepository
from finauditpro.ui.dialogs.login_dialog import LoginDialog


@pytest.fixture
def test_db(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_capstone_governance.db"
    return initialize_database(db_file)


def test_admin_create_and_manage_checker_and_maker_accounts(test_db: DatabaseManager) -> None:
    """Verify Admin can create custom credentials and assign 3-Tier roles (Maker, Checker, Admin)."""
    auth_svc = AuthService(test_db)

    # 1. Setup Initial Admin (Partner / CA)
    admin_sess = auth_svc.setup_initial_admin("ca_admin@firm.com", "AdminSecPass#2026")
    assert admin_sess.username == "ca_admin@firm.com"
    assert admin_sess.role in (RoleEnum.ADMINISTRATOR, RoleEnum.ADMIN, RoleEnum.PARTNER)

    # 2. Admin creates Checker (Audit Senior / Manager)
    checker_user = auth_svc.create_user(
        username="checker_rajesh@firm.com",
        password="CheckerPass#2026",
        role=RoleEnum.CHECKER,
        must_change_password=True,
    )
    assert checker_user.username == "checker_rajesh@firm.com"
    assert checker_user.role == RoleEnum.CHECKER
    assert checker_user.must_change_password is True

    # 3. Admin creates Maker (Audit Assistant)
    maker_user = auth_svc.create_user(
        username="maker_priya@firm.com",
        password="MakerPass#2026",
        role=RoleEnum.MAKER,
        must_change_password=False,
    )
    assert maker_user.username == "maker_priya@firm.com"
    assert maker_user.role == RoleEnum.MAKER
    assert maker_user.must_change_password is False

    # 4. Checker authenticates and is prompted to reset password
    checker_sess = auth_svc.authenticate("checker_rajesh@firm.com", "CheckerPass#2026")
    assert checker_sess.must_change_password is True

    # Checker changes password
    updated_sess = auth_svc.force_change_password(checker_user.id, "CheckerNewPass#2026")
    assert updated_sess.must_change_password is False

    # 5. Maker authenticates directly
    maker_sess = auth_svc.authenticate("maker_priya@firm.com", "MakerPass#2026")
    assert maker_sess.username == "maker_priya@firm.com"
    assert maker_sess.role == RoleEnum.MAKER

    # 6. Admin can update roles and reset passwords
    promoted_maker = auth_svc.update_user_role(maker_user.id, RoleEnum.CHECKER)
    assert promoted_maker.role == RoleEnum.CHECKER

    reset_sess = auth_svc.admin_reset_password(maker_user.id, "MakerResetPass#2026", must_change_password=True)
    assert reset_sess.must_change_password is True


def test_user_management_dialog_and_clean_login(test_db: DatabaseManager) -> None:
    """Verify UserManagementDialog, CreateUserSubDialog, ResetPasswordSubDialog, and clean professional LoginDialog."""
    app = QApplication.instance() or QApplication([])
    auth_svc = AuthService(test_db)
    auth_svc.setup_initial_admin("lead_partner@firm.com", "PartnerPass#2026")

    # 1. Login with Admin credentials
    dialog = LoginDialog(auth_service=auth_svc)
    dialog.input_user.setText("lead_partner@firm.com")
    dialog.input_pass.setText("PartnerPass#2026")
    dialog._handle_login()

    assert dialog.authenticated_session is not None
    assert dialog.authenticated_session.username == "lead_partner@firm.com"

    # 2. Open UserManagementDialog
    from finauditpro.ui.dialogs.user_management_dialog import (
        CreateUserSubDialog,
        ResetPasswordSubDialog,
        UserManagementDialog,
    )

    mgmt_dlg = UserManagementDialog(auth_svc, current_session=dialog.authenticated_session)
    initial_count = mgmt_dlg.table.rowCount()
    assert initial_count >= 1

    # 3. Create a Checker account via CreateUserSubDialog
    create_sub = CreateUserSubDialog(auth_svc)
    create_sub.inp_username.setText("checker_manager@firm.com")
    create_sub.inp_password.setText("CheckerValidPass#123")
    create_sub.combo_role.setCurrentIndex(1)  # Checker
    create_sub._on_save()

    assert create_sub.created_user is not None
    assert create_sub.created_user.username == "checker_manager@firm.com"
    assert create_sub.created_user.role == RoleEnum.CHECKER

    # 4. Create a Maker account via CreateUserSubDialog
    create_maker_sub = CreateUserSubDialog(auth_svc)
    create_maker_sub.inp_username.setText("maker_assistant@firm.com")
    create_maker_sub.inp_password.setText("MakerValidPass#123")
    create_maker_sub.combo_role.setCurrentIndex(0)  # Maker
    create_maker_sub._on_save()

    assert create_maker_sub.created_user is not None
    assert create_maker_sub.created_user.role == RoleEnum.MAKER

    # Refresh management dialog
    mgmt_dlg._load_users()
    assert mgmt_dlg.table.rowCount() == initial_count + 2

    # 5. Reset Password for Maker via ResetPasswordSubDialog
    reset_sub = ResetPasswordSubDialog(auth_svc, create_maker_sub.created_user)
    reset_sub.inp_pwd.setText("MakerNewSecret#456")
    reset_sub.combo_reset.setCurrentIndex(1)  # No reset required
    reset_sub._on_save()

    # Verify Maker can authenticate with the newly updated password
    maker_sess = auth_svc.authenticate("maker_assistant@firm.com", "MakerNewSecret#456")
    assert maker_sess.username == "maker_assistant@firm.com"

    # 6. Verify Segregation of Duties (SoD) Permissions
    from finauditpro.application.security.rbac import RBACManager

    admin_rbac = RBACManager(dialog.authenticated_session)
    assert admin_rbac.has_permission("user:manage") is True
    assert admin_rbac.has_permission("engagement:signoff") is True

    checker_sess = auth_svc.authenticate("checker_manager@firm.com", "CheckerValidPass#123")
    checker_rbac = RBACManager(checker_sess)
    assert checker_rbac.has_permission("audit:review") is True
    assert checker_rbac.has_permission("sample:validate") is True
    assert checker_rbac.has_permission("user:manage") is False

    maker_rbac = RBACManager(maker_sess)
    assert maker_rbac.has_permission("control_testing:execute") is True
    assert maker_rbac.has_permission("workpaper:draft") is True
    assert maker_rbac.has_permission("user:manage") is False
    assert maker_rbac.has_permission("engagement:signoff") is False




def test_12_standard_ifc_controls_catalogue() -> None:
    """Verify preloaded 12 standard IFC controls across 5 business cycles."""
    controls = get_all_standard_controls()
    assert len(controls) == 12

    cycles = {c.cycle for c in controls}
    assert cycles == {"Revenue", "Procurement", "Treasury", "Payroll", "Fixed Assets"}

    # Verify key controls exist
    rev1 = get_control_by_id("IFC-REV-001")
    assert rev1 is not None
    assert "Credit Limit" in rev1.title

    tre2 = get_control_by_id("IFC-TRE-002")
    assert tre2 is not None
    assert "Dual-Signatory" in tre2.title

    far2 = get_control_by_id("IFC-FAR-002")
    assert far2 is not None
    assert "Schedule II" in far2.title


def test_dynamic_sample_sizing_engine() -> None:
    """Verify statistical sample sizing per SA 530 guidance."""
    # Small population (<= 10) -> 100% sample
    res_small = DynamicSampleSizingEngine.calculate_sample_size(population_size=8, risk_level="High")
    assert res_small.recommended_sample_size == 8

    # Medium population High risk -> >= 60 or 40%
    res_high = DynamicSampleSizingEngine.calculate_sample_size(population_size=200, risk_level="High")
    assert res_high.recommended_sample_size >= 60

    # Large population Medium risk -> 25 to 40
    res_med = DynamicSampleSizingEngine.calculate_sample_size(population_size=500, risk_level="Medium")
    assert 25 <= res_med.recommended_sample_size <= 70


def test_ifc_automated_testing_engine() -> None:
    """Verify batch execution of IFC control tests against transaction records."""
    dummy_records = [
        {"voucher_number": "INV-001", "amount_paise": 150000000, "credit_approved": False, "notes": "unauthorized manual override"},
        {"voucher_number": "PAY-001", "amount_paise": 80000000, "signatories": "1"},  # > 5 Lakhs single sig
        {"voucher_number": "INV-002", "amount_paise": 200000, "credit_approved": True},
    ]

    results = IFCAutomatedTestingEngine.test_all_12_controls(dummy_records)
    assert len(results) == 12

    # Check REV-001 exception detected
    rev_res = next(r for r in results if r.control_id == "IFC-REV-001")
    assert rev_res.deviations_found >= 1
    assert len(rev_res.exceptions) >= 1

    # Check TRE-002 exception detected
    tre_res = next(r for r in results if r.control_id == "IFC-TRE-002")
    assert tre_res.deviations_found >= 1


def test_risk_matrix_5x5_and_heatmap_engine() -> None:
    """Verify 5x5 Inherent Risk calculation, control mitigation, and heatmap grid."""
    # High Likelihood (5) x High Impact (4) = 20 (Critical / RoMM)
    score_res = RiskMatrix5x5Engine.evaluate_risk(
        risk_code="RSK-01",
        risk_title="Revenue Cutoff Leakage",
        category="Revenue",
        likelihood=5,
        impact=4,
        control_status="Effective",  # 50% reduction
    )
    assert score_res.inherent_score == 20
    assert score_res.inherent_rating == RiskRatingBandEnum.CRITICAL_ROMM
    assert score_res.residual_score == 10.0  # 20 * 0.5
    assert score_res.residual_rating == RiskRatingBandEnum.MEDIUM
    assert score_res.is_significant_risk is True

    # Generate 5x5 heatmap grid
    grid = RiskMatrix5x5Engine.generate_5x5_heatmap([score_res])
    assert len(grid) == 5
    assert len(grid[0]) == 5
    # Cell (5, 4) should have 1 risk
    top_row = grid[0]  # Likelihood 5
    impact_4_cell = top_row[3]  # Impact 4
    assert impact_4_cell.risks_count == 1
    assert "RSK-01" in impact_4_cell.risk_codes


def test_tax_gstr2b_3way_reconciler() -> None:
    """Verify GSTR-2B vs Books reconciliation and Section 16(2) / 17(5) ITC eligibility flags."""
    books = [
        {"invoice_number": "INV-101", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Steel Corp", "tax_paise": 1800000, "description": "Raw Material Steel"},
        {"invoice_number": "INV-102", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Auto Motors", "tax_paise": 2500000, "description": "Executive Motor Vehicle Purchase"},
        {"invoice_number": "INV-103", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Vendor C", "tax_paise": 500000, "description": "Consulting"},
    ]
    gstr2b = [
        {"invoice_number": "INV-101", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Steel Corp", "tax_paise": 1800000, "supplier_gstr3b_filed": True},
        {"invoice_number": "INV-102", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Auto Motors", "tax_paise": 2500000, "supplier_gstr3b_filed": True},
        {"invoice_number": "INV-999", "supplier_gstin": "27AAACB1234F1Z1", "supplier_name": "Unbooked Vendor", "tax_paise": 300000, "supplier_gstr3b_filed": True},
    ]

    summary = TaxGSTR2BReconciler.reconcile(books, gstr2b)

    assert summary.exact_matches_count == 2
    assert summary.missing_in_2b_count == 1  # INV-103
    assert summary.missing_in_books_count == 1  # INV-999

    # Verify Section 17(5) blocked credit detection on motor vehicle
    mv_item = next(i for i in summary.items if i.invoice_number == "INV-102")
    assert mv_item.itc_eligibility == ITCEligibilityEnum.BLOCKED_SEC_17_5

    # Verify Missing in 2B marked ineligible
    m2b_item = next(i for i in summary.items if i.invoice_number == "INV-103")
    assert m2b_item.match_category == MatchCategoryEnum.MISSING_IN_2B


def test_icai_knowledge_centre_search() -> None:
    """Verify searchable knowledge centre for SAs, CARO 2020, and Schedule III."""
    all_items = search_knowledge_centre("")
    assert len(all_items) >= 11

    # Search for fraud
    fraud_res = search_knowledge_centre("fraud")
    assert any("SA 240" in r.standard_code for r in fraud_res)

    # Search for CARO
    caro_res = search_knowledge_centre("CARO")
    assert any("CARO 2020" in r.standard_code for r in caro_res)

    # Search for materiality
    mat_res = search_knowledge_centre("materiality")
    assert any("SA 320" in r.standard_code for r in mat_res)
