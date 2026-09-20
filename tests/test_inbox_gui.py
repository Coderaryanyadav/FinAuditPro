"""Automated PySide6 GUI tests for the Practice Inbox View (InboxView)."""

import sys

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.inbox_service import InboxService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.inbox_view import InboxView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_inbox_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_inbox_view_rendering_and_tabs(
    qapp: QApplication, db_manager: DatabaseManager
) -> None:
    """Test InboxView renders filter tabs and handles tab switching."""
    inbox_svc = InboxService(db_manager)

    view = InboxView(inbox_svc)
    view.show()

    assert view.isVisible()
    assert "ALL" in view.tab_buttons
    assert "NEEDS_REVIEW" in view.tab_buttons
    assert "DOCUMENTS" in view.tab_buttons
    assert "REQUESTS" in view.tab_buttons
    assert "AI_SUGGESTIONS" in view.tab_buttons

    # Switch tab to Needs Review
    view._on_tab_changed("NEEDS_REVIEW")
    assert view.current_tab == "NEEDS_REVIEW"

    # Switch tab to AI Suggestions
    view._on_tab_changed("AI_SUGGESTIONS")
    assert view.current_tab == "AI_SUGGESTIONS"

    view.close()


@pytest.mark.gui
def test_inbox_view_populated_data_and_actions(
    qapp: QApplication, db_manager: DatabaseManager, monkeypatch, tmp_path
) -> None:
    """Test InboxView renders intake rows and triggers human approval action without blocking on dialogs."""
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.Ok)

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    doc_svc = DocumentService(db_manager)
    inbox_svc = InboxService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI Inbox Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Inbox Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    sample_file = tmp_path / "Audit_Trial_Balance.pdf"
    sample_file.write_bytes(b"%PDF-1.5 Trial Balance Content")

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng.id, file_path=str(sample_file))
    )

    view = InboxView(inbox_svc)
    view.show()

    assert view.table_inbox.rowCount() >= 1

    # Simulate accept click on first row document item
    view._on_accept_clicked(doc.id)

    # Verify table refreshes
    assert view.table_inbox.rowCount() >= 1

    view.close()
