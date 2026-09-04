"""CA-oriented interactive Audit Matrix, Assertion Coverage, and Completeness Score Dialog."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.core_audit_dtos import (
    CalculateAuditCompletenessDTO,
    GenerateAssertionCoverageDTO,
)
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.core_audit_service import CoreAuditService
from finauditpro.domain.audit_matrix_entities import ProcedureStatusEnum, RiskSeverityEnum


class AuditMatrixViewDialog(QDialog):
    """Complete Audit Matrix, Assertion Coverage Matrix, and Audit Completeness Score workspace."""

    def __init__(
        self,
        matrix_service: AuditMatrixService,
        core_service: CoreAuditService,
        engagement_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.matrix_service = matrix_service
        self.core_service = core_service
        self.engagement_id = engagement_id

        self.setWindowTitle("Core Audit Matrix & SA 330 Quality Control Workspace")
        self.resize(1180, 720)
        self.setModal(True)

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.tabs = QTabWidget()

        # --- Tab 1: Complete Audit Matrix ---
        matrix_tab = QWidget()
        m_layout = QVBoxLayout(matrix_tab)

        m_toolbar = QHBoxLayout()
        m_toolbar.addWidget(QLabel("Filter Matrix View:"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(
            [
                "All Audit Records",
                "Open / Incomplete",
                "Exceptions Only",
                "High Risk Items",
                "Missing Evidence",
                "Missing Conclusion",
                "Unreviewed Work",
            ]
        )
        self.filter_combo.currentIndexChanged.connect(self._apply_matrix_filter)
        m_toolbar.addWidget(self.filter_combo, stretch=1)
        m_toolbar.addStretch(2)
        m_layout.addLayout(m_toolbar)

        self.matrix_table = QTableWidget()
        self.matrix_table.setColumnCount(8)
        self.matrix_table.setHorizontalHeaderLabels(
            ["RISK", "ASSERTION", "PROCEDURE", "TYPE", "STATUS", "RESULT", "EVIDENCE", "CONCLUSION"]
        )
        self.matrix_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in (0, 1, 3, 4, 5, 6, 7):
            self.matrix_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.matrix_table.verticalHeader().setVisible(False)
        self.matrix_table.setAlternatingRowColors(True)
        m_layout.addWidget(self.matrix_table)
        self.tabs.addTab(matrix_tab, "Complete Audit Matrix")

        # --- Tab 2: Assertion Coverage Matrix ---
        cov_tab = QWidget()
        c_layout = QVBoxLayout(cov_tab)

        self.cov_stats_lbl = QLabel("Evaluating assertion coverage...")
        self.cov_stats_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 700; color: #1E293B; padding: 6px 12px; background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px;"
        )
        c_layout.addWidget(self.cov_stats_lbl)

        self.cov_table = QTableWidget()
        self.cov_table.setColumnCount(6)
        self.cov_table.setHorizontalHeaderLabels(
            ["AUDIT AREA", "ASSERTION", "RISKS", "PROCEDURES", "COVERED?", "GAP ANALYSIS"]
        )
        self.cov_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for c in (0, 1, 2, 3, 4):
            self.cov_table.horizontalHeader().setSectionResizeMode(
                c, QHeaderView.ResizeMode.ResizeToContents
            )
        self.cov_table.verticalHeader().setVisible(False)
        self.cov_table.setAlternatingRowColors(True)
        c_layout.addWidget(self.cov_table)
        self.tabs.addTab(cov_tab, "Assertion Coverage Matrix")

        # --- Tab 3: Completeness Score & Orphan Detector ---
        comp_tab = QWidget()
        comp_layout = QVBoxLayout(comp_tab)

        self.comp_banner_lbl = QLabel("Computing audit completeness score...")
        self.comp_banner_lbl.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #0F172A; padding: 10px 14px; background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 6px;"
        )
        comp_layout.addWidget(self.comp_banner_lbl)

        self.orphan_table = QTableWidget()
        self.orphan_table.setColumnCount(3)
        self.orphan_table.setHorizontalHeaderLabels(
            ["QUALITY GATE CHECK", "SEVERITY", "DETAILS / ORPHANED ITEMS"]
        )
        self.orphan_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.orphan_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.orphan_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        self.orphan_table.verticalHeader().setVisible(False)
        self.orphan_table.setAlternatingRowColors(True)
        comp_layout.addWidget(self.orphan_table)
        self.tabs.addTab(comp_tab, "Audit Completeness & Orphan Detector")

        layout.addWidget(self.tabs, stretch=1)

        bottom = QHBoxLayout()
        bottom.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _load_data(self) -> None:
        self.risks = self.matrix_service.list_risks_for_engagement(self.engagement_id)
        self.procs = self.matrix_service.list_procedures_for_engagement(self.engagement_id)
        self.evidences = self.matrix_service.list_evidence_for_engagement(self.engagement_id)

        self._render_matrix(self.procs)
        self._render_coverage_matrix()
        self._render_completeness_report()

    def _render_matrix(self, procs: list[Any]) -> None:
        risk_map = {r.id: r for r in self.risks}
        self.matrix_table.setRowCount(len(procs))
        for row, p in enumerate(procs):
            linked_r = [risk_map[rid].risk_code for rid in p.linked_risk_ids if rid in risk_map]
            self.matrix_table.setItem(row, 0, QTableWidgetItem(", ".join(linked_r) or "—"))
            self.matrix_table.setItem(
                row,
                1,
                QTableWidgetItem(
                    p.assertion.value if hasattr(p.assertion, "value") else str(p.assertion)
                ),
            )
            self.matrix_table.setItem(
                row, 2, QTableWidgetItem(f"[{p.procedure_code}] {p.objective}")
            )
            self.matrix_table.setItem(row, 3, QTableWidgetItem(p.procedure_type))

            st_item = QTableWidgetItem(
                p.status.value if hasattr(p.status, "value") else str(p.status)
            )
            if p.status == ProcedureStatusEnum.COMPLETED:
                st_item.setForeground(Qt.GlobalColor.darkGreen)
            self.matrix_table.setItem(row, 4, st_item)

            self.matrix_table.setItem(row, 5, QTableWidgetItem(p.result_summary or "—"))
            ev_count = len([e for e in self.evidences if e.procedure_id == p.id])
            self.matrix_table.setItem(
                row, 6, QTableWidgetItem(f"{ev_count} file(s)" if ev_count else "None")
            )

            conc_item = QTableWidgetItem(p.conclusion or "Pending")
            if p.conclusion == "PASS":
                conc_item.setForeground(Qt.GlobalColor.darkGreen)
            elif p.conclusion in ("FAIL", "EXCEPTION"):
                conc_item.setForeground(Qt.GlobalColor.red)
            self.matrix_table.setItem(row, 7, conc_item)

    def _apply_matrix_filter(self) -> None:
        idx = self.filter_combo.currentIndex()
        filtered = []
        for p in self.procs:
            if (
                idx == 0
                or (idx == 1 and p.status != ProcedureStatusEnum.COMPLETED)
                or (idx == 2 and p.conclusion in ("FAIL", "EXCEPTION"))
                or (
                    idx == 3
                    and any(
                        r.severity == RiskSeverityEnum.HIGH
                        for r in self.risks
                        if r.id in p.linked_risk_ids
                    )
                )
                or (idx == 4 and not any(e.procedure_id == p.id for e in self.evidences))
                or (idx == 5 and not p.conclusion)
                or (idx == 6 and not p.reviewer)
            ):  # All
                filtered.append(p)
        self._render_matrix(filtered)

    def _render_coverage_matrix(self) -> None:
        rep = self.core_service.generate_assertion_coverage_matrix(
            GenerateAssertionCoverageDTO(engagement_id=self.engagement_id)
        )
        self.cov_stats_lbl.setText(
            f"Assertion Coverage: {rep.coverage_percentage}% | Total Areas Evaluated: {rep.total_matrix_lines} | "
            f"Covered: {rep.covered_lines} | Gaps Identified: {rep.gap_count}"
        )
        self.cov_table.setRowCount(len(rep.lines))
        for row, l in enumerate(rep.lines):
            self.cov_table.setItem(row, 0, QTableWidgetItem(l.account_or_area))
            self.cov_table.setItem(row, 1, QTableWidgetItem(l.assertion.value))
            self.cov_table.setItem(row, 2, QTableWidgetItem(", ".join(l.linked_risk_codes) or "—"))
            self.cov_table.setItem(
                row, 3, QTableWidgetItem(", ".join(l.linked_procedure_codes) or "—")
            )

            cov_item = QTableWidgetItem("YES" if l.is_covered else "NO")
            cov_item.setForeground(Qt.GlobalColor.darkGreen if l.is_covered else Qt.GlobalColor.red)
            self.cov_table.setItem(row, 4, cov_item)
            self.cov_table.setItem(row, 5, QTableWidgetItem(l.gap_reason or "Fully Covered"))

    def _render_completeness_report(self) -> None:
        rep = self.core_service.calculate_audit_completeness(
            CalculateAuditCompletenessDTO(engagement_id=self.engagement_id)
        )
        status_text = (
            "READY FOR SIGN-OFF"
            if rep.is_ready_for_finalization
            else "ACTION REQUIRED (INCOMPLETE)"
        )
        self.comp_banner_lbl.setText(
            f"Deterministic Audit Completeness Score: {rep.composite_completeness_score}/100 | Quality Gate: {status_text}\n"
            f"Risks: {rep.risk_coverage_pct}% | Procedures: {rep.procedure_execution_pct}% | Evidence: {rep.evidence_coverage_pct}% | "
            f"Exceptions: {rep.exception_resolution_pct}% | Misstatements: {rep.misstatement_resolution_pct}% | Review: {rep.review_completion_pct}%"
        )
        checks = [
            (
                "Orphaned Risks (No Procedures)",
                "High",
                ", ".join(rep.orphaned_risks) if rep.orphaned_risks else "None (All Covered)",
            ),
            (
                "Orphaned Procedures (No Linked Risk)",
                "Medium",
                ", ".join(rep.orphaned_procedures) if rep.orphaned_procedures else "None",
            ),
            (
                "Procedures Missing Evidence",
                "High",
                ", ".join(rep.procedures_missing_evidence)
                if rep.procedures_missing_evidence
                else "None",
            ),
            (
                "Procedures Missing Conclusion",
                "High",
                ", ".join(rep.procedures_missing_conclusion)
                if rep.procedures_missing_conclusion
                else "None",
            ),
            (
                "Unresolved Exceptions",
                "High",
                ", ".join(rep.unresolved_exceptions) if rep.unresolved_exceptions else "None",
            ),
            (
                "Uncorrected Misstatements",
                "Medium",
                ", ".join(rep.unresolved_misstatements) if rep.unresolved_misstatements else "None",
            ),
        ]
        self.orphan_table.setRowCount(len(checks))
        for row, (check, sev, details) in enumerate(checks):
            self.orphan_table.setItem(row, 0, QTableWidgetItem(check))
            sev_item = QTableWidgetItem(sev)
            if sev == "High":
                sev_item.setForeground(Qt.GlobalColor.red)
            self.orphan_table.setItem(row, 1, sev_item)
            self.orphan_table.setItem(row, 2, QTableWidgetItem(details))
