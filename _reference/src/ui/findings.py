"""
Audit Findings Workspace Module for FinAuditPro.
Provides a dedicated, top-level Audit Findings Manager featuring:
1. Executive Metric Strip (Total Findings, High Risk Count, Total Financial Impact ₹, Resolution Rate)
2. Interactive Search, Severity & Status Filter Bar
3. Findings Data Table with Custom Item Delegates (Severity Badges, Status Pills, Financial Impact Formatting)
4. Finding Inspector & Working Paper Linkage Editor
5. Create & Resolve Finding Dialogs
"""

import logging
import os
from typing import List, Optional
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QTableWidget, QTableWidgetItem,
                               QComboBox, QMessageBox, QSplitter, QTextEdit, QHeaderView,
                               QLineEdit, QDialog, QFormLayout, QDoubleSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Finding, WorkingPaper, WorkingPaperIndex, Engagement
from database.repositories.working_paper_repo import WorkingPaperRepository
from services.finding_service import FindingService
from security.security_manager import SecurityManager
from security.rbac import Permission
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from .icons import get_app_icon, get_app_pixmap

logger = logging.getLogger(__name__)

def format_currency_inr(val: float) -> str:
    """Formats float values into Indian Rupee currency notation (₹ #,##,###.00)."""
    try:
        if val is None:
            return "₹ 0.00"
        s = f"{val:.2f}"
        parts = s.split(".")
        integer_part = parts[0]
        decimal_part = parts[1]
        
        if len(integer_part) <= 3:
            formatted = integer_part
        else:
            last_three = integer_part[-3:]
            rest = integer_part[:-3]
            chunks = []
            while len(rest) > 2:
                chunks.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest:
                chunks.insert(0, rest)
            formatted = ",".join(chunks) + "," + last_three

        return f"₹ {formatted}.{decimal_part}"
    except Exception:
        return f"₹ {val}"

