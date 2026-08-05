import sys
import os
import json
import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath('src'))
from PySide6.QtWidgets import QApplication, QComboBox
from core.config import get_default_data_dir

# Ensure QApplication instance exists for PySide6 GUI elements
app = QApplication.instance() or QApplication(sys.argv)

def test_compliance_signoffs_roundtrip():
    from ui.compliance import ComplianceWidget, CARO_2020_CLAUSES, FORM_3CD_CLAUSES

    with patch("PySide6.QtWidgets.QMessageBox.information"):
        # 1. Instantiate widget
        widget = ComplianceWidget()

        # 2. Modify combo selections
        caro_combo = widget.caro_table.cellWidget(0, 3)
        assert isinstance(caro_combo, QComboBox)
        caro_combo.setCurrentText("Qualified / Remark")

        f3cd_combo = widget.f3cd_table.cellWidget(0, 3)
        assert isinstance(f3cd_combo, QComboBox)
        f3cd_combo.setCurrentText("Observation Noted")

        # 3. Save sign-offs
        widget.save_compliance_signoffs()

        # 4. Verify JSON file on disk
        filepath = widget.get_signoffs_file_path()
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        code_caro = CARO_2020_CLAUSES[0][0]
        code_f3cd = FORM_3CD_CLAUSES[0][0]
        assert data.get("caro", {}).get(code_caro) == "Qualified / Remark"
        assert data.get("form3cd", {}).get(code_f3cd) == "Observation Noted"

        # 5. Instantiate a NEW widget and verify load restores selections
        widget2 = ComplianceWidget()

        caro_combo2 = widget2.caro_table.cellWidget(0, 3)
        assert caro_combo2.currentText() == "Qualified / Remark"

        f3cd_combo2 = widget2.f3cd_table.cellWidget(0, 3)
        assert f3cd_combo2.currentText() == "Observation Noted"
