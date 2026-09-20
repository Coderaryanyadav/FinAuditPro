"""Phase 15 — UX Polish & Desktop-Native Accessibility Test Suite."""

import pytest
from PySide6.QtWidgets import QApplication

from finauditpro.ui.dialogs.confirm_dialog import (
    confirm_destructive_action,
    show_actionable_error,
    show_success_feedback,
)
from finauditpro.ui.human_formatters import (
    format_client_display,
    format_document_display,
    format_engagement_display,
    format_finding_display,
    format_task_display,
)


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_human_friendly_formatters():
    eng_label = format_engagement_display("FY 2025-26", "Statutory Audit", "ABC Pvt Ltd")
    assert eng_label == "ABC Pvt Ltd — FY 2025-26 (Statutory Audit)"

    eng_short = format_engagement_display("FY 2025-26", "Statutory Audit")
    assert eng_short == "FY 2025-26 / Statutory Audit"

    cli_label = format_client_display("XYZ Ltd", "ABCDE1234F", "Private Limited")
    assert "XYZ Ltd" in cli_label
    assert "ABCDE1234F" in cli_label

    doc_label = format_document_display("Invoice_101.pdf", "Tax Invoice")
    assert doc_label == "[Tax Invoice] Invoice_101.pdf"

    task_label = format_task_display("Reconcile Bank Statement", "HIGH", "31 Mar")
    assert task_label == "[HIGH] Reconcile Bank Statement (Due: 31 Mar)"

    finding_label = format_finding_display("Revenue Cutoff Exception", "High", "Substantive")
    assert finding_label == "[HIGH] Revenue Cutoff Exception (Substantive)"


def test_confirm_dialogs_helpers(qapp):
    # Verify dialog construction without exception
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QDialog

    def auto_close():
        top = QApplication.activeModalWidget()
        if isinstance(top, QDialog):
            top.accept()

    QTimer.singleShot(50, auto_close)
    res = confirm_destructive_action(None, "Test Delete", "Are you sure?", "Delete")
    assert res is True or res is False


def test_actionable_error_and_success_dialogs(qapp):
    from PySide6.QtCore import QTimer
    from PySide6.QtWidgets import QDialog

    def auto_close():
        top = QApplication.activeModalWidget()
        if isinstance(top, QDialog):
            top.accept()

    QTimer.singleShot(50, auto_close)
    show_actionable_error(None, "Test Error", "Database timeout", "Retry connecting to SQLite database.")

    QTimer.singleShot(50, auto_close)
    show_success_feedback(None, "Operation Completed", "Client updated successfully.")