class CreateFindingDialog(QDialog):
    """Dialog for creating a new Audit Finding and linking to a Working Paper."""
    def __init__(self, engagement_id: int = None, parent=None):
        super().__init__(parent)
        self.engagement_id = engagement_id
        self.setWindowTitle("Create Audit Finding")
        self.resize(520, 420)
        self.setStyleSheet("""
            QDialog { background-color: #ffffff; }
            QLabel { font-size: 12px; font-weight: 600; color: #334155; }
            QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox {
                background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 10px; font-size: 12px; color: #0f172a;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border-color: #0284c7;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Create New Audit Finding")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #0f172a;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        self.txt_desc = QTextEdit()
        self.txt_desc.setFixedHeight(80)
        self.txt_desc.setPlaceholderText("Describe the audit observation, anomaly, or compliance exception...")
        form.addRow("Description *:", self.txt_desc)

        self.combo_severity = QComboBox()
        self.combo_severity.addItems(["High", "Medium", "Low"])
        form.addRow("Severity *:", self.combo_severity)

        self.spin_impact = QDoubleSpinBox()
        self.spin_impact.setRange(0.0, 1000000000.0)
        self.spin_impact.setPrefix("₹ ")
        self.spin_impact.setDecimals(2)
        self.spin_impact.setSingleStep(10000.0)
        form.addRow("Financial Impact (₹):", self.spin_impact)

        self.combo_wp = QComboBox()
        self.populate_wp_combo()
        form.addRow("Working Paper *:", self.combo_wp)

        layout.addLayout(form)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("background-color: #f1f5f9; color: #475569; font-weight: 600; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 16px;")
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_save = QPushButton("Create Finding")
        self.btn_save.setStyleSheet("background-color: #0284c7; color: white; font-weight: 700; border-radius: 6px; padding: 8px 18px; border: none;")
        self.btn_save.clicked.connect(self.save_finding)

        btn_box.addWidget(self.btn_cancel)
        btn_box.addWidget(self.btn_save)
        layout.addLayout(btn_box)

    def populate_wp_combo(self):
        self.combo_wp.clear()
        with get_session() as session:
            q = session.query(WorkingPaper)
            if self.engagement_id:
                q = q.join(WorkingPaperIndex).filter(WorkingPaperIndex.engagement_id == self.engagement_id)
            wps = q.all()
            for wp in wps:
                code = wp.index.section_code if wp.index else "WP"
                self.combo_wp.addItem(f"[{code}] {wp.title}", wp.id)

    def save_finding(self):
        desc = self.txt_desc.toPlainText().strip()
        if not desc:
            QMessageBox.warning(self, "Validation Error", "Finding description is required.")
            return

        wp_id = self.combo_wp.currentData()
        if not wp_id:
            QMessageBox.warning(self, "Validation Error", "Please select a target Working Paper.")
            return

        severity = self.combo_severity.currentText()
        impact = self.spin_impact.value()

        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                service = FindingService(wp_repo)
                service.create_finding(working_paper_id=wp_id, description=desc, severity=severity, financial_impact=impact)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Creation Failed", f"Failed to create finding: {e}")

class FindingsWorkspaceWidget(QWidget):
    """
    Standalone Top-Level Findings Manager View.
    Features:
    - Executive Metric Cards Strip
    - Real-Time Search & Severity / Resolution Status Filters
    - Findings Data Table with Custom Status & Severity Badges
    - Inspector Side Panel for Linkage to Working Papers & Resolution Action
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._active_engagement_id = None
        self._active_project_id = None
        self.selected_finding_id = None

        self._init_ui()

    @property
    def active_engagement_id(self):
        return self._active_engagement_id

    @active_engagement_id.setter
    def active_engagement_id(self, val):
        self._active_engagement_id = val
        self.load_findings_data()

    @property
    def active_project_id(self):
        return self._active_project_id

    @active_project_id.setter
    def active_project_id(self, val):
        self._active_project_id = val

    def load_active_document_view(self):
        self.load_findings_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 24)
        main_layout.setSpacing(16)

        # 1. Header Strip & Metrics
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        lbl_title = QLabel("Audit Findings Workspace")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; letter-spacing: -0.4px;")
        lbl_sub = QLabel("Centralized audit anomaly observations, financial impact tracking, and ISA working paper linkage.")
        lbl_sub.setStyleSheet("font-size: 12px; color: #64748b;")

        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.btn_create_finding = QPushButton("+ Create Finding")
        self.btn_create_finding.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create_finding.setStyleSheet("""
            QPushButton {
                background-color: #0284c7; color: #ffffff; font-weight: 700; font-size: 12px;
                border-radius: 6px; padding: 8px 16px; border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        self.btn_create_finding.clicked.connect(self._open_create_dialog)
        header_layout.addWidget(self.btn_create_finding)

        main_layout.addLayout(header_layout)

        # Metric Strip (4 Box Cards)
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(14)

        self.card_total = self._create_metric_card("TOTAL FINDINGS", "0", "AUDIT SCOPE", "#e0f2fe", "#0284c7")
        self.card_high_risk = self._create_metric_card("HIGH RISK ANOMALIES", "0", "CRITICAL", "#fee2e2", "#dc2626")
        self.card_financial = self._create_metric_card("FINANCIAL IMPACT", "₹ 0.00", "EXPOSURE", "#fef3c7", "#d97706")
        self.card_resolved = self._create_metric_card("RESOLUTION RATE", "0%", "AUDIT STATUS", "#dcfce7", "#15803d")

        metrics_layout.addWidget(self.card_total)
        metrics_layout.addWidget(self.card_high_risk)
        metrics_layout.addWidget(self.card_financial)
        metrics_layout.addWidget(self.card_resolved)

        main_layout.addLayout(metrics_layout)

        # 2. Search & Filter Bar
        filter_card = QFrame()
        filter_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px 14px;")
        fl = QHBoxLayout(filter_card)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(12)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍  Search findings by keyword, description, or working paper...")
        self.txt_search.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 12px; font-size: 12px;")
        self.txt_search.textChanged.connect(self.filter_table)

        lbl_sev = QLabel("Severity:")
        lbl_sev.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; border: none;")
        self.combo_severity_filter = QComboBox()
        self.combo_severity_filter.addItems(["All Severities", "High", "Medium", "Low"])
        self.combo_severity_filter.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; font-size: 11px;")
        self.combo_severity_filter.currentIndexChanged.connect(self.filter_table)

        lbl_status = QLabel("Status:")
        lbl_status.setStyleSheet("font-size: 11px; font-weight: 700; color: #475569; border: none;")
        self.combo_status_filter = QComboBox()
        self.combo_status_filter.addItems(["All Statuses", "Unresolved", "Resolved"])
        self.combo_status_filter.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; font-size: 11px;")
        self.combo_status_filter.currentIndexChanged.connect(self.filter_table)

        fl.addWidget(self.txt_search, 1)
        fl.addWidget(lbl_sev)
        fl.addWidget(self.combo_severity_filter)
        fl.addWidget(lbl_status)
        fl.addWidget(self.combo_status_filter)

        main_layout.addWidget(filter_card)

        # 3. Main Splitter: Left Table vs Right Inspector
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background: #cbd5e1; width: 1px; }")

        # Left Table
        self.table_card = QFrame()
        self.table_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        tl = QVBoxLayout(self.table_card)
        tl.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "SEVERITY", "DESCRIPTION & ANOMALY", "FINANCIAL IMPACT", "WORKING PAPER", "STATUS", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #ffffff; border: none; font-size: 12px; color: #0f172a; }
            QHeaderView::section { background-color: #f8fafc; color: #475569; font-weight: 700; font-size: 11px; padding: 8px 12px; border-bottom: 1px solid #e2e8f0; border-top: none; }
            QTableWidget::item { padding: 8px 12px; border-bottom: 1px solid #f1f5f9; }
            QTableWidget::item:selected { background-color: rgba(2, 132, 199, 0.08); color: #0284c7; }
        """)
        self.table.itemSelectionChanged.connect(self._on_finding_selected)

        tl.addWidget(self.table)
        splitter.addWidget(self.table_card)

        # Right Inspector Panel
        self.inspector_card = QFrame()
        self.inspector_card.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;")
        il = QVBoxLayout(self.inspector_card)
        il.setSpacing(12)

        self.lbl_insp_title = QLabel("Select a Finding")
        self.lbl_insp_title.setStyleSheet("font-size: 15px; font-weight: 800; color: #0f172a;")
        il.addWidget(self.lbl_insp_title)

        self.lbl_insp_meta = QLabel("Choose an audit observation from the left table to inspect details, working paper linkage, and resolution status.")
        self.lbl_insp_meta.setWordWrap(True)
        self.lbl_insp_meta.setStyleSheet("font-size: 12px; color: #64748b;")
        il.addWidget(self.lbl_insp_meta)

        self.txt_insp_desc = QTextEdit()
        self.txt_insp_desc.setReadOnly(True)
        self.txt_insp_desc.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; font-size: 12px; color: #0f172a;")
        il.addWidget(self.txt_insp_desc)

        # Linkage & Action Box
        action_box = QFrame()
        action_box.setStyleSheet("background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px;")
        abl = QVBoxLayout(action_box)
        abl.setSpacing(8)

        abl_title = QLabel("WORKING PAPER LINKAGE & STATUS")
        abl_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #0284c7; letter-spacing: 0.6px;")
        abl.addWidget(abl_title)

        self.combo_insp_wp = QComboBox()
        self.combo_insp_wp.setStyleSheet("background: #ffffff; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        abl.addWidget(self.combo_insp_wp)

        self.btn_update_linkage = QPushButton("Update Working Paper Link")
        self.btn_update_linkage.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_update_linkage.setStyleSheet("background: #ffffff; color: #334155; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 11px; font-weight: 600; padding: 5px;")
        self.btn_update_linkage.clicked.connect(self._update_finding_linkage)
        abl.addWidget(self.btn_update_linkage)

        self.btn_toggle_resolve = QPushButton("Mark as Resolved")
        self.btn_toggle_resolve.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_resolve.setStyleSheet("background: #16a34a; color: white; border-radius: 4px; font-size: 11px; font-weight: 700; padding: 7px;")
        self.btn_toggle_resolve.clicked.connect(self._toggle_finding_resolution)
        abl.addWidget(self.btn_toggle_resolve)

        il.addWidget(action_box)
        il.addStretch()

        splitter.addWidget(self.inspector_card)
        splitter.setSizes([750, 400])

        main_layout.addWidget(splitter, 1)

    def _create_metric_card(self, title: str, val: str, badge: str, bg: str, fg: str) -> QFrame:
        card = QFrame()
        card.setFixedHeight(80)
        card.setStyleSheet(f"background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px;")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(4)

        tr = QHBoxLayout()
        tl = QLabel(title)
        tl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 0.5px; border: none;")
        bl = QLabel(badge)
        bl.setStyleSheet(f"font-size: 9px; font-weight: 800; color: {fg}; background: {bg}; padding: 2px 6px; border-radius: 4px; border: none;")
        tr.addWidget(tl)
        tr.addStretch()
        tr.addWidget(bl)
        cl.addLayout(tr)

        vl = QLabel(val)
        vl.setObjectName("valLbl")
        vl.setStyleSheet("font-size: 20px; font-weight: 800; color: #0f172a; border: none;")
        cl.addWidget(vl)

        apply_shadow(card, blur=8, dy=2, alpha=8)
        return card

    def load_findings_data(self):
        self.table.setRowCount(0)
        with get_session() as session:
            q = session.query(Finding)
            if self._active_engagement_id:
                q = q.filter(Finding.audit_id == self._active_engagement_id)
            findings = q.order_by(Finding.id.desc()).all()

            total_c = len(findings)
            high_c = 0
            total_impact = 0.0
            resolved_c = 0

            self.table.setRowCount(len(findings))
            for r, f in enumerate(findings):
                if f.severity == 'High':
                    high_c += 1
                if f.is_resolved:
                    resolved_c += 1
                total_impact += (f.financial_impact or 0.0)

                # Col 0: ID
                id_item = QTableWidgetItem(f"#{f.id}")
                id_item.setData(Qt.ItemDataRole.UserRole, f.id)
                self.table.setItem(r, 0, id_item)

                # Col 1: Severity Badge
                sev_text = f.severity or "Low"
                sev_item = QTableWidgetItem(sev_text)
                self.table.setItem(r, 1, sev_item)

                # Col 2: Description
                desc_text = f.description or "—"
                self.table.setItem(r, 2, QTableWidgetItem(desc_text))

                # Col 3: Impact
                imp_str = format_currency_inr(f.financial_impact)
                self.table.setItem(r, 3, QTableWidgetItem(imp_str))

                # Col 4: Working Paper
                wp_title = f.working_paper.title if f.working_paper else "Unlinked"
                wp_code = f.working_paper.index.section_code if (f.working_paper and f.working_paper.index) else "WP"
                self.table.setItem(r, 4, QTableWidgetItem(f"[{wp_code}] {wp_title}"))

                # Col 5: Status
                st_text = "Resolved" if f.is_resolved else "Unresolved"
                self.table.setItem(r, 5, QTableWidgetItem(st_text))

                # Col 6: Action
                self.table.setItem(r, 6, QTableWidgetItem("Inspect →"))

            # Update Metric Strip
            self.card_total.findChild(QLabel, "valLbl").setText(str(total_c))
            self.card_high_risk.findChild(QLabel, "valLbl").setText(str(high_c))
            self.card_financial.findChild(QLabel, "valLbl").setText(format_currency_inr(total_impact))
            res_rate = int((resolved_c / total_c * 100)) if total_c > 0 else 100
            self.card_resolved.findChild(QLabel, "valLbl").setText(f"{res_rate}%")

            if len(findings) > 0:
                self.table.setCurrentCell(0, 0)

    def filter_table(self):
        query = self.txt_search.text().strip().lower()
        sev_filter = self.combo_severity_filter.currentText()
        st_filter = self.combo_status_filter.currentText()

        for r in range(self.table.rowCount()):
            desc = self.table.item(r, 2).text().lower() if self.table.item(r, 2) else ""
            wp = self.table.item(r, 4).text().lower() if self.table.item(r, 4) else ""
            sev = self.table.item(r, 1).text() if self.table.item(r, 1) else ""
            st = self.table.item(r, 5).text() if self.table.item(r, 5) else ""

            match_query = query in desc or query in wp
            match_sev = (sev_filter == "All Severities") or (sev_filter == sev)
            match_st = (st_filter == "All Statuses") or (st_filter == st)

            self.table.setRowHidden(r, not (match_query and match_sev and match_st))

    def _on_finding_selected(self):
        r = self.table.currentRow()
        if r < 0 or not self.table.item(r, 0):
            return

        finding_id = self.table.item(r, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_finding_id = finding_id

        with get_session() as session:
            f = session.query(Finding).filter_by(id=finding_id).first()
            if not f:
                return

            self.lbl_insp_title.setText(f"Finding #{f.id} — Severity: {f.severity}")
            self.lbl_insp_meta.setText(f"Financial Impact: {format_currency_inr(f.financial_impact)} • Created: {f.created_at.strftime('%d %b %Y') if f.created_at else 'Today'}")
            self.txt_insp_desc.setPlainText(f.description)

            # Populate combo_insp_wp
            self.combo_insp_wp.clear()
            wps = session.query(WorkingPaper).all()
            target_idx = 0
            for i, wp in enumerate(wps):
                code = wp.index.section_code if wp.index else "WP"
                self.combo_insp_wp.addItem(f"[{code}] {wp.title}", wp.id)
                if f.working_paper_id == wp.id:
                    target_idx = i
            self.combo_insp_wp.setCurrentIndex(target_idx)

            if f.is_resolved:
                self.btn_toggle_resolve.setText("Reopen Finding (Mark Unresolved)")
                self.btn_toggle_resolve.setStyleSheet("background: #d97706; color: white; border-radius: 4px; font-size: 11px; font-weight: 700; padding: 7px;")
            else:
                self.btn_toggle_resolve.setText("Mark as Resolved ✓")
                self.btn_toggle_resolve.setStyleSheet("background: #16a34a; color: white; border-radius: 4px; font-size: 11px; font-weight: 700; padding: 7px;")

    def _update_finding_linkage(self):
        if not self.selected_finding_id:
            return
        wp_id = self.combo_insp_wp.currentData()
        if not wp_id:
            return
        try:
            with get_session() as session:
                f = session.query(Finding).filter_by(id=self.selected_finding_id).first()
                if f:
                    f.working_paper_id = wp_id
                    session.commit()
            QMessageBox.information(self, "Linkage Updated", "Finding working paper linkage successfully updated.")
            self.load_findings_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update linkage: {e}")

    def _toggle_finding_resolution(self):
        if not self.selected_finding_id:
            return
        try:
            with get_session() as session:
                wp_repo = WorkingPaperRepository(session)
                service = FindingService(wp_repo)
                f = session.query(Finding).filter_by(id=self.selected_finding_id).first()
                if f:
                    if f.is_resolved:
                        f.is_resolved = False
                        session.commit()
                    else:
                        service.resolve_finding(self.selected_finding_id)
            self.load_findings_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update resolution status: {e}")

    def _open_create_dialog(self):
        dlg = CreateFindingDialog(engagement_id=self._active_engagement_id, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.load_findings_data()
