"""UI Dialog for Phase D: Audit Completion & Misstatement Evaluation (SA 450, SA 570, SA 580, SA 560, SA 520)."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_completion_dtos import CreateGoingConcernAssessmentDTO
from finauditpro.application.services.audit_completion_service import AuditCompletionService


class AuditCompletionDialog(QDialog):
    """Multi-tab workspace for ICAI Standards on Auditing completion procedures."""

    def __init__(
        self, db_manager: Any, engagement_id: str, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.engagement_id = engagement_id
        self.completion_service = AuditCompletionService(db_manager)

        self.setWindowTitle("Audit Completion & Misstatement Evaluation — FinAuditPro")
        self.resize(1100, 750)
        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header Bar
        top_bar = QHBoxLayout()
        self.lbl_title = QLabel("Statutory Audit Completion Dashboard")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 15px; color: #0f172a;")
        top_bar.addWidget(self.lbl_title)
        top_bar.addStretch()

        self.btn_refresh = QPushButton("Refresh Completion Workpapers")
        self.btn_refresh.clicked.connect(self._load_data)
        top_bar.addWidget(self.btn_refresh)
        layout.addLayout(top_bar)

        # Tab Widget
        self.tabs = QTabWidget()
        self.tab_sa450 = QWidget()
        self.tab_sa570 = QWidget()
        self.tab_sa580 = QWidget()
        self.tab_sa560 = QWidget()
        self.tab_sa520 = QWidget()

        self.tabs.addTab(self.tab_sa450, "SA 450 Misstatements (SUM)")
        self.tabs.addTab(self.tab_sa570, "SA 570 Going Concern")
        self.tabs.addTab(self.tab_sa580, "SA 580 Representation Letter (MRL)")
        self.tabs.addTab(self.tab_sa560, "SA 560 Subsequent Events")
        self.tabs.addTab(self.tab_sa520, "SA 520 Final Analytical Review")

        self._setup_sa450_tab()
        self._setup_sa570_tab()
        self._setup_sa580_tab()
        self._setup_sa560_tab()
        self._setup_sa520_tab()

        layout.addWidget(self.tabs)

        # Bottom Close Bar
        bot_bar = QHBoxLayout()
        bot_bar.addStretch()
        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.accept)
        bot_bar.addWidget(self.btn_close)
        layout.addLayout(bot_bar)

    def _setup_sa450_tab(self) -> None:
        layout = QVBoxLayout(self.tab_sa450)
        self.lbl_sa450_summary = QLabel("Loading SA 450 evaluation...")
        self.lbl_sa450_summary.setStyleSheet(
            "padding: 10px; background-color: #f1f5f9; border-radius: 4px; font-weight: 500;"
        )
        layout.addWidget(self.lbl_sa450_summary)

        self.tbl_sa450 = QTableWidget(0, 6)
        self.tbl_sa450.setHorizontalHeaderLabels([
            "Ref #", "Type", "Title / Account", "Status", "Amount (₹)", "Clearly Trivial"
        ])
        self.tbl_sa450.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_sa450)

    def _setup_sa570_tab(self) -> None:
        layout = QVBoxLayout(self.tab_sa570)
        self.lbl_sa570_status = QLabel("SA 570 Assessment Memo")
        self.lbl_sa570_status.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
        layout.addWidget(self.lbl_sa570_status)

        self.lbl_sa570_conclusion = QLabel("Evaluating solvency...")
        self.lbl_sa570_conclusion.setStyleSheet(
            "padding: 12px; background-color: #f8fafc; border-left: 4px solid #3b82f6; font-size: 12px;"
        )
        self.lbl_sa570_conclusion.setWordWrap(True)
        layout.addWidget(self.lbl_sa570_conclusion)

        grp = QGroupBox("12-Month Solvency Mitigations")
        grp_layout = QVBoxLayout(grp)
        self.tbl_mitigations = QTableWidget(0, 4)
        self.tbl_mitigations.setHorizontalHeaderLabels([
            "Risk Factor", "Management Action Plan", "Auditor Evaluation", "Feasible"
        ])
        self.tbl_mitigations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        grp_layout.addWidget(self.tbl_mitigations)
        layout.addWidget(grp)

        btn_bar = QHBoxLayout()
        btn_bar.addStretch()
        self.btn_partner_signoff = QPushButton("Partner Sign-Off (SA 570)")
        self.btn_partner_signoff.setStyleSheet(
            "background-color: #059669; color: white; font-weight: bold; padding: 6px 14px;"
        )
        self.btn_partner_signoff.clicked.connect(self._signoff_going_concern)
        btn_bar.addWidget(self.btn_partner_signoff)
        layout.addLayout(btn_bar)

    def _setup_sa580_tab(self) -> None:
        layout = QVBoxLayout(self.tab_sa580)
        self.lbl_mrl_info = QLabel("SA 580 Management Representation Letter")
        self.lbl_mrl_info.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
        layout.addWidget(self.lbl_mrl_info)

        self.tbl_mrl_clauses = QTableWidget(0, 4)
        self.tbl_mrl_clauses.setHorizontalHeaderLabels([
            "Clause #", "Category", "Title", "Mandatory"
        ])
        self.tbl_mrl_clauses.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_mrl_clauses)

    def _setup_sa560_tab(self) -> None:
        layout = QVBoxLayout(self.tab_sa560)
        self.lbl_sa560_header = QLabel("SA 560 Subsequent Events Register (Post-Balance Sheet)")
        self.lbl_sa560_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
        layout.addWidget(self.lbl_sa560_header)

        self.tbl_subseq = QTableWidget(0, 5)
        self.tbl_subseq.setHorizontalHeaderLabels([
            "Event Date", "Classification", "Description", "Estimated Amount (₹)", "Procedure Applied"
        ])
        self.tbl_subseq.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_subseq)

    def _setup_sa520_tab(self) -> None:
        layout = QVBoxLayout(self.tab_sa520)
        self.lbl_sa520_header = QLabel("SA 520 Final Analytical Ratios & Consistency Review")
        self.lbl_sa520_header.setStyleSheet("font-weight: bold; font-size: 13px; color: #1e293b;")
        layout.addWidget(self.lbl_sa520_header)

        self.tbl_ratios = QTableWidget(0, 6)
        self.tbl_ratios.setHorizontalHeaderLabels([
            "Analytical Ratio", "Category", "Current Year", "Previous Year", "Variance %", "Significant Variance"
        ])
        self.tbl_ratios.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.tbl_ratios)

    def _load_data(self) -> None:
        # Load SA 450
        try:
            summary = self.completion_service.evaluate_sa450_misstatements(self.engagement_id)
            om_rs = summary.overall_materiality_paise / 100
            unc_rs = summary.total_uncorrected_amount_paise / 100
            self.lbl_sa450_summary.setText(
                f"Overall Materiality: ₹{om_rs:,.2f} | Performance Materiality: ₹{summary.performance_materiality_paise/100:,.2f}\n"
                f"Total Identified: {summary.total_identified_misstatements} | Corrected: {summary.total_corrected_misstatements} | "
                f"Uncorrected: {summary.total_uncorrected_misstatements} (Total: ₹{unc_rs:,.2f})\n"
                f"Conclusion: {summary.audit_conclusion}"
            )
            self.tbl_sa450.setRowCount(0)
            for row, m in enumerate(summary.misstatements):
                self.tbl_sa450.insertRow(row)
                self.tbl_sa450.setItem(row, 0, QTableWidgetItem(m.misstatement_number))
                self.tbl_sa450.setItem(row, 1, QTableWidgetItem(m.misstatement_type))
                self.tbl_sa450.setItem(row, 2, QTableWidgetItem(m.title))
                self.tbl_sa450.setItem(row, 3, QTableWidgetItem(m.status))
                self.tbl_sa450.setItem(row, 4, QTableWidgetItem(f"₹{m.amount_paise/100:,.2f}"))
                self.tbl_sa450.setItem(row, 5, QTableWidgetItem("Yes" if m.is_clearly_trivial else "No"))
        except Exception as e:
            self.lbl_sa450_summary.setText(f"SA 450 Notice: {e}")

        # Load SA 570
        try:
            gc = self.completion_service.get_going_concern_assessment(self.engagement_id)
            if gc:
                signoff_str = " (Partner Signed Off)" if gc.partner_signoff else " (Draft / Pending Signoff)"
                self.lbl_sa570_status.setText(f"SA 570 Solvency Risk: {gc.solvency_risk_level}{signoff_str}")
                self.lbl_sa570_conclusion.setText(
                    f"Audit Conclusion: {gc.audit_conclusion}\nRationale: {gc.conclusion_rationale}"
                )
                self.tbl_mitigations.setRowCount(0)
                for row, mit in enumerate(gc.mitigations):
                    self.tbl_mitigations.insertRow(row)
                    self.tbl_mitigations.setItem(row, 0, QTableWidgetItem(mit.factor_title))
                    self.tbl_mitigations.setItem(row, 1, QTableWidgetItem(mit.management_plan))
                    self.tbl_mitigations.setItem(row, 2, QTableWidgetItem(mit.auditor_evaluation))
                    self.tbl_mitigations.setItem(row, 3, QTableWidgetItem("Yes" if mit.is_feasible else "No"))
        except Exception as e:
            self.lbl_sa570_conclusion.setText(f"SA 570 Notice: {e}")

        # Load SA 580
        try:
            mrls = self.completion_service.list_mrls(self.engagement_id)
            if mrls:
                mrl = mrls[0]
                self.lbl_mrl_info.setText(f"MRL #{mrl.mrl_number} — Status: {mrl.status}")
                self.tbl_mrl_clauses.setRowCount(0)
                for row, c in enumerate(mrl.clauses):
                    self.tbl_mrl_clauses.insertRow(row)
                    self.tbl_mrl_clauses.setItem(row, 0, QTableWidgetItem(c.clause_number))
                    self.tbl_mrl_clauses.setItem(row, 1, QTableWidgetItem(c.category))
                    self.tbl_mrl_clauses.setItem(row, 2, QTableWidgetItem(c.title))
                    self.tbl_mrl_clauses.setItem(row, 3, QTableWidgetItem("Yes" if c.is_mandatory else "No"))
        except Exception:
            pass

        # Load SA 560
        try:
            events = self.completion_service.list_subsequent_events(self.engagement_id)
            self.tbl_subseq.setRowCount(0)
            for row, ev in enumerate(events):
                self.tbl_subseq.insertRow(row)
                self.tbl_subseq.setItem(row, 0, QTableWidgetItem(ev.event_date))
                self.tbl_subseq.setItem(row, 1, QTableWidgetItem(ev.event_type))
                self.tbl_subseq.setItem(row, 2, QTableWidgetItem(ev.description))
                self.tbl_subseq.setItem(row, 3, QTableWidgetItem(f"₹{ev.estimated_amount_paise/100:,.2f}"))
                self.tbl_subseq.setItem(row, 4, QTableWidgetItem(ev.procedure_applied))
        except Exception:
            pass

        # Load SA 520
        try:
            far = self.completion_service.get_final_analytical_review(self.engagement_id)
            if far:
                self.lbl_sa520_header.setText(f"SA 520 Review: {far.overall_consistency_conclusion}")
                self.tbl_ratios.setRowCount(0)
                for row, r in enumerate(far.ratio_lines):
                    self.tbl_ratios.insertRow(row)
                    self.tbl_ratios.setItem(row, 0, QTableWidgetItem(r.ratio_name))
                    self.tbl_ratios.setItem(row, 1, QTableWidgetItem(r.category))
                    self.tbl_ratios.setItem(row, 2, QTableWidgetItem(f"{r.current_year_value:.2f}"))
                    self.tbl_ratios.setItem(row, 3, QTableWidgetItem(f"{r.previous_year_value:.2f}"))
                    self.tbl_ratios.setItem(row, 4, QTableWidgetItem(f"{r.variance_percentage:+.2f}%"))
                    self.tbl_ratios.setItem(row, 5, QTableWidgetItem("FLAGGED" if r.is_significant_variance else "Normal"))
        except Exception:
            pass

    def _signoff_going_concern(self) -> None:
        try:
            dto = CreateGoingConcernAssessmentDTO(
                partner_signoff=True,
                reviewer="Engagement Partner",
            )
            self.completion_service.create_or_update_going_concern_assessment(
                self.engagement_id, dto
            )
            QMessageBox.information(
                self, "Sign-Off Complete", "Going Concern Assessment signed off successfully by Partner."
            )
            self._load_data()
        except Exception as e:
            QMessageBox.warning(self, "Sign-Off Notice", str(e))
