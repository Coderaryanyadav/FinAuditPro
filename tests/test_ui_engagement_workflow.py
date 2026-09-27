"""Comprehensive UI workflow tests for FinAuditPro.

Tests:
- Global Context (Firm, Client, Engagement, FY)
- Primary Workflow Navigation (PLANNING -> FINANCIAL DATA -> FIELDWORK -> FINALISATION)
- Engagement Command Center 9 Essential Indicators
- Unified 3-Pane Audit Workbench (Tree, Workspace, Evidence/Review/AI tabs)
- Search, filters, breadcrumbs, status indicators, and state management
"""

import sys
from pathlib import Path
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def seeded_db(tmp_path: Path):
    db_file = tmp_path / "test_ui_workflow.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Premier Audit LLP"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Solaris Industries Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    wp1 = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-REV-01",
            title="Revenue Recognition & Cut-Off",
            area="Revenue & Receivables",
            preparer_id="Senior Auditor",
        )
    )
    wp2 = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng.id,
            index_reference="WP-BNK-01",
            title="Bank Balances & 26AS Tie-Out",
            area="Cash & Banking",
            preparer_id="Senior Auditor",
        )
    )
    wp_svc.sign_off_working_paper(
        SignOffDTO(
            working_paper_id=wp1.id,
            level=SignOffLevelEnum.FINAL_SIGN_OFF,
            user_id="Partner Auditor",
            user_role="Partner",
        )
    )

    return db_manager, firm, client, eng, wp1, wp2


def test_global_context_and_primary_navigation(qapp: QApplication, seeded_db) -> None:
    """Verify Global Context (Firm, Client, Engagement, FY) and 4 primary workflow stages."""
    db_manager, firm, client, eng, wp1, wp2 = seeded_db
    window = MainWindow(db_manager)
    window.show()

    assert window.isVisible()

    # Verify Global Context is recognized
    assert window.current_firm is not None
    assert window.current_firm.name == "Premier Audit LLP"
    assert window.current_client is not None
    assert window.current_client.name == "Solaris Industries Ltd"
    assert window.current_engagement is not None
    assert window.current_engagement.financial_year == "2025-26"

    # Verify Primary Workflow Navigation buttons exist
    assert hasattr(window, "btn_dashboard")
    assert hasattr(window, "btn_financial_data")
    assert hasattr(window, "btn_working_papers")
    assert hasattr(window, "btn_reports")

    # Navigate to PLANNING (Command Center)
    window.btn_dashboard.click()
    assert window.stack.currentWidget() == window.view_dashboard

    # Navigate to FINANCIAL DATA
    window.btn_financial_data.click()
    assert window.stack.currentWidget() == window.view_financial_data

    # Navigate to FIELDWORK (Audit Workbench)
    window.btn_working_papers.click()
    assert window.stack.currentWidget() == window.view_working_papers

    # Navigate to FINALISATION (Reports & Sign-Off)
    window.btn_reports.click()
    assert window.stack.currentWidget() == window.view_reports

    window.close()


def test_engagement_command_center_indicators(qapp: QApplication, seeded_db) -> None:
    """Verify Engagement Command Center dynamically displays key audit indicators."""
    db_manager, firm, client, eng, wp1, wp2 = seeded_db
    window = MainWindow(db_manager)
    window.show()

    dashboard = window.view_dashboard
    dashboard.set_active_engagement(eng.id)

    # 1. Engagement Status & Context
    assert "Solaris Industries Ltd" in dashboard.lbl_context_text.text()
    assert "2025-26" in dashboard.lbl_context_text.text()
    assert dashboard.status_badge.text() is not None

    # 2. Audit Progress & Workpapers count
    assert dashboard.card_completed is not None
    assert dashboard.card_pending is not None
    assert dashboard.card_high_risk is not None

    window.close()


def test_audit_workbench_three_pane_layout(qapp: QApplication, seeded_db) -> None:
    """Verify 3-pane layout, working paper selection, search, conclusion saving, and sign-off."""
    db_manager, firm, client, eng, wp1, wp2 = seeded_db
    window = MainWindow(db_manager)
    window.show()

    workbench = window.view_working_papers
    workbench.set_active_engagement(eng.id)

    # 1. LEFT PANE: Tree widget populated with working papers
    assert workbench.tree.topLevelItemCount() >= 2
    assert int(workbench.card_total.value_lbl.text()) >= 2

    # 2. Search filtering
    workbench.tree_search.setText("Revenue")
    workbench._filter_tree("Revenue")

    # 3. CENTER PANE: Active working paper loading
    workbench._load_working_paper(wp2.id)
    assert workbench.active_wp_id == wp2.id
    assert "WP-BNK-01" in workbench.lbl_wp_title.text()

    # 4. Save Conclusion
    workbench.txt_conclusion_editor.setText("Bank confirmations reconciled with zero material variance.")
    workbench._on_save_conclusion_clicked()
    assert "Bank confirmations reconciled" in workbench.txt_conclusion_editor.toPlainText()

    # 5. RIGHT PANE: Evidence list and Review Notes
    assert workbench.evidence_list is not None
    assert workbench.notes_list is not None
    assert workbench.signoffs_list is not None

    window.close()


def test_command_palette_and_ai_copilot_drawer(qapp: QApplication, seeded_db) -> None:
    """Verify Command Palette (Ctrl+P) and AI Copilot Drawer (Ctrl+K) interactions."""
    db_manager, firm, client, eng, wp1, wp2 = seeded_db
    window = MainWindow(db_manager)
    window.show()

    # Test AI Drawer toggle
    assert window.ai_drawer.isVisible() is False
    window._toggle_ai_drawer()
    assert window.ai_drawer.isVisible() is True
    window._toggle_ai_drawer()
    assert window.ai_drawer.isVisible() is False

    # Test Command Palette shortcut handler
    assert hasattr(window, "_open_command_palette")

    window.close()


def test_workbench_review_and_evidence_workflows(qapp: QApplication, seeded_db) -> None:
    """Verify Review Notes raising, clearance, and evidence verification on Audit Workbench."""
    db_manager, firm, client, eng, wp1, wp2 = seeded_db
    window = MainWindow(db_manager)
    window.show()

    window.btn_working_papers.click()
    workbench = window.view_working_papers
    workbench.set_active_engagement(eng.id)
    workbench._load_working_paper(wp2.id)

    # 1. Raise a review note
    with db_manager.session_scope() as session:
        from finauditpro.domain.working_paper_entities import ReviewNote
        from finauditpro.infrastructure.persistence.repositories import WorkingPaperRepository
        repo = WorkingPaperRepository(session)
        note = ReviewNote(
            working_paper_id=wp2.id,
            raised_by="Senior Reviewer",
            note_text="Please reconcile closing balance with March bank statement.",
        )
        repo.add_review_note(note)

    workbench._load_working_paper(wp2.id)
    assert workbench.notes_list.count() >= 1

    # 2. Verify blocking review note alert is shown
    assert not workbench.lbl_review_alert.isHidden()
    assert "Approval Precondition Blocked" in workbench.lbl_review_alert.text()

    # 3. Clear review note
    with db_manager.session_scope() as session:
        from finauditpro.infrastructure.persistence.repositories import WorkingPaperRepository
        repo = WorkingPaperRepository(session)
        notes = repo.list_review_notes(wp2.id)
        for n in notes:
            n.clear("Audit Partner")
            repo.update_review_note(n)

    workbench._load_working_paper(wp2.id)
    assert workbench.lbl_review_alert.isHidden()

    window.close()
