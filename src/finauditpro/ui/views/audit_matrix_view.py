"""
Audit Matrix Workspace View for FinAuditPro.
Planning & Execution Core: SA 320 Materiality, SA 315 Risk Register, Procedures, and Findings.
"""

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

from finauditpro.application.audit_planning_dtos import SetMaterialityDTO
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.domain.audit_matrix_entities import MaterialityAssessment
from finauditpro.domain.entities import Engagement
from finauditpro.domain.materiality_engine import BENCHMARK_GUIDANCE_OPTIONS
from finauditpro.ui.dialogs.finding_dialog import FindingDialog
from finauditpro.ui.dialogs.procedure_dialog import ProcedureDialog
from finauditpro.ui.dialogs.risk_dialog import RiskDialog
from finauditpro.ui.dialogs.traceability_dialog import TraceabilityDialog
from finauditpro.ui.theme import CardWidget, EmptyStateWidget, MetricCard, PageHeader


class AuditMatrixView(QWidget):
    """Primary Audit Execution Matrix Workspace view."""

    matrix_changed = Signal()

    def __init__(self, engagement_service: EngagementService, planning_service: Any = None, traceability_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engagement_service = engagement_service
        is_tr_planning = hasattr(traceability_service, "list_risks_for_engagement")
        self.planning_service = traceability_service if is_tr_planning else planning_service
        self.traceability_service = None if is_tr_planning else traceability_service
        self.current_engagement: Engagement | None = None
        self.current_materiality: MaterialityAssessment | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        self.header = PageHeader("Audit Matrix", "Core planning & execution hub: SA 320 Materiality, SA 315 Risks, Procedures, and Findings.")
        layout.addWidget(self.header)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E2E8F0; background-color: #FFFFFF; border-radius: 8px; } QTabBar::tab { font-size: 12px; font-weight: 600; padding: 8px 18px; color: #64748B; border: none; background: transparent; } QTabBar::tab:selected { color: #2563EB; border-bottom: 2px solid #2563EB; font-weight: 700; }")

        self.tab_mat, self.tab_risks, self.tab_procs, self.tab_findings = QWidget(), QWidget(), QWidget(), QWidget()
        self._init_materiality_tab()
        self._init_risks_tab()
        self._init_procedures_tab()
        self._init_findings_tab()

        self.tabs.addTab(self.tab_mat, "SA 320 Materiality")
        self.tabs.addTab(self.tab_risks, "Risk Register (SA 315)")
        self.tabs.addTab(self.tab_procs, "Audit Procedures")
        self.tabs.addTab(self.tab_findings, "Unified Findings Vault")
        layout.addWidget(self.tabs, 1)

    def _init_materiality_tab(self) -> None:
        layout = QVBoxLayout(self.tab_mat)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        card = CardWidget("SA 320 AUDIT MATERIALITY CALCULATION ENGINE")
        form = QFormLayout()
        form.setSpacing(8)

        self.bm_combo = QComboBox()
        for opt in BENCHMARK_GUIDANCE_OPTIONS:
            self.bm_combo.addItem(f"{opt.benchmark_type.value} ({opt.default_overall_pct}%)", opt.benchmark_type)

        self.bm_amount_input = QLineEdit()
        self.bm_amount_input.setPlaceholderText("Enter benchmark amount in INR...")
        calc_btn = QPushButton("Calculate & Save Materiality")
        calc_btn.clicked.connect(self._on_calculate_materiality)

        form.addRow("Benchmark Type:", self.bm_combo)
        form.addRow("Amount (INR):", self.bm_amount_input)
        form.addRow("", calc_btn)
        card.content_layout.addLayout(form)
        layout.addWidget(card)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.card_overall = MetricCard("OVERALL MATERIALITY", "₹ 0.00", "Benchmark × 1%", accent_color="#2563EB")
        self.card_performance = MetricCard("PERFORMANCE MATERIALITY", "₹ 0.00", "75% of OM", accent_color="#16A34A")
        self.card_trivial = MetricCard("CLEARLY TRIVIAL", "₹ 0.00", "5% of OM", accent_color="#D97706")
        for c in (self.card_overall, self.card_performance, self.card_trivial):
            metrics.addWidget(c)
        layout.addLayout(metrics)

        hist_card = CardWidget("MATERIALITY REVISION HISTORY")
        self.hist_table = QTableWidget()
        self.hist_table.setColumnCount(6)
        self.hist_table.setHorizontalHeaderLabels(["VERSION", "BENCHMARK", "AMOUNT (INR)", "OM", "PM", "CTT"])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.hist_table.verticalHeader().setVisible(False)
        self.hist_table.setAlternatingRowColors(True)
        hist_card.content_layout.addWidget(self.hist_table)
        layout.addWidget(hist_card)
        layout.addStretch(1)

    def _init_risks_tab(self) -> None:
        layout = QVBoxLayout(self.tab_risks)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Qualitative Risk Register & Assertion Mapping (SA 315)"))
        hdr.addStretch()
        btn = QPushButton("+ New Audit Risk")
        btn.clicked.connect(self._on_new_risk_clicked)
        hdr.addWidget(btn)
        layout.addLayout(hdr)

        card = CardWidget()
        self.risks_table = QTableWidget()
        self.risks_table.setColumnCount(8)
        self.risks_table.setHorizontalHeaderLabels(["CODE", "TITLE", "CATEGORY", "ASSERTIONS", "INHERENT", "CONTROL", "DERIVED RoMM", "SIG"])
        self.risks_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.risks_table.verticalHeader().setVisible(False)
        self.risks_table.setAlternatingRowColors(True)

        self.risks_empty = EmptyStateWidget("No audit risks recorded", "Log qualitative risks mapped to assertions per SA 315.", "+ New Audit Risk", self._on_new_risk_clicked)
        card.content_layout.addWidget(self.risks_table)
        card.content_layout.addWidget(self.risks_empty)
        layout.addWidget(card)
        layout.addStretch(1)

    def _init_procedures_tab(self) -> None:
        layout = QVBoxLayout(self.tab_procs)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Structured Audit Procedures Execution Hub"))
        hdr.addStretch()
        btn = QPushButton("+ New Procedure")
        btn.clicked.connect(self._on_new_proc_clicked)
        hdr.addWidget(btn)
        layout.addLayout(hdr)

        card = CardWidget()
        self.procs_table = QTableWidget()
        self.procs_table.setColumnCount(6)
        self.procs_table.setHorizontalHeaderLabels(["CODE", "OBJECTIVE", "TYPE", "STATUS", "PREPARER", "REVIEWER"])
        self.procs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.procs_table.verticalHeader().setVisible(False)
        self.procs_table.setAlternatingRowColors(True)

        self.procs_empty = EmptyStateWidget("No audit procedures scheduled", "Create substantive tests or analytical procedures.", "+ New Procedure", self._on_new_proc_clicked)
        card.content_layout.addWidget(self.procs_table)
        card.content_layout.addWidget(self.procs_empty)
        layout.addWidget(card)
        layout.addStretch(1)

    def _init_findings_tab(self) -> None:
        layout = QVBoxLayout(self.tab_findings)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(QLabel("Unified Findings Directory Across All Sources"))
        hdr.addStretch()
        btn = QPushButton("+ Log Finding")
        btn.clicked.connect(self._on_new_finding_clicked)
        hdr.addWidget(btn)
        layout.addLayout(hdr)

        card = CardWidget()
        self.findings_table = QTableWidget()
        self.findings_table.setColumnCount(7)
        self.findings_table.setHorizontalHeaderLabels(["SOURCE", "TITLE", "SEVERITY", "IMPACT (₹)", "ACCOUNT", "STATUS", "GRAPH"])
        self.findings_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.findings_table.verticalHeader().setVisible(False)
        self.findings_table.setAlternatingRowColors(True)

        self.findings_empty = EmptyStateWidget("No audit findings logged", "Promote flagged exceptions or log audit findings.", "+ Log Finding", self._on_new_finding_clicked)
        card.content_layout.addWidget(self.findings_table)
        card.content_layout.addWidget(self.findings_empty)
        layout.addWidget(card)
        layout.addStretch(1)

    def set_engagement(self, engagement: Any) -> None:
        if isinstance(engagement, Engagement):
            self.current_engagement = engagement
        elif engagement:
            try:
                self.current_engagement = self.engagement_service.get_engagement(str(engagement))
            except Exception:
                self.current_engagement = None
        else:
            self.current_engagement = None
        self.refresh()

    set_active_engagement = set_engagement


    def refresh(self) -> None:
        if not self.current_engagement or not self.planning_service:
            for c in (self.card_overall, self.card_performance, self.card_trivial):
                c.set_value("₹ 0.00")
            for t, e in ((self.risks_table, self.risks_empty), (self.procs_table, self.procs_empty), (self.findings_table, self.findings_empty)):
                t.setVisible(False)
                e.setVisible(True)
            self.hist_table.setRowCount(0)
            return

        mat_fn = getattr(self.planning_service, "get_latest_materiality", None)
        mat = mat_fn(self.current_engagement.id) if mat_fn else None
        if mat:
            self.current_materiality = mat
            self.card_overall.set_value(mat.overall_materiality.formatted if hasattr(mat.overall_materiality, "formatted") else f"₹ {mat.overall_materiality:,.2f}")
            self.card_performance.set_value(mat.performance_materiality.formatted if hasattr(mat.performance_materiality, "formatted") else f"₹ {mat.performance_materiality:,.2f}")
            self.card_trivial.set_value(mat.clearly_trivial_threshold.formatted if hasattr(mat.clearly_trivial_threshold, "formatted") else f"₹ {mat.clearly_trivial_threshold:,.2f}")

        hist_fn = getattr(self.planning_service, "list_materiality_history", None)
        history = hist_fn(self.current_engagement.id) if hist_fn else ([mat] if mat else [])
        self.hist_table.setRowCount(0)
        for r, m in enumerate(history):
            self.hist_table.insertRow(r)
            self.hist_table.setItem(r, 0, QTableWidgetItem(f"v{m.version}"))
            self.hist_table.setItem(r, 1, QTableWidgetItem(m.benchmark_type.value))
            self.hist_table.setItem(r, 2, QTableWidgetItem(m.benchmark_amount.formatted if hasattr(m.benchmark_amount, "formatted") else f"₹ {m.benchmark_amount:,.2f}"))
            self.hist_table.setItem(r, 3, QTableWidgetItem(m.overall_materiality.formatted if hasattr(m.overall_materiality, "formatted") else f"₹ {m.overall_materiality:,.2f}"))
            self.hist_table.setItem(r, 4, QTableWidgetItem(m.performance_materiality.formatted if hasattr(m.performance_materiality, "formatted") else f"₹ {m.performance_materiality:,.2f}"))
            self.hist_table.setItem(r, 5, QTableWidgetItem(m.clearly_trivial_threshold.formatted if hasattr(m.clearly_trivial_threshold, "formatted") else f"₹ {m.clearly_trivial_threshold:,.2f}"))

        r_fn = getattr(self.planning_service, "list_risks", None) or getattr(self.planning_service, "list_risks_for_engagement", None)
        risks = r_fn(self.current_engagement.id) if r_fn else []
        self._populate_table(self.risks_table, self.risks_empty, len(risks))
        for r, rk in enumerate(risks):
            self.risks_table.setItem(r, 0, QTableWidgetItem(rk.risk_code))
            self.risks_table.setItem(r, 1, QTableWidgetItem(getattr(rk, "title", rk.risk_code)))
            self.risks_table.setItem(r, 2, QTableWidgetItem(rk.category))
            as_str = ", ".join(a.value for a in rk.assertions) if hasattr(rk, "assertions") else rk.assertion.value
            self.risks_table.setItem(r, 3, QTableWidgetItem(as_str))
            self.risks_table.setItem(r, 4, QTableWidgetItem(f"● {rk.inherent_risk.value}"))
            self.risks_table.setItem(r, 5, QTableWidgetItem(f"● {rk.control_risk.value}"))
            romm = rk.derived_romm.value if hasattr(rk, "derived_romm") else rk.severity.value
            self.risks_table.setItem(r, 6, QTableWidgetItem(f"● {romm}"))
            self.risks_table.setItem(r, 7, QTableWidgetItem("YES" if getattr(rk, "is_significant_risk", False) else "NO"))

        p_fn = getattr(self.planning_service, "list_procedures", None) or getattr(self.planning_service, "list_procedures_for_engagement", None)
        procs = p_fn(self.current_engagement.id) if p_fn else []
        self._populate_table(self.procs_table, self.procs_empty, len(procs))
        for r, p in enumerate(procs):
            self.procs_table.setItem(r, 0, QTableWidgetItem(p.procedure_code))
            self.procs_table.setItem(r, 1, QTableWidgetItem(p.objective))
            self.procs_table.setItem(r, 2, QTableWidgetItem(p.procedure_type))
            self.procs_table.setItem(r, 3, QTableWidgetItem(f"● {p.status.value}"))
            self.procs_table.setItem(r, 4, QTableWidgetItem(p.preparer or "—"))
            self.procs_table.setItem(r, 5, QTableWidgetItem(p.reviewer or "—"))

        f_fn = getattr(self.planning_service, "list_findings", None) or getattr(self.planning_service, "list_findings_for_engagement", None)
        findings = f_fn(self.current_engagement.id) if f_fn else []
        self._populate_table(self.findings_table, self.findings_empty, len(findings))
        for r, f in enumerate(findings):
            src_val = f.source.value if hasattr(f.source, "value") else str(f.source)
            self.findings_table.setItem(r, 0, QTableWidgetItem(src_val.upper()))
            self.findings_table.setItem(r, 1, QTableWidgetItem(f.title))
            self.findings_table.setItem(r, 2, QTableWidgetItem(f"● {f.severity.value}"))
            amt = f.monetary_amount.formatted if hasattr(f, "monetary_amount") and hasattr(f.monetary_amount, "formatted") else f"₹ {getattr(f, 'monetary_amount', 0):,.2f}"
            self.findings_table.setItem(r, 3, QTableWidgetItem(amt))
            self.findings_table.setItem(r, 4, QTableWidgetItem(f.affected_account or "—"))
            self.findings_table.setItem(r, 5, QTableWidgetItem(f"● {f.status.value}"))
            bg = QPushButton("Graph")
            bg.clicked.connect(lambda _, fid=f.id: self._open_traceability(fid))
            self.findings_table.setCellWidget(r, 6, bg)

    def _populate_table(self, table: QTableWidget, empty: QWidget, count: int) -> None:
        table.setVisible(count > 0)
        empty.setVisible(count == 0)
        table.setRowCount(count)

    def _open_traceability(self, finding_id: str) -> None:
        if self.current_engagement and self.traceability_service:
            TraceabilityDialog(self.traceability_service, self.current_engagement.id, finding_id, parent=self).exec()

    def _on_calculate_materiality(self) -> None:
        if not self.current_engagement or not self.planning_service:
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
        dto = SetMaterialityDTO(engagement_id=self.current_engagement.id, benchmark_type=self.bm_combo.currentData(), benchmark_amount_paise=paise)
        try:
            mat = self.planning_service.set_materiality(dto)
            QMessageBox.information(self, "SA 320 Calculated", f"Materiality v{mat.version}:\nOM: {mat.overall_materiality.formatted}\nPM: {mat.performance_materiality.formatted}\nCTT: {mat.clearly_trivial_threshold.formatted}")
            self.refresh()
            self.matrix_changed.emit()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"Failed: {ex}")

    def _on_new_risk_clicked(self) -> None:
        if self.current_engagement and self.planning_service and RiskDialog(self.planning_service, engagement=self.current_engagement, parent=self).exec() == RiskDialog.DialogCode.Accepted:
            self.refresh()
            self.matrix_changed.emit()

    def _on_new_proc_clicked(self) -> None:
        if self.current_engagement and self.planning_service:
            risks = self.planning_service.list_risks(self.current_engagement.id)
            if ProcedureDialog(self.planning_service, engagement=self.current_engagement, risks=risks, parent=self).exec() == ProcedureDialog.DialogCode.Accepted:
                self.refresh()
                self.matrix_changed.emit()

    def _on_new_finding_clicked(self) -> None:
        if self.current_engagement and self.planning_service:
            procs = self.planning_service.list_procedures(self.current_engagement.id)
            risks = self.planning_service.list_risks(self.current_engagement.id)
            if FindingDialog(self.planning_service, engagement=self.current_engagement, procedures=procs, risks=risks, parent=self).exec() == FindingDialog.DialogCode.Accepted:
                self.refresh()
                self.matrix_changed.emit()
