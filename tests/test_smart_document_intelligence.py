"""Comprehensive unit & integration tests for Phase 9 — Smart Document Intelligence."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from finauditpro.application.document_dtos import UploadDocumentDTO
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.document_entities import (
    DocumentCategoryEnum,
    DocumentStatusEnum,
    MetadataFieldStatusEnum,
    MetadataSourceEnum,
)
from finauditpro.infrastructure.documents.document_pipeline import DocumentPipeline
from finauditpro.infrastructure.documents.document_security import DocumentSecurityError
from finauditpro.infrastructure.documents.smart_document_intelligence import (
    confirm_human_metadata,
    extract_deterministic_metadata,
    merge_metadata_with_provenance,
    process_smart_document_classification_and_metadata,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_smart_doc.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Smart Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Acme Enterprises Pvt Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2023-24")
    )

    doc_pipeline = DocumentPipeline(storage_dir=tmp_path / "storage")
    doc_svc = DocumentService(manager, pipeline=doc_pipeline)

    return manager, eng, client, doc_svc


def test_metadata_extraction_and_provenance(tmp_path):
    """Test deterministic metadata extraction across structured fields."""
    sample_text = """
    TAX INVOICE
    Vendor: SupplyCo Pvt Ltd
    Client: Acme Enterprises Pvt Ltd
    Invoice No: INV-2024-9988
    Date: 31/03/2024
    Period: Q4 FY 2023-24
    Financial Year: FY 2023-24
    GSTIN: 27AAACB1234C1ZV
    Total Amount: INR 1,50,000.00
    """
    meta = extract_deterministic_metadata(
        text=sample_text,
        filename="invoice_march.pdf",
        client_name="Acme Enterprises Pvt Ltd",
        active_fy="FY 2023-24",
        category=DocumentCategoryEnum.INVOICE,
        category_confidence=0.95,
    )

    assert meta.document_type.value == DocumentCategoryEnum.INVOICE.value
    assert meta.document_type.status == MetadataFieldStatusEnum.PENDING_REVIEW
    assert meta.document_type.source == MetadataSourceEnum.DETERMINISTIC

    assert meta.client.value == "Acme Enterprises Pvt Ltd"
    assert meta.fy.value == "FY 2023-24"
    assert meta.reference_number.value == "INV-2024-9988"
    assert meta.financial_amount.value == 150000.00
    assert "27AAACB1234C1ZV" in str(meta.tax_identifiers.value)


def test_human_override_and_no_ai_overwrite():
    """Test that human confirmed fields receive HUMAN source/CONFIRMED status and are never silently overwritten."""
    initial_meta = extract_deterministic_metadata(
        text="Invoice Amount INR 1000",
        filename="inv.pdf",
        category=DocumentCategoryEnum.INVOICE,
    )

    # Auditor confirms/overrides reference_number and financial_amount
    overrides = {
        "reference_number": "REF-CONFIRMED-123",
        "financial_amount": 250000.00,
    }
    confirmed_meta = confirm_human_metadata(initial_meta, overrides)

    assert confirmed_meta.reference_number.value == "REF-CONFIRMED-123"
    assert confirmed_meta.reference_number.source == MetadataSourceEnum.HUMAN
    assert confirmed_meta.reference_number.status == MetadataFieldStatusEnum.CONFIRMED

    # Run new AI extraction attempt
    new_extracted = extract_deterministic_metadata(
        text="Invoice Amount INR 99999 Invoice No: OVERWRITE_ME",
        filename="inv.pdf",
        category=DocumentCategoryEnum.INVOICE,
    )
    new_extracted.reference_number.value = "OVERWRITE_ME"
    new_extracted.reference_number.source = MetadataSourceEnum.AI

    # Merge newly extracted metadata with confirmed metadata
    merged = merge_metadata_with_provenance(new_extracted, confirmed_meta)

    # Human confirmed value MUST BE PRESERVED
    assert merged.reference_number.value == "REF-CONFIRMED-123"
    assert merged.reference_number.source == MetadataSourceEnum.HUMAN
    assert merged.reference_number.status == MetadataFieldStatusEnum.CONFIRMED
    assert merged.financial_amount.value == 250000.00


def test_uncertain_classification_ai_fallback_and_ai_unavailable():
    """Test AI classification fallback when uncertain, and resilient handling when AI is unavailable."""
    ambiguous_text = "General note without standard accounting keywords."

    # 1. AI available
    mock_ai = MagicMock()
    mock_ai.classify_document.return_value = (DocumentCategoryEnum.CONTRACT, 0.92, ["AI Contract Terms"])

    cat, conf, ev, meta = process_smart_document_classification_and_metadata(
        text=ambiguous_text,
        filename="agreement_draft.docx",
        category_hint=DocumentCategoryEnum.GENERAL,
        ai_service=mock_ai,
    )
    assert cat == DocumentCategoryEnum.CONTRACT
    assert conf >= 0.88
    assert meta.document_type.source == MetadataSourceEnum.AI

    # 2. AI unavailable / throwing exception
    failing_ai = MagicMock()
    failing_ai.classify_document.side_effect = RuntimeError("Local LLM Offline")

    cat2, conf2, _ev2, meta2 = process_smart_document_classification_and_metadata(
        text=ambiguous_text,
        filename="agreement_draft.docx",
        category_hint=DocumentCategoryEnum.GENERAL,
        ai_service=failing_ai,
    )
    # Graceful fallback without crashing
    assert cat2 == DocumentCategoryEnum.GENERAL
    assert conf2 == 0.50
    assert meta2.document_type.status == MetadataFieldStatusEnum.PENDING_REVIEW


def test_duplicate_file_deduplication(setup_services, tmp_path):
    """Test SHA-256 deduplication check returning existing document without duplicating storage."""
    _manager, eng, _client, doc_svc = setup_services

    file_path = tmp_path / "bank_stmt.csv"
    file_path.write_text("Date,Description,Amount\n2024-03-01,Opening Balance,500000\n", encoding="utf-8")

    dto1 = UploadDocumentDTO(engagement_id=eng.id, file_path=str(file_path), category=DocumentCategoryEnum.BANK_STATEMENT)
    doc1 = doc_svc.upload_and_process_document(dto1)

    dto2 = UploadDocumentDTO(engagement_id=eng.id, file_path=str(file_path), category=DocumentCategoryEnum.BANK_STATEMENT)
    doc2 = doc_svc.upload_and_process_document(dto2)

    assert doc1.id == doc2.id
    assert doc1.content_hash == doc2.content_hash

    # Confirm only 1 document persisted for engagement
    docs = doc_svc.list_documents_for_engagement(eng.id)
    assert len(docs) == 1


def test_malformed_file_quarantine(tmp_path):
    """Test pipeline handling of empty or corrupt file upload."""
    pipeline = DocumentPipeline(storage_dir=tmp_path / "storage")
    empty_file = tmp_path / "empty_corrupt.pdf"
    empty_file.write_bytes(b"")

    res = pipeline.process_incoming_file(
        engagement_id="eng-test",
        source_path=empty_file,
    )
    assert res.status == DocumentStatusEnum.QUARANTINED
    assert res.failed_stage == "VALIDATING"


def test_wrong_extension_validation_error(tmp_path):
    """Test security validation error when file extension/header mismatch."""
    from finauditpro.infrastructure.documents.document_security import validate_document_security

    exe_disguised = tmp_path / "fake_doc.pdf"
    exe_disguised.write_bytes(b"\x7fELF\x01\x01\x01\x00executable_binary_header")

    with pytest.raises(DocumentSecurityError):
        validate_document_security(exe_disguised)


def test_ocr_text_extraction(tmp_path):
    """Test OCR fallback for image files or text-sparse documents."""
    pipeline = DocumentPipeline(storage_dir=tmp_path / "storage")

    # Plain text simulating OCR output
    txt_file = tmp_path / "scanned_receipt.txt"
    txt_file.write_text("SCANNED RECEIPT\nVendor: OfficeSupplies Ltd\nTotal: INR 4500", encoding="utf-8")

    res = pipeline.process_incoming_file(
        engagement_id="eng-test-ocr",
        source_path=txt_file,
        category=DocumentCategoryEnum.INVOICE,
    )
    assert res.status == DocumentStatusEnum.READY
    assert "OfficeSupplies Ltd" in res.pages[0].extracted_text


def test_document_metadata_persistence_and_confirmation(setup_services, tmp_path):
    """Test full integration: document upload, metadata persistence in DB, and auditor confirmation."""
    _manager, eng, _client, doc_svc = setup_services

    invoice_file = tmp_path / "march_tax_invoice.txt"
    invoice_file.write_text(
        "TAX INVOICE\nVendor: TechSupply Pvt Ltd\nInvoice No: INV-2024-5544\nDate: 2024-03-31\nTotal Amount: INR 75,000.00\nGSTIN: 27AAACB1234C1ZV",
        encoding="utf-8",
    )

    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng.id, file_path=str(invoice_file), category=DocumentCategoryEnum.INVOICE)
    )

    details = doc_svc.get_document_details(doc.id)
    meta = details.document.extracted_metadata
    assert meta is not None
    assert meta.reference_number.value == "INV-2024-5544"
    assert meta.reference_number.status == MetadataFieldStatusEnum.PENDING_REVIEW

    # Auditor confirms metadata
    updated_doc = doc_svc.confirm_document_metadata(
        doc.id,
        {
            "reference_number": "INV-2024-5544-CONFIRMED",
            "vendor_customer": "TechSupply Pvt Ltd",
        },
    )

    assert updated_doc.extracted_metadata.reference_number.value == "INV-2024-5544-CONFIRMED"
    assert updated_doc.extracted_metadata.reference_number.source == MetadataSourceEnum.HUMAN
    assert updated_doc.extracted_metadata.reference_number.status == MetadataFieldStatusEnum.CONFIRMED
