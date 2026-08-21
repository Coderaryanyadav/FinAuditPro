"""GUI unit tests for Document Workspace PySide6 components."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.document_dtos import UploadDocumentDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.document_view import DocumentView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_doc_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_document_view_rendering(qapp: QApplication, db_manager: DatabaseManager, tmp_path) -> None:
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    doc_svc = DocumentService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI Doc Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI Doc Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    doc_file = tmp_path / "gui_test_doc.txt"
    doc_file.write_text("Sample Audit Doc Content for GUI Test", encoding="utf-8")
    doc_svc.upload_and_process_document(UploadDocumentDTO(engagement_id=eng.id, file_path=str(doc_file)))

    doc_view = DocumentView(doc_svc)
    doc_view.set_engagement(eng.id)

    assert doc_view.table.rowCount() == 1
    assert doc_view.upload_btn.isEnabled()
