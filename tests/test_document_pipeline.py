"""Integration tests for document processing pipeline and text extraction."""

from pathlib import Path

from finauditpro.domain.document_entities import DocumentCategoryEnum
from finauditpro.infrastructure.documents.document_pipeline import DocumentPipeline


def test_document_pipeline_text_file(tmp_path) -> None:
    storage_dir = tmp_path / "doc_storage"
    pipeline = DocumentPipeline(storage_dir=storage_dir)

    source_file = tmp_path / "sample_board_minutes.txt"
    source_file.write_text(
        "Board of Directors Meeting Minutes\nCompany: ABC Pvt Ltd\nResolution: Approved FY 2025-26 Financial Statements.",
        encoding="utf-8",
    )

    res = pipeline.process_incoming_file(
        engagement_id="eng-101",
        source_path=source_file,
        category=DocumentCategoryEnum.BOARD_MINUTES,
    )

    assert res.filename == "sample_board_minutes.txt"
    assert len(res.content_hash) == 64
    assert res.page_count == 1
    assert "Approved FY 2025-26" in res.pages[0].text
    assert Path(res.stored_path).exists()


def test_document_pipeline_csv_file(tmp_path) -> None:
    storage_dir = tmp_path / "doc_storage"
    pipeline = DocumentPipeline(storage_dir=storage_dir)

    source_file = tmp_path / "bank_statement.csv"
    source_file.write_text(
        "Date,Transaction ID,Description,Debit,Credit,Balance\n2026-04-01,TXN001,Vendor Payment,50000,,450000\n",
        encoding="utf-8",
    )

    res = pipeline.process_incoming_file(
        engagement_id="eng-102",
        source_path=source_file,
        category=DocumentCategoryEnum.BANK_STATEMENT,
    )

    assert res.page_count == 1
    assert "Vendor Payment" in res.pages[0].text
    assert "TXN001" in res.pages[0].text
