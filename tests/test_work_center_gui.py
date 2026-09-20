"""GUI unit tests for WorkCenterView PySide6 interface."""

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.application.services.work_center_service import WorkCenterService
from finauditpro.infrastructure.first_run import get_all_migrations
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.ui.views.work_center_view import WorkCenterView


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def db_mgr(tmp_path):
    db_file = tmp_path / "gui_work_center.db"
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


def test_work_center_view_initialization_and_quick_actions(qapp, db_mgr):
    service = WorkCenterService(db_mgr)

    # Seed data
    t1 = service.create_task(title="Sample Manual Task", priority="HIGH")
    t2 = service.create_task(title="AI Suggested Task", source="AI_SUGGESTION")

    clients = [{"id": "c1", "name": "Global Corp"}]
    view = WorkCenterView(service, clients=clients)

    assert view.card_total.value_lbl.text() == "2"
    assert view.card_ai_suggestions.value_lbl.text() == "1"

    # Test Section switching
    view._select_section("Compliance")
    assert view.current_section == "Compliance"

    view._select_section("Tasks")
    assert view.current_section == "Tasks"

    # Test complete quick action
    view._on_complete_task(t1.id)
    items = service.get_work_items()
    completed_items = [i for i in items if i.id == t1.id]
    assert completed_items[0].status == "COMPLETED"

    # Test AI confirm quick action
    view._on_confirm_ai_task(t2.id)
    ai_items = [i for i in service.get_work_items() if i.id == t2.id]
    assert ai_items[0].is_confirmed is True
