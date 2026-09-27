"""
SA 530 Audit Sampling & Sample Size Calculator Dialog.
Computes statistically defensible sample sizes, sampling intervals, and high-value thresholds per ICAI SA 530.
"""

import math
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.ui.theme import format_inr
from finauditpro.ui.widgets.custom_combo import CustomComboBox

# Standard ICAI / AICPA Confidence Factors for Monetary Unit Sampling (MUS)
# Zero expected misstatement expansion factors:
CONFIDENCE_FACTORS = {
    "95% Confidence (Factor 3.00 - High Risk / Significant RoMM)": 3.00,
    "90% Confidence (Factor 2.31 - Moderate Risk / Standard Testing)": 2.31,
    "85% Confidence (Factor 1.90 - Low Control Risk)": 1.90,
    "80% Confidence (Factor 1.61 - Analytical Corroboration Available)": 1.61,
}


class SamplingCalculatorDialog(QDialog):
    """Interactive statistical and monetary unit sampling calculator per SA 530."""

    def __init__(
        self,
        tolerable_misstatement_paise: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tolerable_misstatement_paise = tolerable_misstatement_paise
        self.calculated_sample_size: int = 0
        self.calculated_interval_paise: int = 0
        self.high_value_cutoff_paise: int = 0

        self.setWindowTitle("SA 530 Audit Sampling & Sample Size Calculator")
        self.resize(600, 520)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Statutory Guidance Banner
        guidance_box = QGroupBox("ICAI SA 530 AUDIT SAMPLING METHODOLOGY")
        guidance_box.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #1E40AF; background-color: #EFF6FF; "
            "border: 1px solid #BFDBFE; border-radius: 8px; margin-top: 10px; padding: 10px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #1D4ED8; }"
        )
        g_layout = QVBoxLayout(guidance_box)
        g_lbl = QLabel(
            "<b>Auditor Guidance:</b> Design an effective sample to provide a reasonable basis "
            "for conclusions about the population. All items exceeding the sampling interval "
            "must be tested 100% without sampling (Key Items per SA 530.A11)."
        )
        g_lbl.setWordWrap(True)
        g_lbl.setStyleSheet("color: #1E3A8A; font-size: 12px; background: transparent; border: none;")
        g_layout.addWidget(g_lbl)
        layout.addWidget(guidance_box)

        # 2. Input Parameters Form
        form = QFormLayout()
        form.setSpacing(10)

        field_style = (
            "QLineEdit, QComboBox { border: 1px solid #CBD5E1; border-radius: 6px; "
            "padding: 6px 10px; font-size: 13px; color: #0F172A; background-color: #FFFFFF; min-width: 260px; }"
            "QLineEdit:focus, QComboBox:focus { border-color: #2563EB; }"
        )

        self.method_combo = CustomComboBox()
        self.method_combo.setStyleSheet(field_style)
        self.method_combo.addItem("Monetary Unit Sampling (MUS / Probability Proportional to Size)", "MUS")
        self.method_combo.addItem("Stratified Sampling (High-Value 100% + Representative Sample)", "STRATIFIED")
        self.method_combo.addItem("Systematic Random Sampling (Uniform Interval)", "SYSTEMATIC")
        self.method_combo.addItem("Haphazard / Qualitative Selection (Auditor Judgment)", "HAPHAZARD")

        self.pop_count_input = QLineEdit("500")
        self.pop_count_input.setPlaceholderText("Number of vouchers / records in population")
        self.pop_count_input.setStyleSheet(field_style)

        default_book_val = "10000000"  # 1 Crore default
        self.pop_amount_input = QLineEdit(default_book_val)
        self.pop_amount_input.setPlaceholderText("Total recorded book value in INR")
        self.pop_amount_input.setStyleSheet(field_style)

        default_tm = str(self.tolerable_misstatement_paise // 100) if self.tolerable_misstatement_paise else "500000"
        self.tm_input = QLineEdit(default_tm)
        self.tm_input.setPlaceholderText("Tolerable Misstatement / Performance Materiality in INR")
        self.tm_input.setStyleSheet(field_style)

        self.confidence_combo = CustomComboBox()
        self.confidence_combo.setStyleSheet(field_style)
        for label, factor in CONFIDENCE_FACTORS.items():
            self.confidence_combo.addItem(label, factor)
        self.confidence_combo.setCurrentIndex(1)  # Default 90%

        self.expected_misstatement_input = QLineEdit("0")
        self.expected_misstatement_input.setPlaceholderText("Expected misstatement in INR (usually 0)")
        self.expected_misstatement_input.setStyleSheet(field_style)

        form.addRow("Sampling Method:", self.method_combo)
        form.addRow("Population Item Count (N):", self.pop_count_input)
        form.addRow("Population Total Value (₹):", self.pop_amount_input)
        form.addRow("Tolerable Misstatement (TM / PM) (₹):", self.tm_input)
        form.addRow("Confidence Level & Risk Factor:", self.confidence_combo)
        form.addRow("Expected Misstatement (₹):", self.expected_misstatement_input)

        layout.addLayout(form)

        # 3. Compute Button
        btn_calc = QPushButton("Calculate Sample Size per SA 530")
        btn_calc.setStyleSheet(
            "background-color: #2563EB; color: white; font-weight: 600; padding: 8px 16px; border-radius: 6px;"
        )
        btn_calc.clicked.connect(self._recalculate)
        layout.addWidget(btn_calc)

        # 4. Results Card
        res_card = QGroupBox("SA 530 SAMPLE SIZE & INTERVAL OUTPUT")
        res_card.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #0F172A; background-color: #F8FAFC; "
            "border: 1px solid #E2E8F0; border-radius: 8px; margin-top: 6px; padding: 10px; }"
        )
        res_layout = QVBoxLayout(res_card)
        res_layout.setSpacing(6)

        self.lbl_sample_size = QLabel("<b>Recommended Sample Size (n):</b> —")
        self.lbl_sample_size.setStyleSheet("font-size: 14px; color: #0F172A;")

        self.lbl_interval = QLabel("<b>Sampling Interval (J):</b> —")
        self.lbl_interval.setStyleSheet("font-size: 13px; color: #334155;")

        self.lbl_cutoff = QLabel("<b>Key Items (100% Testing Cutoff):</b> —")
        self.lbl_cutoff.setStyleSheet("font-size: 13px; color: #334155;")

        self.lbl_note = QLabel("Press 'Calculate' to evaluate statistically defensible sample parameters.")
        self.lbl_note.setWordWrap(True)
        self.lbl_note.setStyleSheet("font-size: 12px; color: #64748B; font-style: italic;")

        res_layout.addWidget(self.lbl_sample_size)
        res_layout.addWidget(self.lbl_interval)
        res_layout.addWidget(self.lbl_cutoff)
        res_layout.addWidget(self.lbl_note)
        layout.addWidget(res_card)

        # 5. Dialog Actions
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_apply = QPushButton("Apply && Insert Rows to Testing Grid")
        self.btn_apply.setStyleSheet(
            "background-color: #10B981; color: white; font-weight: 600; padding: 8px 18px; border-radius: 6px;"
        )
        self.btn_apply.setEnabled(False)
        self.btn_apply.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(self.btn_apply)
        layout.addLayout(btn_box)

        # Initial calculation
        self._recalculate()

    def _recalculate(self) -> None:
        try:
            pop_count_str = self.pop_count_input.text().replace(",", "").strip()
            pop_amount_str = self.pop_amount_input.text().replace(",", "").strip()
            tm_str = self.tm_input.text().replace(",", "").strip()

            n_pop = int(pop_count_str) if pop_count_str else 100
            val_pop = float(pop_amount_str) if pop_amount_str else 1000000.0
            tm = float(tm_str) if tm_str else 100000.0
            factor = float(self.confidence_combo.currentData() or 2.31)
            method = self.method_combo.currentData() or "MUS"

            if n_pop <= 0 or val_pop <= 0 or tm <= 0:
                QMessageBox.warning(self, "Invalid Inputs", "Population count, amount, and TM must be positive numbers.")
                return

            if method == "MUS":
                # Monetary Unit Sampling: J = TM / factor
                interval = tm / factor
                raw_n = val_pop / interval if interval > 0 else 25
                sample_size = max(5, min(n_pop, int(math.ceil(raw_n))))
                cutoff = interval
                note = (
                    f"MUS Formula: Interval J = TM ({format_inr(int(tm * 100))}) / Factor ({factor}) = "
                    f"{format_inr(int(interval * 100))}. Any individual item exceeding {format_inr(int(cutoff * 100))} "
                    f"must be tested 100% as a Key Item."
                )
            elif method == "STRATIFIED":
                cutoff = tm
                sample_size = max(10, min(n_pop, int(math.ceil(n_pop * 0.05 + 15))))
                interval = val_pop / sample_size if sample_size > 0 else val_pop
                note = (
                    f"Stratified Selection: 100% verification for items > {format_inr(int(cutoff * 100))}. "
                    f"Remaining stratum sampled with size n={sample_size}."
                )
            elif method == "SYSTEMATIC":
                sample_size = max(5, min(n_pop, int(math.ceil(20 * (factor / 2.0)))))
                interval = val_pop / sample_size if sample_size > 0 else 0
                cutoff = interval
                step = max(1, n_pop // sample_size)
                note = f"Systematic Sampling: Pick every {step}-th voucher from population of {n_pop} items."
            else:
                sample_size = 20
                interval = val_pop / sample_size if sample_size > 0 else 0
                cutoff = tm
                note = "Haphazard / Qualitative Selection based on professional auditor judgment under SA 530."

            self.calculated_sample_size = sample_size
            self.calculated_interval_paise = int(round(interval * 100))
            self.high_value_cutoff_paise = int(round(cutoff * 100))

            self.lbl_sample_size.setText(
                f"<b>Recommended Sample Size (n):</b> <span style='color: #2563EB; font-size: 15px;'>{sample_size} vouchers</span>"
            )
            self.lbl_interval.setText(
                f"<b>Sampling Interval (J):</b> {format_inr(self.calculated_interval_paise)}"
            )
            self.lbl_cutoff.setText(
                f"<b>Key Items (100% Testing Cutoff):</b> {format_inr(self.high_value_cutoff_paise)}"
            )
            self.lbl_note.setText(note)
            self.btn_apply.setEnabled(True)

        except Exception as ex:
            QMessageBox.critical(self, "Calculation Error", f"Failed to compute sample size: {ex}")
