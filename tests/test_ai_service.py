"""Integration tests for AIService and AI-assisted Finding proposals."""

import pytest

from finauditpro.application.ai.llm_provider import LLMResponse, ProviderStatus
from finauditpro.application.services.ai_service import AIService
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.domain.audit_matrix_entities import FindingSourceEnum, FindingStatusEnum
from finauditpro.infrastructure.ai.faiss_vector_store import FAISSVectorStore
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


class DummyLLMProvider:
    """Mock LLM Provider for unit tests."""

    def __init__(self) -> None:
        self.chat_model_id = "deepseek/deepseek-r1-distill-qwen-14b"
        self.embedding_model_id = "text-embedding-nomic-embed-text-v1.5"

    def available(self) -> ProviderStatus:
        return ProviderStatus(
            is_server_up=True,
            chat_model_loaded=True,
            embedding_model_loaded=True,
            chat_model_id=self.chat_model_id,
            embedding_model_id=self.embedding_model_id,
        )

    def chat(self, messages, schema_class=None, **kwargs) -> LLMResponse:
        if schema_class:
            content = (
                '{"title": "Unrecorded Revenue Exception", "description": "Cut-off exception on invoice #1002.", '
                '"severity": "High", "assertion": "Cut-Off", "affected_account": "Sales Revenue", '
                '"recommendation": "Post adjusting entry.", "cited_chunk_ids": ["fts_page1"]}'
            )
        else:
            content = "Payment terms are Net 30 days per [fts_page1]."
        return LLMResponse(content=content, reasoning_text="Reasoning logic...")

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]

    def list_models(self) -> list[str]:
        return [self.chat_model_id, self.embedding_model_id]


@pytest.fixture
def setup_ai_env(tmp_path):
    db_file = tmp_path / "test_ai_m5.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="AI Test Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="AI Test Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    vector_store = FAISSVectorStore(tmp_path / "ai_indices")
    provider = DummyLLMProvider()
    ai_svc = AIService(db_manager, provider, vector_store)

    return eng, ai_svc


def test_ai_finding_proposal_flow(setup_ai_env) -> None:
    """Verify AI proposal creation into M4 unified model with source='ai' and status='Open'."""
    eng, ai_svc = setup_ai_env

    finding = ai_svc.propose_finding(
        engagement_id=eng.id,
        target_context="Invoice #1002 revenue cut-off misstatement.",
    )

    assert finding.id is not None
    assert finding.title == "Unrecorded Revenue Exception"
    assert finding.source == FindingSourceEnum.AI
    assert finding.is_ai_generated is True
    assert finding.status == FindingStatusEnum.OPEN
