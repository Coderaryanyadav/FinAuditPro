"""Security Regression Test Suite: Multi-Tenant Client & Engagement Isolation.

Verifies strict tenant boundary enforcement across documents, PBC requests, financial datasets,
and AI vector store RAG retrieval to prevent cross-client data leakage.
"""

import pytest

from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.financial_dtos import ImportDatasetDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
from finauditpro.application.services.document_service import DocumentService, UploadDocumentDTO
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.financial_data_service import FinancialDataService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.infrastructure.ai.rag_pipeline import DocumentChunk, LocalVectorStore
from finauditpro.infrastructure.persistence.database import DatabaseManager


def test_client_isolation_documents(tmp_path) -> None:
    """Verify Client A cannot access Client B's uploaded evidence documents."""
    db_path = tmp_path / "test_iso_docs.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    doc_svc = DocumentService(db_manager)
    workspace_svc = ClientWorkspaceService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Security CA Firm"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client A Corp"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client B Inc"))

    eng_a = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26"))
    eng_b = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26"))

    # Upload document for Client A
    file_a = tmp_path / "Client_A_Confidential_Bank.pdf"
    file_a.write_bytes(b"%PDF-1.5 Confidential Client A Bank Data")
    doc_a = doc_svc.upload_and_process_document(UploadDocumentDTO(engagement_id=eng_a.id, file_path=str(file_a)))

    # Upload document for Client B
    file_b = tmp_path / "Client_B_Tax_Return.pdf"
    file_b.write_bytes(b"%PDF-1.5 Confidential Client B Tax Data")
    doc_b = doc_svc.upload_and_process_document(UploadDocumentDTO(engagement_id=eng_b.id, file_path=str(file_b)))

    # Query Client A workspace summary
    sum_a = workspace_svc.get_client_workspace_summary(client_a.id)
    assert sum_a.total_documents == 1

    # Query Client B workspace summary
    sum_b = workspace_svc.get_client_workspace_summary(client_b.id)
    assert sum_b.total_documents == 1

    # Verify document listing for Client A does not contain Client B's document
    docs_a = doc_svc.list_documents_for_engagement(eng_a.id)
    doc_ids_a = [d.id for d in docs_a]
    assert doc_a.id in doc_ids_a
    assert doc_b.id not in doc_ids_a


def test_client_isolation_financial_data(tmp_path) -> None:
    """Verify Client A cannot query or view Client B's imported financial datasets."""
    db_path = tmp_path / "test_iso_fin.db"
    db_manager = DatabaseManager(db_path=db_path)
    db_manager.create_tables()

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    fin_svc = FinancialDataService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Fin Security Firm"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta"))

    eng_a = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26"))
    eng_b = eng_svc.create_engagement(CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26"))

    # Create CSV file for Client A
    csv_a = tmp_path / "client_a_tb.csv"
    csv_a.write_text("AccountCode,AccountName,Debit,Credit\n1001,Alpha Cash,50000,0\n")

    # Create CSV file for Client B
    csv_b = tmp_path / "client_b_tb.csv"
    csv_b.write_text("AccountCode,AccountName,Debit,Credit\n2001,Beta Loan,0,90000\n")

    # Import datasets
    ds_a = fin_svc.import_financial_dataset(ImportDatasetDTO(engagement_id=eng_a.id, dataset_name="Client A TB", file_path=str(csv_a)))
    ds_b = fin_svc.import_financial_dataset(ImportDatasetDTO(engagement_id=eng_b.id, dataset_name="Client B TB", file_path=str(csv_b)))

    # Query datasets for Client A
    datasets_a = fin_svc.list_datasets_for_engagement(eng_a.id)
    ds_ids_a = [d.id for d in datasets_a]
    assert ds_a.id in ds_ids_a
    assert ds_b.id not in ds_ids_a

    # Query datasets for Client B
    datasets_b = fin_svc.list_datasets_for_engagement(eng_b.id)
    ds_ids_b = [d.id for d in datasets_b]
    assert ds_b.id in ds_ids_b
    assert ds_a.id not in ds_ids_b


def test_ai_vector_rag_isolation() -> None:
    """Verify AI vector store search enforces strict engagement/client vector chunk scoping."""
    vector_store = LocalVectorStore()

    # Add chunk for Engagement A (Client A)
    chunk_a = DocumentChunk(
        chunk_id="chk_a",
        engagement_id="eng_client_a",
        document_id="doc_a",
        filename="Bank_A.pdf",
        category="Bank Statement",
        page_number=1,
        chunk_index=0,
        text="Client A Confidential Revenue: INR 500 Crores",
        embedding=[0.9, 0.1, 0.0],
    )

    # Add chunk for Engagement B (Client B)
    chunk_b = DocumentChunk(
        chunk_id="chk_b",
        engagement_id="eng_client_b",
        document_id="doc_b",
        filename="Tax_B.pdf",
        category="Tax Return",
        page_number=1,
        chunk_index=0,
        text="Client B Confidential Expense: INR 200 Crores",
        embedding=[0.9, 0.1, 0.0],
    )

    vector_store.add_chunks([chunk_a, chunk_b])

    # Search scoped strictly to Engagement A
    results_a = vector_store.search(engagement_id="eng_client_a", query_embedding=[0.9, 0.1, 0.0], top_k=5)
    chunks_a = [r[0] for r in results_a]

    assert len(chunks_a) == 1
    assert chunks_a[0].engagement_id == "eng_client_a"
    assert "Client A" in chunks_a[0].text

    # Search scoped strictly to Engagement B
    results_b = vector_store.search(engagement_id="eng_client_b", query_embedding=[0.9, 0.1, 0.0], top_k=5)
    chunks_b = [r[0] for r in results_b]

    assert len(chunks_b) == 1
    assert chunks_b[0].engagement_id == "eng_client_b"
    assert "Client B" in chunks_b[0].text
