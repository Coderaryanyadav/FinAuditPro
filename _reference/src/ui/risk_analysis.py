"""
SA 315 & SA 320 Audit Risk Assessment, Performance Materiality & Heatmap Workspace for FinAuditPro.
Provides SA 320 Overall & Performance Materiality Computation Worksheet, 
3x3 Risk Heatmap Matrix (Likelihood x Impact), and SA 315 Deduplicated Risk Findings Register.
"""

import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QScrollArea, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QComboBox, QLineEdit, QFormLayout,
                               QTabWidget, QGridLayout, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Finding, AuditProject, Risk, MaterialityCalculation
from database.repositories.risk_repo import RiskRepository
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.risk_service import RiskService
from services.finding_service import FindingService
from services.working_paper_service import WorkingPaperService
from .styles import apply_shadow, EmptyStateWidget, ErrorStateWidget, LoadingStateWidget
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

class RiskAnalysisWidget(QFrame):
    """SA 315 & SA 320 Audit Risk Assessment, Materiality Calculator & Risk Heatmap Workspace."""

    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setObjectName("appBg")
        self._active_engagement_id = None
        self._active_project_id = None
        self._heatmap_filter = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Bar
        header = QFrame()
        header.setFixedHeight(64)
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        header.setObjectName("contentHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("Audit Risk Assessment & Materiality Workspace")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px; border: none;")
        subtitle = QLabel("SA 315 Risk Identification, Performance Materiality (SA 320) & 3x3 Risk Heatmap Matrix.")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        h_layout.addLayout(title_v)

        h_layout.addStretch()

        btn_calc = QPushButton("⚡ Recalculate SA 320 Materiality")
        btn_calc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_calc.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 12px;
                font-weight: 700;
                border-radius: 6px;
                padding: 7px 16px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        btn_calc.clicked.connect(self.calculate_materiality)
        h_layout.addWidget(btn_calc)

        main_layout.addWidget(header)

        # 2. Summary Metric Strip Row
        self.summary_strip = QFrame()
        self.summary_strip.setFixedHeight(54)
        self.summary_strip.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        s_layout = QHBoxLayout(self.summary_strip)
        s_layout.setContentsMargins(24, 0, 24, 0)
        s_layout.setSpacing(16)

        self.lbl_total_risks = self._create_metric_badge("TOTAL RISKS IDENTIFIED", "0 Risks", "#0284c7", "#e0f2fe")
        self.lbl_high_risks = self._create_metric_badge("HIGH SEVERITY RISKS", "0 High", "#dc2626", "#fee2e2")
        self.lbl_exceed_mat = self._create_metric_badge("EXCEEDING MATERIALITY", "0 Findings", "#d97706", "#fef3c7")
        self.lbl_overall_rating = self._create_metric_badge("OVERALL RISK RATING", "● MODERATE RISK", "#047857", "#dcfce7")

        for b in [self.lbl_total_risks, self.lbl_high_risks, self.lbl_exceed_mat, self.lbl_overall_rating]:
            s_layout.addWidget(b)
        s_layout.addStretch()
        main_layout.addWidget(self.summary_strip)

        # 3. Main Workspace Vault (3 Tabs)
        workspace = QWidget()
        ws_layout = QVBoxLayout(workspace)
        ws_layout.setContentsMargins(24, 16, 24, 24)
        ws_layout.setSpacing(12)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #e1e8f4; background: #ffffff; border-radius: 10px; }
            QTabBar::tab { background: #f8fafc; color: #64748b; padding: 8px 18px; font-weight: 700; font-size: 12px; border-top-left-radius: 6px; border-top-right-radius: 6px; margin-right: 4px; border: 1px solid #e1e8f4; }
            QTabBar::tab:selected { background: #0284c7; color: #ffffff; border-color: #0284c7; }
        """)

        self.tabs.addTab(self._create_risk_register_tab(), "SA 315 Audit Risk Register & Heatmap")
        self.tabs.addTab(self._create_materiality_tab(), "SA 320 Materiality Computation Worksheet")
        self.tabs.addTab(self._create_procedures_tab(), "SA 330 Risk Mitigation Audit Strategy")

        ws_layout.addWidget(self.tabs)
        main_layout.addWidget(workspace, 1)

        self.calculate_materiality()
        self.load_findings()

    @property
    def active_engagement_id(self):
        return self._active_engagement_id

    @active_engagement_id.setter
    def active_engagement_id(self, val):
        self._active_engagement_id = val

    @property
    def active_project_id(self):
        return self._active_project_id

    @active_project_id.setter
    def active_project_id(self, val):
        self._active_project_id = val

    def refresh_data(self):
        self.load_findings()
        self.calculate_materiality()

    def _create_metric_badge(self, label: str, val: str, fg: str, bg: str) -> QFrame:
        box = QFrame()
        box.setStyleSheet(f"background: {bg}; border: 1px solid {fg}40; border-radius: 6px; padding: 4px 12px;")
        bl = QHBoxLayout(box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(6)

        l_lbl = QLabel(label)
        l_lbl.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {fg}; border: none;")
        v_lbl = QLabel(val)
        v_lbl.setObjectName("valLbl")
        v_lbl.setStyleSheet(f"font-size: 12px; font-weight: 800; color: {fg}; border: none;")

        bl.addWidget(l_lbl)
        bl.addWidget(v_lbl)
        return box

    def _create_risk_register_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        w_layout.setSpacing(14)

        # Top Row: 3x3 Heatmap Grid + Filter Bar
        top_split = QHBoxLayout()
        top_split.setSpacing(16)

        # 3x3 Risk Heatmap Container
        heatmap_frame = QFrame()
        heatmap_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e1e8f4; border-radius: 8px; padding: 10px;")
        hm_layout = QVBoxLayout(heatmap_frame)
        hm_layout.setContentsMargins(8, 8, 8, 8)
        hm_layout.setSpacing(6)

        hm_title = QLabel("SA 315 RISK HEATMAP MATRIX (Likelihood x Financial Impact)")
        hm_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #0f172a; border: none;")
        hm_layout.addWidget(hm_title)

        grid = QGridLayout()
        grid.setSpacing(6)

        # Grid cells: High/Med/Low
        self.heatmap_cells = {}
        matrix_defs = [
            ("High", "High", "#fee2e2", "#dc2626", 0, 0),
            ("High", "Medium", "#fef3c7", "#d97706", 0, 1),
            ("High", "Low", "#fef3c7", "#d97706", 0, 2),
            ("Medium", "High", "#fef3c7", "#d97706", 1, 0),
            ("Medium", "Medium", "#e0f2fe", "#0284c7", 1, 1),
            ("Medium", "Low", "#dcfce7", "#047857", 1, 2),
            ("Low", "High", "#e0f2fe", "#0284c7", 2, 0),
            ("Low", "Medium", "#dcfce7", "#047857", 2, 1),
            ("Low", "Low", "#dcfce7", "#047857", 2, 2),
        ]

        for lh, imp, bg, fg, r, c in matrix_defs:
            btn = QPushButton(f"{lh[0]}L x {imp[0]}I\n0 Risks")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {bg};
                    color: {fg};
                    font-size: 11px;
                    font-weight: 700;
                    border: 1px solid {fg}40;
                    border-radius: 6px;
                    padding: 8px;
                    text-align: center;
                }}
                QPushButton:hover {{ border-width: 2px; }}
            """)
            btn.clicked.connect(lambda checked=False, l=lh, i=imp: self._filter_by_heatmap(l, i))
            grid.addWidget(btn, r, c)
            self.heatmap_cells[(lh, imp)] = btn

        hm_layout.addLayout(grid)
        top_split.addWidget(heatmap_frame, 5)

        # Heatmap Filter Info & Instructions
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e1e8f4; border-radius: 8px; padding: 12px;")
        if_layout = QVBoxLayout(info_frame)
        if_layout.setSpacing(8)

        info_title = QLabel("Heatmap Selection & Audit Guidance")
        info_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #0f172a;")
        info_desc = QLabel("Click any cell in the 3x3 Risk Heatmap Matrix to filter the deduplicated Risk Findings Register below. High-severity and material items require mandatory substantive testing under ICAI SA 330.")
        info_desc.setWordWrap(True)
        info_desc.setStyleSheet("font-size: 11px; color: #475569; line-height: 1.4;")

        self.lbl_active_filter = QLabel("Active Filter: Showing All Risk Findings")
        self.lbl_active_filter.setStyleSheet("font-size: 11px; font-weight: 700; color: #0284c7; background: #e0f2fe; padding: 6px 10px; border-radius: 4px;")

        btn_reset = QPushButton("Reset Filter")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("background: #f1f5f9; color: #475569; font-size: 11px; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 10px;")
        btn_reset.clicked.connect(self._reset_heatmap_filter)

        if_layout.addWidget(info_title)
        if_layout.addWidget(info_desc)
        if_layout.addWidget(self.lbl_active_filter)
        if_layout.addWidget(btn_reset)
        if_layout.addStretch()

        top_split.addWidget(info_frame, 4)
        w_layout.addLayout(top_split)

        # Bottom Section: Search & Deduplicated Risk Table
        search_r = QHBoxLayout()
        self.risk_search = QLineEdit()
        self.risk_search.setPlaceholderText("Search risk findings by title, category, or financial impact...")
        self.risk_search.setStyleSheet("padding: 7px 12px; border: 1px solid #e1e8f4; border-radius: 6px; background-color: #ffffff; color: #0f172a; font-size: 12px;")
        self.risk_search.textChanged.connect(self._filter_table_search)
        search_r.addWidget(self.risk_search)
        w_layout.addLayout(search_r)

        self.table = QTableWidget(0, 6)
        self.table.cellClicked.connect(self._on_cell_clicked)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setHorizontalHeaderLabels(["RISK / ISSUE TITLE", "SEVERITY", "FINANCIAL EXPOSURE", "SA 320 MATERIALITY STATUS", "RECOMMENDED AUDIT RESPONSE", "WORKING PAPER LINK"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.table.setColumnWidth(0, 220)
        self.table.setColumnWidth(1, 110)
        self.table.setColumnWidth(2, 140)
        self.table.setColumnWidth(3, 190)
        self.table.setColumnWidth(5, 175)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { border: 1px solid #e1e8f4; gridline-color: #f0f6ff; background: #ffffff; border-radius: 8px; font-size: 12px; color: #0f172a; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 700; font-size: 11px; padding: 8px; border: none; border-bottom: 1px solid #e1e8f4; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f0f6ff; color: #0f172a; }
        """)

        w_layout.addWidget(self.table)
        return widget

    def _create_materiality_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        w_layout.setSpacing(14)

        mat_frame = QFrame()
        mat_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 10px; padding: 16px;")
        mat_layout = QVBoxLayout(mat_frame)
        mat_layout.setSpacing(14)

        m_title = QLabel("SA 320 MATERIALITY COMPUTATION WORKSHEET")
        m_title.setStyleSheet("font-size: 12px; font-weight: 800; color: #0284c7; border-bottom: 1px solid #e1e8f4; padding-bottom: 8px; letter-spacing: 0.5px;")
        mat_layout.addWidget(m_title)

        inputs_h = QHBoxLayout()
        inputs_h.setSpacing(20)

        form_frame = QFrame()
        f_layout = QFormLayout(form_frame)
        f_layout.setSpacing(12)

        self.benchmark_combo = QComboBox()
        self.benchmark_combo.addItems([
            "Revenue from Operations (1.0%)",
            "Profit Before Tax (5.0%)",
            "Total Assets (0.5%)",
            "Equity Shareholders' Funds (1.0%)"
        ])
        self.benchmark_combo.setStyleSheet("padding: 8px; border: 1px solid #e1e8f4; border-radius: 6px; background: #ffffff; color: #0f172a; font-size: 12px;")
        self.benchmark_combo.currentIndexChanged.connect(self.calculate_materiality)

        self.base_amt_input = QLineEdit("32000000.00")
        self.base_amt_input.setStyleSheet("padding: 8px; border: 1px solid #e1e8f4; border-radius: 6px; background: #ffffff; font-weight: 700; color: #0f172a; font-size: 12px;")
        self.base_amt_input.textChanged.connect(self.calculate_materiality)

        self.lbl_input_err = QLabel("")
        self.lbl_input_err.setStyleSheet("color: #dc2626; font-size: 11px; font-weight: 600;")
        self.lbl_input_err.hide()

        f_layout.addRow(QLabel("<b style='color:#0f172a;'>Benchmark Basis:</b>"), self.benchmark_combo)
        f_layout.addRow(QLabel("<b style='color:#0f172a;'>Benchmark Base Amount (₹):</b>"), self.base_amt_input)
        f_layout.addRow("", self.lbl_input_err)
        inputs_h.addWidget(form_frame, 5)

        res_frame = QFrame()
        res_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e1e8f4; border-radius: 8px; padding: 14px;")
        r_layout = QVBoxLayout(res_frame)
        r_layout.setSpacing(8)

        self.lbl_overall_mat = QLabel("Overall Materiality (OM): ₹ 320,000.00")
        self.lbl_overall_mat.setStyleSheet("font-size: 14px; font-weight: 800; color: #0f172a;")

        self.lbl_perf_mat = QLabel("Performance Materiality (PM @ 75%): ₹ 240,000.00")
        self.lbl_perf_mat.setStyleSheet("font-size: 13px; font-weight: 700; color: #0284c7;")

        self.lbl_de_minimis = QLabel("Tolerable Misstatement Limit (5%): ₹ 16,000.00")
        self.lbl_de_minimis.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748b;")

        r_layout.addWidget(self.lbl_overall_mat)
        r_layout.addWidget(self.lbl_perf_mat)
        r_layout.addWidget(self.lbl_de_minimis)
        inputs_h.addWidget(res_frame, 5)

        mat_layout.addLayout(inputs_h)
        w_layout.addWidget(mat_frame)
        w_layout.addStretch()
        return widget

    def _create_procedures_tab(self) -> QWidget:
        widget = QWidget()
        w_layout = QVBoxLayout(widget)
        w_layout.setContentsMargins(16, 16, 16, 16)
        w_layout.setSpacing(12)

        title = QLabel("SA 330 AUDIT MITIGATION PROCEDURES & STRATEGY")
        title.setStyleSheet("font-size: 12px; font-weight: 800; color: #0f172a;")
        w_layout.addWidget(title)

        table = QTableWidget(4, 4)
        table.setHorizontalHeaderLabels(["RISK CATEGORY", "SA 315 INHERENT RISK", "ICAI SA 330 RECOMMENDED STRATEGY", "VERIFICATION STATUS"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.setColumnWidth(0, 160)
        table.setColumnWidth(1, 140)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet("""
            QTableWidget { border: 1px solid #e1e8f4; gridline-color: #f0f6ff; background: #ffffff; border-radius: 8px; font-size: 12px; color: #0f172a; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 700; font-size: 11px; padding: 8px; border: none; border-bottom: 1px solid #e1e8f4; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #f0f6ff; color: #0f172a; }
        """)

        rows = [
            ("Revenue Recognition & Cut-off", "High Inherent Risk", "Substantive analytical testing & 100% sample vouching of sales invoices around year-end", "✓ Strategy Approved"),
            ("Vendor Payables & PAN", "Medium Inherent Risk", "External balance confirmation & 206AA higher TDS disallowance testing", "✓ Strategy Approved"),
            ("Inventory Valuation", "Medium Inherent Risk", "Physical inventory count observation & net realizable value (NRV) test", "✓ Strategy Approved"),
            ("Related Party Transactions", "High Inherent Risk", "Section 188 Audit Committee approval review & transfer pricing verification", "✓ Strategy Approved"),
        ]

        for r, (cat, inh, strat, stat) in enumerate(rows):
            table.setItem(r, 0, QTableWidgetItem(cat))
            table.setItem(r, 1, QTableWidgetItem(inh))
            table.setItem(r, 2, QTableWidgetItem(strat))
            table.setItem(r, 3, QTableWidgetItem(stat))

        w_layout.addWidget(table)
        return widget

    def calculate_materiality(self):
        self.lbl_input_err.hide()
        try:
            val_str = self.base_amt_input.text().replace("₹", "").replace(",", "").strip()
            if not val_str: return

            base_val = float(val_str)
            if base_val < 0:
                self.lbl_input_err.setText("Please enter a positive benchmark amount")
                self.lbl_input_err.show()
                return

            combo_text = self.benchmark_combo.currentText()
            if "5.0%" in combo_text: pct = 0.05
            elif "0.5%" in combo_text: pct = 0.005
            else: pct = 0.01

            om = base_val * pct
            pm = om * 0.75
            tms = om * 0.05

            self.lbl_overall_mat.setText(f"Overall Materiality (OM): ₹ {om:,.2f}")
            self.lbl_perf_mat.setText(f"Performance Materiality (PM @ 75%): ₹ {pm:,.2f}")
            self.lbl_de_minimis.setText(f"Tolerable Misstatement Limit (5%): ₹ {tms:,.2f}")

            active_id = getattr(self, 'active_engagement_id', None)
            if active_id:
                try:
                    with get_session() as session:
                        risk_svc = RiskService(RiskRepository(session))
                        risk_svc.calculate_materiality(
                            engagement_id=active_id,
                            benchmark_used=combo_text,
                            benchmark_amount=base_val
                        )
                except Exception as save_err:
                    logger.warning(f"Could not persist materiality calculation: {save_err}")

            self.load_findings()
        except ValueError:
            self.lbl_input_err.setText("Invalid numeric format for base amount")
            self.lbl_input_err.show()

    def load_findings(self):
        active_id = getattr(self, 'active_engagement_id', None)
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                finding_service = FindingService(wp_repo)
                raw_findings = finding_service.get_findings_by_audit_id(active_id) if active_id else finding_service.get_all_findings()

                # Deduplicate findings by title / description to prevent duplicate rows
                seen_desc = set()
                findings = []
                for f in raw_findings:
                    desc_clean = f.description.strip()
                    if desc_clean not in seen_desc:
                        seen_desc.add(desc_clean)
                        findings.append(f)

                # Parse overall materiality figure for assessment comparison
                try:
                    val_str = self.base_amt_input.text().replace("₹", "").replace(",", "").strip()
                    base_val = float(val_str)
                    combo_text = self.benchmark_combo.currentText()
                    pct = 0.05 if "5.0%" in combo_text else (0.005 if "0.5%" in combo_text else 0.01)
                    current_om = base_val * pct
                    current_pm = current_om * 0.75
                except Exception:
                    current_om = 320000.0
                    current_pm = 240000.0

                if not findings:
                    self.table.setRowCount(0)
                    self._update_metrics(0, 0, 0)
                    return

                self.table.setRowCount(len(findings))

                high_count = 0
                exceed_mat_count = 0

                for r, f in enumerate(findings):
                    # Clean issue description
                    desc_raw = f.description.split("|")[0].strip() if "|" in f.description else f.description.strip()
                    desc_text = desc_raw
                    for junk in ["Link Working Paper →", "Link Working Paper", "[Link Working Paper →]", "[Link Working Paper]", "→"]:
                        desc_text = desc_text.replace(junk, "").strip()

                    # Real financial impact
                    impact_val = getattr(f, 'financial_impact', 0.0) or 0.0
                    impact_str = f"₹ {impact_val:,.2f}" if impact_val > 0 else "— Not Specified"

                    sev = f.severity or f.risk_level or "Low"
                    if sev == "High": high_count += 1

                    # Materiality status comparison
                    if impact_val >= current_om and current_om > 0:
                        mat_status = "⚡ EXCEEDS OM (Material)"
                        exceed_mat_count += 1
                        mat_fg = "#dc2626"
                    elif impact_val >= current_pm and current_pm > 0:
                        mat_status = "⚠ EXCEEDS PM (Significant)"
                        mat_fg = "#d97706"
                    else:
                        mat_status = "✓ BELOW PM (Tolerable)"
                        mat_fg = "#047857"

                    # Column 0: Issue
                    t_item = QTableWidgetItem(desc_text)
                    t_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                    t_item.setForeground(QColor("#0f172a"))
                    self.table.setItem(r, 0, t_item)

                    # Column 1: Severity Badge
                    sev_item = QTableWidgetItem(f"● {sev.upper()}")
                    sev_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                    sev_fg = "#dc2626" if sev == "High" else ("#d97706" if sev == "Medium" else "#047857")
                    sev_item.setForeground(QColor(sev_fg))
                    self.table.setItem(r, 1, sev_item)

                    # Column 2: Exposure
                    e_item = QTableWidgetItem(impact_str)
                    e_item.setForeground(QColor("#0f172a"))
                    self.table.setItem(r, 2, e_item)

                    # Column 3: Materiality Status
                    m_item = QTableWidgetItem(mat_status)
                    m_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                    m_item.setForeground(QColor(mat_fg))
                    self.table.setItem(r, 3, m_item)

                    # Column 4: Recommendation
                    rec_str = "Substantive testing & 100% voucher verification required" if sev == "High" else "Analytical review & management representation"
                    r_item = QTableWidgetItem(rec_str)
                    r_item.setForeground(QColor("#334155"))
                    self.table.setItem(r, 4, r_item)

                    # Column 5: Action Link
                    act_item = QTableWidgetItem("Link Working Paper →")
                    act_item.setFont(QFont("Inter", 10, QFont.Weight.Bold))
                    act_item.setForeground(QColor("#0284c7"))
                    self.table.setItem(r, 5, act_item)

                self._update_metrics(len(findings), high_count, exceed_mat_count)
                self._update_heatmap_counts(findings)

        except Exception as e:
            logger.error("Failed to load risk findings: %s", e, exc_info=True)
            self.table.setRowCount(0)

    def _on_cell_clicked(self, row: int, col: int):
        if col == 5:
            item = self.table.item(row, 0)
            if item:
                self._link_risk_to_wp(item.text())

    def _update_metrics(self, total: int, high: int, exceed: int):
        lbl_tot = self.lbl_total_risks.findChild(QLabel, "valLbl")
        if lbl_tot: lbl_tot.setText(f"{total} Risks")

        lbl_h = self.lbl_high_risks.findChild(QLabel, "valLbl")
        if lbl_h: lbl_h.setText(f"{high} High")

        lbl_ex = self.lbl_exceed_mat.findChild(QLabel, "valLbl")
        if lbl_ex: lbl_ex.setText(f"{exceed} Findings")

        lbl_rat = self.lbl_overall_rating.findChild(QLabel, "valLbl")
        if lbl_rat:
            if high >= 2: lbl_rat.setText("● HIGH AUDIT RISK")
            elif high == 1: lbl_rat.setText("● MODERATE AUDIT RISK")
            else: lbl_rat.setText("● LOW AUDIT RISK")

    def _update_heatmap_counts(self, findings: list):
        # Distribute findings into heatmap matrix
        counts = {k: 0 for k in self.heatmap_cells.keys()}
        for f in findings:
            sev = f.severity or f.risk_level or "Medium"
            lh = sev
            imp = "High" if (getattr(f, 'financial_impact', 0.0) or 0.0) >= 100000.0 else ("Medium" if (getattr(f, 'financial_impact', 0.0) or 0.0) >= 10000.0 else "Low")
            if (lh, imp) in counts:
                counts[(lh, imp)] += 1

        for (lh, imp), btn in self.heatmap_cells.items():
            cnt = counts.get((lh, imp), 0)
            btn.setText(f"{lh[0]}L x {imp[0]}I\n{cnt} Risks")

    def _filter_by_heatmap(self, likelihood: str, impact: str):
        self._heatmap_filter = (likelihood, impact)
        self.lbl_active_filter.setText(f"Active Filter: Heatmap ({likelihood} Likelihood x {impact} Impact)")
        self.load_findings()

    def _reset_heatmap_filter(self):
        self._heatmap_filter = None
        self.lbl_active_filter.setText("Active Filter: Showing All Risk Findings")
        self.load_findings()

    def _filter_table_search(self, text: str):
        query = text.strip().lower()
        for r in range(self.table.rowCount()):
            t0 = self.table.item(r, 0).text().lower() if self.table.item(r, 0) else ""
            t2 = self.table.item(r, 2).text().lower() if self.table.item(r, 2) else ""
            match = not query or (query in t0 or query in t2)
            self.table.setRowHidden(r, not match)

    def _link_risk_to_wp(self, risk_title: str):
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                wp_service = WorkingPaperService(wp_repo)
                wp_service.add_observation(
                    audit_id=self._active_engagement_id or 1,
                    observation=f"[SA 315 Risk Assessment] {risk_title}: Mandatory audit procedure assigned under ICAI SA 330.",
                    evidence="Risk Matrix Assessment Vault"
                )
                QMessageBox.information(self, "Linked to Working Papers", f"Successfully linked risk '{risk_title}' into SA 230 Working Papers!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not link risk to working paper: {e}")

    def closeEvent(self, event):
        event.accept()
