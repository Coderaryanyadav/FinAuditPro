"""Unit and integration tests for WorkCenterService."""

import uuid

import pytest

from finauditpro.application.dtos_work import WorkCenterFilterDTO
from finauditpro.application.services.work_center_service import WorkCenterService
from finauditpro.infrastructure.first_run import get_all_migrations
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.models import ClientModel, EngagementModel, FirmModel


@pytest.fixture
def db_mgr(tmp_path):
    db_file = tmp_path / "test_work_center.db"
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seed_data(db_mgr):
    firm_id = str(uuid.uuid4())
    client_id = str(uuid.uuid4())
    eng_id = str(uuid.uuid4())
    with db_mgr.session_scope() as session:
        f = FirmModel(id=firm_id, name="Test Firm")
        c = ClientModel(id=client_id, firm_id=firm_id, name="Apex Holdings", entity_type="COMPANY")
        e = EngagementModel(id=eng_id, firm_id=firm_id, client_id=client_id, financial_year="2024-25", audit_type="STATUTORY")
        session.add_all([f, c, e])
    return {"firm_id": firm_id, "client_id": client_id, "engagement_id": eng_id}


def test_create_manual_and_ai_tasks(db_mgr, seed_data):
    service = WorkCenterService(db_mgr)
    cid = seed_data["client_id"]
    eid = seed_data["engagement_id"]

    # Manual task creation
    manual_task = service.create_task(
        title="Verify Bank Balances",
        description="Reconcile SBI account",
        client_id=cid,
        engagement_id=eid,
        assignee="Senior Auditor",
        priority="HIGH",
        source="MANUAL",
    )
    assert manual_task.title == "Verify Bank Balances"
    assert manual_task.is_confirmed is True
    assert manual_task.requires_human_confirmation is False

    # AI Suggestion task creation
    ai_task = service.create_task(
        title="Investigate Large Cash Discrepancy",
        description="Detected 5L INR anomaly",
        client_id=cid,
        engagement_id=eid,
        assignee="Audit Team",
        priority="URGENT",
        source="AI_SUGGESTION",
    )
    assert ai_task.title == "Investigate Large Cash Discrepancy"
    assert ai_task.is_confirmed is False
    assert ai_task.requires_human_confirmation is True


def test_human_confirmation_of_ai_suggestion(db_mgr, seed_data):
    service = WorkCenterService(db_mgr)
    ai_task = service.create_task(
        title="Review Unmapped Ledger Code",
        source="AI_SUGGESTION",
        status="WAITING_REVIEW",
    )
    assert ai_task.is_confirmed is False

    confirmed = service.confirm_ai_suggestion(ai_task.id)
    assert confirmed is not None
    assert confirmed.is_confirmed is True
    assert confirmed.status == "TODO"
    assert confirmed.requires_human_confirmation is False


def test_task_quick_actions(db_mgr, seed_data):
    service = WorkCenterService(db_mgr)
    task = service.create_task(title="Sample Audit Task", assignee="Junior 1")

    # Update status
    updated = service.update_task_status(task.id, "COMPLETED")
    assert updated.status == "COMPLETED"

    # Reassign
    reassigned = service.assign_task(task.id, "Partner Lead")
    assert reassigned.assignee == "Partner Lead"

    # Postpone
    postponed = service.postpone_task(task.id, "2026-10-15")
    assert postponed.due_at == "2026-10-15"


def test_work_center_filtering_and_summary(db_mgr, seed_data):
    service = WorkCenterService(db_mgr)
    cid = seed_data["client_id"]

    service.create_task(title="T1", client_id=cid, status="TODO", priority="HIGH")
    service.create_task(title="T2", client_id=cid, status="IN_PROGRESS", priority="LOW")
    service.create_task(title="AI Task", client_id=cid, source="AI_SUGGESTION")

    summary = service.get_summary(client_id=cid)
    assert summary.total_tasks == 3
    assert summary.todo_count == 2
    assert summary.in_progress_count == 1
    assert summary.ai_suggestions_pending_confirmation == 1

    filtered = service.get_work_items(WorkCenterFilterDTO(section="Tasks", priority="HIGH"))
    assert len(filtered) == 1
    assert filtered[0].title == "T1"


def test_get_open_source_info(db_mgr, seed_data):
    service = WorkCenterService(db_mgr)
    task = service.create_task(title="Linked Finding Task", linked_finding="find_123")

    info = service.get_open_source_info(task.id)
    assert info["id"] == task.id
    assert info["linked_finding"] == "find_123"
