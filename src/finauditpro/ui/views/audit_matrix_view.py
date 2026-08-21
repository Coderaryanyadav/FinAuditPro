"""Audit Matrix Workspace View for FinAuditPro."""
from typing import Any
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from finauditpro.application.audit_planning_dtos import (
    SetMaterialityDTO,
)
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.domain.audit_matrix_entities import (
    MaterialityAssessment,
)
from finauditpro.domain.entities import Engagement
from finauditpro.domain.materiality_engine import BENCHMARK_GUIDANCE_OPTIONS
from finauditpro.ui.dialogs.finding_dialog import FindingDialog
from finauditpro.ui.dialogs.procedure_dialog import ProcedureDialog
from finauditpro.ui.dialogs.risk_dialog import RiskDialog
from finauditpro.ui.dialogs.traceability_dialog import TraceabilityDialog
from finauditpro.ui.theme import CardWidget, MetricCard

class AuditMatrixView(QWidget):
    """Primary Audit Execution Matrix Workspace view."""
    matrix_changed = Signal()
    def __init__(
        self,
        engagement_service: EngagementService,
        planning_service: Any = None,
        traceability_service: Any = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        if hasattr(traceability_service, "list_risks_for_engagement"):
            self.planning_service = traceability_service
            self.traceability_service = None
        else:
            self.planning_service = planning_service
            self.traceability_service = traceability_service
        self.current_engagement: Engagement | None = None
        self.current_materiality: MaterialityAssessment | None = None
        self._init_ui()
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)
        header_layout = QHBoxLayout()
        self.title_label = QLabel("Audit Planning & Execution Core (Materiality • Risk • Procedures • Findings)")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #f8fafc;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        self.tabs = QTabWidget()
        self.tab_mat = QWidget()
        self._init_materiality_tab()
        self.tabs.addTab(self.tab_mat, "SA 320 Materiality")
        self.tab_risks = QWidget()
        self._init_risks_tab()
        self.tabs.addTab(self.tab_risks, "Risk Register")
        self.tab_procs = QWidget()
        self._init_procedures_tab()
        self.tabs.addTab(self.tab_procs, "Audit Procedures")
        self.tab_findings = QWidget()
        self._init_findings_tab()
        self.tabs.addTab(self.tab_findings, "Unified Findings Vault")
        layout.addWidget(self.tabs)
    def _init_materiality_tab(self) -> None:
        layout = QVBoxLayout(self.tab_mat)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)
        card = CardWidget("SA 320 Audit Materiality Calculation Engine")
        form = QFormLayout()
        self.bm_combo = QComboBox()
        for opt in BENCHMARK_GUIDANCE_OPTIONS:
            self.bm_combo.addItem(f"{opt.benchmark_type.value} ({opt.default_overall_pct}%)", opt.benchmark_type)
        self.bm_amount_input = QLineEdit()
        self.bm_amount_input.setPlaceholderText("Enter benchmark amount in INR (e.g. 50000000)...")
        self.disclaimer_label = QLabel("⚠️ Non-Statutory Guidance: Percentages are auditor judgements per SA 320 (verified: false).")
        self.disclaimer_label.setStyleSheet("color: #f59e0b; font-size: 12px; font-style: italic;")
        calc_btn = QPushButton("Calculate & Save Materiality Version")
        calc_btn.clicked.connect(self._on_calculate_materiality)
        form.addRow("Financial Benchmark:", self.bm_combo)
        form.addRow("Benchmark Amount (INR):", self.bm_amount_input)
        form.addRow("", self.disclaimer_label)
        form.addRow("", calc_btn)
        card.content_layout.addLayout(form)
        layout.addWidget(card)
        metrics_layout = QHBoxLayout()
        self.card_overall = MetricCard("Overall Materiality (OM)", "₹ 0.00", "SA 320 Benchmark × 1%")
        self.card_performance = MetricCard("Performance Materiality (PM)", "₹ 0.00", "Testing Scope (75% of OM)")
        self.card_trivial = MetricCard("Clearly Trivial (CTT)", "₹ 0.00", "De Minimis Limit (5% of OM)")
        metrics_layout.addWidget(self.card_overall)
        metrics_layout.addWidget(self.card_performance)
        metrics_layout.addWidget(self.card_trivial)
        layout.addLayout(metrics_layout)
        hist_card = CardWidget("Materiality Revision History")
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels(["Version", "Benchmark", "Amount (INR)", "OM (INR)", "PM (INR)", "CTT (INR)"])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hist_table.verticalHeader().setVisible(False)
        hist_card.content_layout.addWidget(self.hist_table)
        layout.addWidget(hist_card)
    def _init_risks_tab(self) -> None:
        layout = QVBoxLayout(self.tab_risks)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(QLabel("Qualitative Risk Register & Assertion Mapping (SA 315)"))
        header.addStretch()
        btn_new_risk = QPushButton("+ New Audit Risk")
        btn_new_risk.clicked.connect(self._on_new_risk_clicked)
        header.addWidget(btn_new_risk)
        layout.addLayout(header)
        card = CardWidget()
        self.risks_table = QTableWidget()
        self.risks_table.setColumnCount(8)
        self.risks_table.setHorizontalHeaderLabels(
            [
                "Code",
                "Title",
                "Category",
                "Assertions",
                "Inherent",
                "Control",
                "Derived RoMM",
                "Significant?",
            ]
        )
        self.risks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.risks_table.verticalHeader().setVisible(False)
        card.content_layout.addWidget(self.risks_table)
        layout.addWidget(card)
    def _init_procedures_tab(self) -> None:
        layout = QVBoxLayout(self.tab_procs)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(QLabel("Structured Audit Procedures Execution Hub"))
        header.addStretch()
        btn_new_proc = QPushButton("+ New Procedure")
        btn_new_proc.clicked.connect(self._on_new_proc_clicked)
        header.addWidget(btn_new_proc)
        layout.addLayout(header)
        card = CardWidget()
        self.procs_table = QTableWidget()
        self.procs_table.setColumnCount(6)
        self.procs_table.setHorizontalHeaderLabels(["Code", "Objective", "Type", "Status", "Preparer", "Reviewer"])
        self.procs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.procs_table.verticalHeader().setVisible(False)
        card.content_layout.addWidget(self.procs_table)
        layout.addWidget(card)
    def _init_findings_tab(self) -> None:
        layout = QVBoxLayout(self.tab_findings)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)
        header = QHBoxLayout()
        header.addWidget(QLabel("Unified Findings Directory Across All Sources"))
        header.addStretch()
        btn_new_finding = QPushButton("+ Log Finding")
        btn_new_finding.clicked.connect(self._on_new_finding_clicked)
        header.addWidget(btn_new_finding)
        layout.addLayout(header)
        card = CardWidget("Unified Findings Model")
        self.findings_table = QTableWidget()
        self.findings_table.setColumnCount(7)
        self.findings_table.setHorizontalHeaderLabels(["Source", "Title", "Severity", "Monetary Impact", "Account", "Status", "Traceability"])
        self.findings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.findings_table.verticalHeader().setVisible(False)
        card.content_layout.addWidget(self.findings_table)
        layout.addWidget(card)
    def set_engagement(self, engagement_id: str | None) -> None:
        if engagement_id:
            try:
                self.current_engagement = self.engagement_service.get_engagement(engagement_id)
            except Exception:
                self.current_engagement = None
        else:
            self.current_engagement = None
        self.refresh()
    def refresh(self) -> None:
        if not self.current_engagement:
            self.card_overall.set_value("₹ 0.00")
            self.card_performance.set_value("₹ 0.00")
            self.card_trivial.set_value("₹ 0.00")
            self.risks_table.setRowCount(0)
            self.procs_table.setRowCount(0)
            self.findings_table.setRowCount(0)
            self.hist_table.setRowCount(0)
            return
        mat_fn = getattr(self.planning_service, "get_latest_materiality", None)
        mat = mat_fn(self.current_engagement.id) if mat_fn else None
        if mat:
            self.current_materiality = mat
            self.card_overall.set_value(mat.overall_materiality.formatted if hasattr(mat.overall_materiality, "formatted") else f"₹ {mat.overall_materiality:,.2f}")
            self.card_performance.set_value(mat.performance_materiality.formatted if hasattr(mat.performance_materiality, "formatted") else f"₹ {mat.performance_materiality:,.2f}")
            self.card_trivial.set_value(mat.clearly_trivial_threshold.formatted if hasattr(mat.clearly_trivial_threshold, "formatted") else f"₹ {mat.clearly_trivial_threshold:,.2f}")
        else:
            self.card_overall.set_value("₹ 0.00")
            self.card_performance.set_value("₹ 0.00")
            self.card_trivial.set_value("₹ 0.00")
        hist_fn = getattr(self.planning_service, "list_materiality_history", None)
        history = hist_fn(self.current_engagement.id) if hist_fn else ([mat] if mat else [])
        self.hist_table.setRowCount(0)
        for r, m in enumerate(history):
            self.hist_table.insertRow(r)
            self.hist_table.setItem(r, 0, QTableWidgetItem(f"v{m.version}"))
            self.hist_table.setItem(r, 1, QTableWidgetItem(m.benchmark_type.value))
            self.hist_table.setItem(
                r,
                2,
                QTableWidgetItem(m.benchmark_amount.formatted if hasattr(m.benchmark_amount, "formatted") else f"₹ {m.benchmark_amount:,.2f}"),
            )
            self.hist_table.setItem(
                r,
                3,
                QTableWidgetItem(m.overall_materiality.formatted if hasattr(m.overall_materiality, "formatted") else f"₹ {m.overall_materiality:,.2f}"),
            )
            self.hist_table.setItem(
                r,
                4,
                QTableWidgetItem(m.performance_materiality.formatted if hasattr(m.performance_materiality, "formatted") else f"₹ {m.performance_materiality:,.2f}"),
            )
            self.hist_table.setItem(
                r,
                5,
                QTableWidgetItem(m.clearly_trivial_threshold.formatted if hasattr(m.clearly_trivial_threshold, "formatted") else f"₹ {m.clearly_trivial_threshold:,.2f}"),
            )
        risks_fn = getattr(self.planning_service, "list_risks", None) or getattr(self.planning_service, "list_risks_for_engagement", None)
        risks = risks_fn(self.current_engagement.id) if risks_fn else []
        self.risks_table.setRowCount(0)
        for r, rk in enumerate(risks):
            self.risks_table.insertRow(r)
            self.risks_table.setItem(r, 0, QTableWidgetItem(rk.risk_code))
            self.risks_table.setItem(r, 1, QTableWidgetItem(getattr(rk, "title", rk.risk_code)))
            self.risks_table.setItem(r, 2, QTableWidgetItem(rk.category))
            assertions_str = ", ".join([a.value for a in rk.assertions]) if hasattr(rk, "assertions") else rk.assertion.value
            self.risks_table.setItem(r, 3, QTableWidgetItem(assertions_str))
            self.risks_table.setItem(r, 4, QTableWidgetItem(rk.inherent_risk.value))
            self.risks_table.setItem(r, 5, QTableWidgetItem(rk.control_risk.value))
            romm_val = rk.derived_romm.value if hasattr(rk, "derived_romm") else rk.severity.value
            self.risks_table.setItem(r, 6, QTableWidgetItem(romm_val))
            sig_val = "YES" if getattr(rk, "is_significant_risk", False) else "NO"
            self.risks_table.setItem(r, 7, QTableWidgetItem(sig_val))
        procs_fn = getattr(self.planning_service, "list_procedures", None) or getattr(self.planning_service, "list_procedures_for_engagement", None)
        procs = procs_fn(self.current_engagement.id) if procs_fn else []
        self.procs_table.setRowCount(0)
        for r, p in enumerate(procs):
            self.procs_table.insertRow(r)
            self.procs_table.setItem(r, 0, QTableWidgetItem(p.procedure_code))
            self.procs_table.setItem(r, 1, QTableWidgetItem(p.objective))
            self.procs_table.setItem(r, 2, QTableWidgetItem(p.procedure_type))
            self.procs_table.setItem(r, 3, QTableWidgetItem(p.status.value))
            self.procs_table.setItem(r, 4, QTableWidgetItem(p.preparer or "-"))
            self.procs_table.setItem(r, 5, QTableWidgetItem(p.reviewer or "-"))
        findings_fn = getattr(self.planning_service, "list_findings", None) or getattr(self.planning_service, "list_findings_for_engagement", None)
        findings = findings_fn(self.current_engagement.id) if findings_fn else []
        self.findings_table.setRowCount(0)
        for r, f in enumerate(findings):
            self.findings_table.insertRow(r)
            src_val = f.source.value if hasattr(f.source, "value") else str(f.source)
            self.findings_table.setItem(r, 0, QTableWidgetItem(src_val.upper()))
            self.findings_table.setItem(r, 1, QTableWidgetItem(f.title))
            self.findings_table.setItem(r, 2, QTableWidgetItem(f.severity.value))
            amt_str = f.monetary_amount.formatted if hasattr(f, "monetary_amount") and hasattr(f.monetary_amount, "formatted") else f"₹ {getattr(f, 'monetary_amount', 0):,.2f}"
            self.findings_table.setItem(r, 3, QTableWidgetItem(amt_str))
            self.findings_table.setItem(r, 4, QTableWidgetItem(f.affected_account or "-"))
            self.findings_table.setItem(r, 5, QTableWidgetItem(f.status.value))
            btn_graph = QPushButton("View Graph")
            btn_graph.clicked.connect(lambda _, fid=f.id: self._open_traceability(fid))
            self.findings_table.setCellWidget(r, 6, btn_graph)
    def _open_traceability(self, finding_id: str) -> None:
        if not self.current_engagement:
            return
        dialog = TraceabilityDialog(self.traceability_service, self.current_engagement.id, finding_id, parent=self)
        dialog.exec()
    def _on_calculate_materiality(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        amt_str = self.bm_amount_input.text().replace(",", "").strip()
        if not amt_str:
            QMessageBox.warning(self, "Validation Error", "Please enter a benchmark amount in INR.")
            return
        try:
            val = float(amt_str)
            paise = int(round(val * 100))
        except ValueError:
            QMessageBox.warning(self, "Validation Error", "Invalid numeric benchmark amount.")
            return
        dto = SetMaterialityDTO(
            engagement_id=self.current_engagement.id,
            benchmark_type=self.bm_combo.currentData(),
            benchmark_amount_paise=paise,
        )
        try:
            mat = self.planning_service.set_materiality(dto)
            QMessageBox.information(
                self,
                "SA 320 Materiality Calculated",
                f"Calculated & Saved Materiality v{mat.version}:\nOverall Materiality: {mat.overall_materiality.formatted}\nPerformance Materiality: {mat.performance_materiality.formatted}\nClearly Trivial Limit: {mat.clearly_trivial_threshold.formatted}",
            )
            self.refresh()
            self.matrix_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed to calculate materiality: {ex}")
    def _on_new_risk_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        dialog = RiskDialog(self.planning_service, engagement=self.current_engagement, parent=self)
        if dialog.exec() == RiskDialog.DialogCode.Accepted:
            self.refresh()
            self.matrix_changed.emit()
    def _on_new_proc_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        risks = self.planning_service.list_risks(self.current_engagement.id)
        dialog = ProcedureDialog(self.planning_service, engagement=self.current_engagement, risks=risks, parent=self)
        if dialog.exec() == ProcedureDialog.DialogCode.Accepted:
            self.refresh()
            self.matrix_changed.emit()
    def _on_new_finding_clicked(self) -> None:
        if not self.current_engagement:
            QMessageBox.warning(self, "No Engagement", "Please select an active audit engagement first.")
            return
        procs = self.planning_service.list_procedures(self.current_engagement.id)
        risks = self.planning_service.list_risks(self.current_engagement.id)
        dialog = FindingDialog(
            self.planning_service,
            engagement=self.current_engagement,
            procedures=procs,
            risks=risks,
            parent=self,
        )
        if dialog.exec() == FindingDialog.DialogCode.Accepted:
            self.refresh()
            self.matrix_changed.emit()
