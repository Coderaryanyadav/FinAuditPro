"""GUI unit tests for AIAssistantView PySide6 components."""

import sys

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.ai_service import AIService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
from finauditpro.infrastructure.ai.lmstudio_provider import LMStudioProvider
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.ui.views.ai_assistant_view import AIAssistantView


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def db_manager(tmp_path) -> DatabaseManager:
    db_path = tmp_path / "test_ai_gui.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()
    return manager


@pytest.mark.gui
def test_ai_assistant_view_rendering(
    qapp: QApplication, db_manager: DatabaseManager, tmp_path
) -> None:
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    provider = LMStudioProvider()
    vector_store = FAISSVectorStore(tmp_path / "ai_indices")
    ai_svc = AIService(db_manager, provider=provider, vector_store=vector_store)

    firm = firm_svc.create_firm(CreateFirmDTO(name="GUI AI Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="GUI AI Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    view = AIAssistantView(eng_svc, ai_svc)
    view.set_engagement(eng.id)

    assert view.current_engagement is not None
    assert view.current_engagement.id == eng.id
