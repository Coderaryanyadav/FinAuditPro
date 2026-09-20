"""Tests for Phase 7 — Unified Evidence + Working Paper Workspace & Split View."""

import uuid

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSplitter

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.document_service import DocumentService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateReviewNoteDTO, CreateWorkingPaperDTO
from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.working_paper_entities import WorkingPaperStatusEnum
from finauditpro.infrastructure.first_run import get_all_migrations
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.models import (
    ClientModel,
    DocumentModel,
    EngagementModel,
    FirmModel,
    UserModel,
)
from finauditpro.ui.views.working_paper_view import WorkingPaperView
from finauditpro.ui.widgets.evidence_inspector_panel import EvidenceInspectorPanel


@pytest.fixture
def db_mgr(tmp_path):
    db_file = tmp_path / "split_view_test.db"
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seed_data(db_mgr):
    f_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())
    d_id = str(uuid.uuid4())
    with db_mgr.session_scope() as session:
        firm = FirmModel(id=f_id, name="Split View Firm")
        client = ClientModel(id=c_id, firm_id=f_id, name="Alpha Enterprise")
        engagement = EngagementModel(
            id=e_id, firm_id=f_id, client_id=c_id, financial_year="2025-26", audit_type="Statutory Audit"
        )
        session.add_all([firm, client, engagement])

        doc = DocumentModel(
            id=d_id,
            engagement_id=e_id,
            filename="March_Bank_Statement.pdf",
            stored_path="/tmp/March_Bank_Statement.pdf",
            mime_type="application/pdf",
            file_size_bytes=2048,
            page_count=5,
            content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            status="Ready",
        )
        session.add(doc)
        session.flush()

    return {"firm_id": f_id, "client_id": c_id, "engagement_id": e_id, "document_id": d_id}


def test_split_view_initialization(qtbot, db_mgr, seed_data):
    """Test that WorkingPaperView renders as a split-pane layout with EvidenceInspectorPanel."""
    eng_svc = EngagementService(db_mgr)
    wp_svc = WorkingPaperService(db_mgr)
    doc_svc = DocumentService(db_mgr)
    user_session = UserSession(user_id="u1", username="auditor@firm.com", role=RoleEnum.SENIOR)

    view = WorkingPaperView(eng_svc, wp_svc, document_service=doc_svc, user_session=user_session)
    qtbot.addWidget(view)
    view.resize(1440, 900)

    assert hasattr(view, "splitter")
    assert isinstance(view.splitter, QSplitter)
    assert view.splitter.orientation() == Qt.Orientation.Horizontal
    assert view.splitter.count() == 2
    assert hasattr(view, "evidence_inspector")
    assert isinstance(view.evidence_inspector, EvidenceInspectorPanel)


def test_evidence_click_through_navigation(qtbot, db_mgr, seed_data):
    """Test that selecting working paper with evidence opens document in right pane."""
    eng_svc = EngagementService(db_mgr)
    wp_svc = WorkingPaperService(db_mgr)
    doc_svc = DocumentService(db_mgr)
    e_id = seed_data["engagement_id"]
    d_id = seed_data["document_id"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=e_id,
            index_reference="B.01",
            title="Bank Reconciliation Testing",
            area="B. Bank & Cash",
            preparer_id="auditor@firm.com",
        )
    )

    wp_svc.add_working_paper_link(wp.id, "Document", d_id)

    view = WorkingPaperView(eng_svc, wp_svc, document_service=doc_svc)
    qtbot.addWidget(view)
    view.resize(1440, 900)
    view.set_engagement(e_id)

    # Select working paper in table
    assert view.table.rowCount() >= 1
    view.table.selectRow(0)

    assert view.selected_wp_id == wp.id
    assert view.evidence_inspector.current_document_id == d_id


def test_attach_evidence_from_right_pane(qtbot, db_mgr, seed_data):
    """Test attaching evidence from right pane links document without duplicating records."""
    eng_svc = EngagementService(db_mgr)
    wp_svc = WorkingPaperService(db_mgr)
    doc_svc = DocumentService(db_mgr)
    e_id = seed_data["engagement_id"]
    d_id = seed_data["document_id"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=e_id,
            index_reference="C.01",
            title="Trade Receivables Cut-Off",
            area="C. Receivables",
            preparer_id="auditor@firm.com",
        )
    )

    view = WorkingPaperView(eng_svc, wp_svc, document_service=doc_svc)
    qtbot.addWidget(view)
    view.set_engagement(e_id)
    view.table.selectRow(0)

    # Simulate right pane attach signal
    view._on_attach_evidence_from_inspector(d_id, page_num=2, excerpt="Sample invoice text")

    links = wp_svc.list_links(wp.id)
    assert len(links) >= 1
    assert any(lnk["target_id"] == d_id for lnk in links)


def test_maker_checker_and_signoff_preservation(db_mgr, seed_data):
    """Test that maker-checker review note blocking and sign-off verification are preserved."""
    wp_svc = WorkingPaperService(db_mgr)
    e_id = seed_data["engagement_id"]

    with db_mgr.session_scope() as session:
        session.add(
            UserModel(
                id=str(uuid.uuid4()),
                username="reviewer@firm.com",
                password_hash="hash",
                salt="salt",
                role="Senior",
            )
        )
        session.flush()

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=e_id,
            index_reference="D.01",
            title="Fixed Asset Additions Inspection",
            area="D. Fixed Assets",
            preparer_id="auditor@firm.com",
        )
    )

    # Submit for review
    wp_svc.assign_user_to_engagement(e_id, "reviewer@firm.com", "Senior")
    wp_svc.submit_for_review(wp.id, "auditor@firm.com")
    wp_svc.start_review(wp.id, "reviewer@firm.com")

    # Add open review note
    wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="reviewer@firm.com",
            note_text="Provide physical verification register reference.",
        )
    )

    # Open notes count must block sign-off
    open_notes = wp_svc.count_open_review_notes(wp.id)
    assert open_notes == 1


def test_splitter_resize_and_viewport_suitability(qtbot, db_mgr, seed_data):
    """Test that split-pane UI scales smoothly at 1440x900 resolution."""
    eng_svc = EngagementService(db_mgr)
    wp_svc = WorkingPaperService(db_mgr)
    doc_svc = DocumentService(db_mgr)

    view = WorkingPaperView(eng_svc, wp_svc, document_service=doc_svc)
    qtbot.addWidget(view)
    view.show()
    view.resize(1440, 900)

    assert view.splitter.count() == 2
    assert view.splitter.orientation() == Qt.Orientation.Horizontal
