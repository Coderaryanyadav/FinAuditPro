"""Unit tests for ReportLab PDF generation and draft watermarking."""

import os
from pathlib import Path

import pytest

from finauditpro.application.report_dtos import GenerateReportDTO
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.engagement_service import (
    CreateEngagementDTO,
    EngagementService,
)
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner


@pytest.fixture
def setup_pdf_env(tmp_path):
    db_file = tmp_path / "test_pdf_m7.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="PDF Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="PDF Client"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    report_svc = ReportService(db_manager)
    return eng, report_svc


def test_pdf_generation_header_and_watermark(setup_pdf_env) -> None:
    """Verify ReportLab renders valid openable %PDF file bytes and draft watermark."""
    eng, report_svc = setup_pdf_env

    tpls = report_svc.list_templates()
    report = report_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng.id,
            template_id=tpls[0].id,
            title="PDF Watermark Test Report",
            generated_by="Auditor",
        )
    )

    pdf_path = (
        Path(str(report_svc.db_manager.engine.url.database)).parent
        / "reports"
        / eng.id
        / f"report_{report.id}.pdf"
    )
    assert os.path.exists(pdf_path)

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Verify standard PDF magic header
    assert pdf_bytes.startswith(b"%PDF")

    # Verify DRAFT watermark using pymupdf or pypdf reader
    try:
        import pymupdf

        doc = pymupdf.open(pdf_path)
        extracted = "".join(page.get_text() for page in doc)
    except ImportError:
        from pypdf import PdfReader

        reader = PdfReader(pdf_path)
        extracted = "".join(page.extract_text() for page in reader.pages)
    assert "DRAFT" in extracted
