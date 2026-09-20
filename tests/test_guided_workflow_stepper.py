"""Tests for Phase 8 — Guided Audit Engagement Workflow Pipeline & Navigation Stepper."""

import uuid

import pytest
from PySide6.QtCore import Qt

from finauditpro.application.services.guided_workflow_service import GuidedWorkflowService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateReviewNoteDTO, CreateWorkingPaperDTO
from finauditpro.infrastructure.first_run import get_all_migrations
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.models import ClientModel, EngagementModel, FirmModel
from finauditpro.ui.views.guided_workflow_view import GuidedWorkflowView


@pytest.fixture
def db_mgr(tmp_path):
    db_file = tmp_path / "guided_workflow_test.db"
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seed_engagement(db_mgr):
    f_id = str(uuid.uuid4())
    c_id = str(uuid.uuid4())
    e_id = str(uuid.uuid4())
    with db_mgr.session_scope() as session:
        firm = FirmModel(id=f_id, name="Apex Chartered Accountants")
        client = ClientModel(id=c_id, firm_id=f_id, name="Zenith Technologies Pvt Ltd")
        engagement = EngagementModel(
            id=e_id,
            firm_id=f_id,
            client_id=c_id,
            financial_year="2025-26",
            audit_type="Statutory Audit",
        )
        session.add_all([firm, client, engagement])
        session.flush()

    return {"firm_id": f_id, "client_id": c_id, "engagement_id": e_id}


def test_factual_workflow_evaluation_empty_engagement(db_mgr, seed_engagement):
    """Test factual status evaluation for a new engagement without fabrication."""
    service = GuidedWorkflowService(db_mgr)
    e_id = seed_engagement["engagement_id"]

    workflow = service.evaluate_workflow(e_id)
    assert workflow.firm_name == "Apex Chartered Accountants"
    assert workflow.client_name == "Zenith Technologies Pvt Ltd"
    assert workflow.financial_year == "2025-26"
    assert len(workflow.stages) == 4

    # Stage 1: Setup & Planning
    st1 = workflow.stages[0]
    reasons1 = st1.incomplete_reasons
    assert "Materiality not finalized" in reasons1
    assert "Audit risks not identified" in reasons1

    # Stage 2: Financial Data
    st2 = workflow.stages[1]
    assert "Trial balance not imported / imbalanced" in st2.incomplete_reasons

    # Stage 3: Fieldwork & Evidence
    st3 = workflow.stages[2]
    assert "No working papers generated" in st3.incomplete_reasons

    # Stage 4: Review & Reporting
    st4 = workflow.stages[3]
    assert "Report not generated" in st4.incomplete_reasons


def test_factual_workflow_evaluation_in_progress(db_mgr, seed_engagement):
    """Test that actual progress and incomplete reasons update dynamically from database state."""
    wp_svc = WorkingPaperService(db_mgr)
    guided_svc = GuidedWorkflowService(db_mgr)
    e_id = seed_engagement["engagement_id"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=e_id,
            index_reference="A.01",
            title="Statutory Compliance Schedule",
            area="A. General",
            preparer_id="auditor@firm.com",
        )
    )

    wp_svc.raise_review_note(
        CreateReviewNoteDTO(
            working_paper_id=wp.id,
            raised_by="manager@firm.com",
            note_text="Check Form 3CD tax audit report attachment.",
        )
    )

    workflow = guided_svc.evaluate_workflow(e_id)
    st3 = workflow.stages[2]
    reasons3 = st3.incomplete_reasons

    assert any("1 working papers awaiting review" in r for r in reasons3)
    assert any("1 open review notes" in r for r in reasons3)


def test_guided_workflow_ui_and_navigation(qtbot, db_mgr, seed_engagement):
    """Test UI rendering, stepper stages, and route navigation signals."""
    e_id = seed_engagement["engagement_id"]

    view = GuidedWorkflowView(db_mgr)
    qtbot.addWidget(view)
    view.set_engagement(e_id)

    assert "Apex Chartered Accountants" in view.lbl_firm.text()
    assert "Zenith Technologies Pvt Ltd" in view.lbl_client.text()
    assert "2025-26" in view.lbl_fy.text()

    # Verify 4 stepper buttons
    assert len(view.stage_buttons) == 4
    assert "1. Setup & Planning" in view.stage_buttons[0].text()
    assert "2. Financial Data" in view.stage_buttons[1].text()
    assert "3. Fieldwork & Evidence" in view.stage_buttons[2].text()
    assert "4. Review & Reporting" in view.stage_buttons[3].text()

    # Verify route signal emission
    route_emitted = []
    view.navigate_to_route.connect(lambda r: route_emitted.append(r))

    view._select_stage(0)
    assert view.steps_layout.count() > 0
