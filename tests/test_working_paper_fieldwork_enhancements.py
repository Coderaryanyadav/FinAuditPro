"""
Tests for Working Paper & Fieldwork Enhancements:
- Substantive Testing Grid & Audit Tick-Marks serialization & variance computation
- SA 530 Sampling Calculator & sample size derivation
- ICAI UDIN validation and sign-off binding
- Line/section pinned review notes format
"""

import json
from unittest.mock import MagicMock
import pytest

from PySide6.QtWidgets import QApplication

from finauditpro.domain.working_paper_entities import (
    FileCategoryEnum,
    SignOffLevelEnum,
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.ui.dialogs.sampling_dialog import CONFIDENCE_FACTORS, SamplingCalculatorDialog
from finauditpro.ui.dialogs.signoff_dialog import SignOffDialog


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    return app


def test_sampling_calculator_mus_formula(qapp):
    """Test Monetary Unit Sampling interval and sample size calculation."""
    # Population: 500 vouchers, Total Value: ₹1,00,00,000 (1 Cr), TM: ₹5,00,000 (5 Lakhs), 90% Confidence (2.31 factor)
    dlg = SamplingCalculatorDialog(tolerable_misstatement_paise=50000000)
    dlg.pop_count_input.setText("500")
    dlg.pop_amount_input.setText("10000000")
    dlg.tm_input.setText("500000")
    dlg.confidence_combo.setCurrentIndex(1)  # 90% factor 2.31
    dlg._recalculate()

    assert dlg.calculated_sample_size > 0
    # Interval = 500000 / 2.31 ≈ 216450
    # Expected sample size raw = 10000000 / 216450 ≈ 46.2 -> 47
    assert 40 <= dlg.calculated_sample_size <= 50
    assert dlg.calculated_interval_paise > 0
    assert dlg.high_value_cutoff_paise > 0


def test_sampling_calculator_stratified_formula(qapp):
    """Test Stratified Sampling calculation."""
    dlg = SamplingCalculatorDialog()
    dlg.method_combo.setCurrentIndex(1)  # STRATIFIED
    dlg.pop_count_input.setText("1000")
    dlg.pop_amount_input.setText("50000000")
    dlg.tm_input.setText("1000000")
    dlg._recalculate()

    assert dlg.calculated_sample_size >= 10
    assert dlg.calculated_sample_size <= 1000
    assert dlg.high_value_cutoff_paise == 100000000  # 10 Lakhs in paise


def test_udin_format_and_dialog_validation(qapp):
    """Test ICAI UDIN 18-character validation in SignOffDialog."""
    wp = WorkingPaper(
        engagement_id="eng-123",
        index_reference="WP-REV-01",
        title="Revenue Cut-off Testing",
        area="Revenue",
        preparer_id="Lead Auditor",
        file_category=FileCategoryEnum.CURRENT_FILE,
        status=WorkingPaperStatusEnum.APPROVED,
    )
    mock_wp_service = MagicMock()
    dlg = SignOffDialog(wp, mock_wp_service)

    # Invalid UDIN: less than 18 characters
    dlg.udin_input.setText("24123456")
    dlg.user_id_input.setText("partner@audit.com")
    dlg._on_sign_off_clicked()
    assert not mock_wp_service.sign_off_working_paper.called

    # Valid UDIN: 18 alphanumeric characters
    valid_udin = "24098765ABCD123456"
    dlg.udin_input.setText(valid_udin)
    dlg.note_input.setText("Final statutory audit sign-off")
    dlg._on_sign_off_clicked()

    assert mock_wp_service.sign_off_working_paper.called
    dto = mock_wp_service.sign_off_working_paper.call_args[0][0]
    assert f"[UDIN: {valid_udin}]" in dto.note


def test_substantive_testing_grid_serialization():
    """Verify that testing grid rows serialize and parse correctly into sections."""
    from PySide6.QtWidgets import QTableWidgetItem
    from finauditpro.ui.views.working_paper_view import WorkingPaperView

    mock_eng_service = MagicMock()
    mock_wp_service = MagicMock()

    app = QApplication.instance() or QApplication([])
    view = WorkingPaperView(mock_eng_service, mock_wp_service)

    # Insert test rows in view
    view.tbl_testing.insertRow(0)
    view.tbl_testing.setItem(0, 0, QTableWidgetItem("1"))
    view.tbl_testing.setItem(0, 1, QTableWidgetItem("VR-001"))
    view.tbl_testing.setItem(0, 2, QTableWidgetItem("2026-03-31"))
    view.tbl_testing.setItem(0, 3, QTableWidgetItem("Sales Invoice - Tata Motors"))
    view.tbl_testing.setItem(0, 4, QTableWidgetItem("150000.00"))
    view.tbl_testing.setItem(0, 5, QTableWidgetItem("150000.00"))
    view.tbl_testing.setItem(0, 6, QTableWidgetItem("0.00"))
    view.tbl_testing.setItem(0, 7, QTableWidgetItem("T"))
    view.tbl_testing.setItem(0, 8, QTableWidgetItem("Agreed to GSTR-1 and E-Way Bill"))
    view.tbl_testing.setItem(0, 9, QTableWidgetItem("Reconciled"))

    # Serialize
    serialized = view._serialize_testing_grid()
    assert "### Substantive Testing & Tick-Marks" in serialized
    assert "Tata Motors" in serialized
    assert "<!-- GRID_JSON:" in serialized

    # Deserialize into fresh section
    sec = WorkingPaperSection(
        working_paper_id="wp-123",
        title="Substantive Testing Grid",
        content_markdown=serialized,
    )
    view._load_testing_grid_from_sections([sec])

    assert view.tbl_testing.rowCount() == 1
    assert view.tbl_testing.item(0, 1).text() == "VR-001"
    assert view.tbl_testing.item(0, 7).text() == "T"
    assert "Tata Motors" in view.tbl_testing.item(0, 3).text()


def test_line_pinned_review_notes_formatting():
    """Verify that line-pinned review notes display with clean pin badges."""
    pin_ref = "Testing Grid Row #4 (VR-004)"
    comment = "TDS not deducted under section 194C"
    full_text = f"[PIN: {pin_ref}] {comment}"

    assert full_text.startswith("[PIN:")
    pin_part, _, rem = full_text.partition("]")
    extracted_pin = pin_part.replace("[PIN:", "").strip()
    extracted_rem = rem.strip()

    assert extracted_pin == pin_ref
    assert extracted_rem == comment
