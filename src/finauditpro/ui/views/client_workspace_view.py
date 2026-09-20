"""Single-pane Client Workspace View for FinAuditPro Enterprise Shell.

Provides a unified workspace for a client entity featuring Overview, Work, Documents,
Requests, Reconciliations, Compliance, Engagements, and Activity sub-views.
"""


from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos_client_workspace import ClientWorkspaceSummaryDTO
from finauditpro.application.services.client_workspace_service import ClientWorkspaceService
from finauditpro.ui.theme import CardWidget, MetricCard, StatusBadge
from finauditpro.ui.widgets.custom_combo import CustomComboBox


def _create_card_table_page(title: str, col_headers: list[str]) -> tuple[QWidget, QTableWidget]:
    widget = QWidget()
    w_l = QVBoxLayout(widget)
    w_l.setContentsMargins(20, 16, 20, 20)
    card = CardWidget(title)
    table = QTableWidget()
    table.setColumnCount(len(col_headers))
    table.setHorizontalHeaderLabels(col_headers)
    table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    for c in range(1, len(col_headers)):
        table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
    table.verticalHeader().setVisible(False)
    table.setAlternatingRowColors(True)
    card.content_layout.addWidget(table)
    w_l.addWidget(card)
    return widget, table


class ClientWorkspaceView(QWidget):
    """Unified Client Workspace View."""

    engagement_selected = Signal(str)
    navigate_to_route = Signal(str)

    def __init__(
        self,
        client_workspace_service: ClientWorkspaceService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.workspace_service = client_workspace_service
        self.current_client_id: str | None = None
        self.current_summary: ClientWorkspaceSummaryDTO | None = None
        self.current_tab_idx = 0
        self._init_ui()

    def set_client(self, client_id: str | None) -> None:
        self.current_client_id = client_id
        self.refresh()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header Frame
        self.hdr_frame = QFrame()
        self.hdr_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; padding: 12px 20px; }")
        hdr_l = QHBoxLayout(self.hdr_frame)
        hdr_l.setContentsMargins(0, 0, 0, 0)

        info_v = QVBoxLayout()
        info_v.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        self.lbl_client_name = QLabel("Select Client Workspace")
        self.lbl_client_name.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        self.badge_entity = QLabel("Private Limited")
        self.badge_entity.setStyleSheet("QLabel { background: #F1F5F9; color: #475569; font-size: 11px; font-weight: 600; border-radius: 4px; padding: 2px 8px; border: 1px solid #CBD5E1; }")
        self.badge_status = StatusBadge("Active Client", "success")
        for w in (self.lbl_client_name, self.badge_entity, self.badge_status):
            title_row.addWidget(w)
        title_row.addStretch()

        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        self.lbl_meta_pan, self.lbl_meta_gstin, self.lbl_meta_fy = QLabel("PAN: —"), QLabel("GSTIN: —"), QLabel("ACTIVE FY: —")
        for lbl in (self.lbl_meta_pan, self.lbl_meta_gstin, self.lbl_meta_fy):
            lbl.setStyleSheet("font-size: 12px; color: #64748B; font-weight: 500;")
            meta_row.addWidget(lbl)
        meta_row.addStretch()

        info_v.addLayout(title_row)
        info_v.addLayout(meta_row)
        hdr_l.addLayout(info_v)
        hdr_l.addStretch()

        eng_box = QHBoxLayout()
        eng_box.setSpacing(6)
        lbl_eng_tag = QLabel("ENGAGEMENT:")
        lbl_eng_tag.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B;")
        self.combo_engagements = CustomComboBox()
        self.combo_engagements.setMinimumWidth(220)
        self.combo_engagements.currentIndexChanged.connect(self._on_engagement_changed)
        eng_box.addWidget(lbl_eng_tag)
        eng_box.addWidget(self.combo_engagements)
        hdr_l.addLayout(eng_box)
        main_layout.addWidget(self.hdr_frame)

        # Sub-Tabs Bar
        tab_frame = QFrame()
        tab_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border-bottom: 1px solid #E2E8F0; padding: 0 16px; }")
        tab_l = QHBoxLayout(tab_frame)
        tab_l.setContentsMargins(0, 0, 0, 0)
        tab_l.setSpacing(4)
        self.tab_buttons, self.tab_group = [], QButtonGroup(self)
        for idx, name in enumerate(["Overview", "Work", "Documents", "Requests", "Reconciliations", "Compliance", "Engagements", "Activity"]):
            btn = QPushButton(name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background: transparent; color: #64748B; font-size: 12px; font-weight: 500; padding: 8px 14px; border: none; border-bottom: 2px solid transparent; } QPushButton:hover { color: #0284C7; } QPushButton:checked { color: #0284C7; font-weight: 700; border-bottom: 2px solid #0284C7; }")
            btn.clicked.connect(lambda _, i=idx: self._on_sub_tab_clicked(i))
            self.tab_buttons.append(btn)
            self.tab_group.addButton(btn, idx)
            tab_l.addWidget(btn)
        self.tab_buttons[0].setChecked(True)
        tab_l.addStretch()
        main_layout.addWidget(tab_frame)

        # Sub-Pages Stack
        self.stack = QStackedWidget()
        self.page_overview = self._create_overview_page()
        self.page_work, self.table_work = _create_card_table_page("CLIENT AUDIT TASKS, FINDINGS & RISKS", ["ITEM TYPE", "TITLE & DESCRIPTION", "SEVERITY", "FY", "STATUS"])
        self.page_docs, self.table_docs = _create_card_table_page("CLIENT EVIDENCE DOCUMENTS", ["FILENAME", "CATEGORY", "SIZE", "STATUS"])
        self.page_requests, self.table_requests = _create_card_table_page("CLIENT PBC DOCUMENT INTAKE STATUS", ["REQUEST ITEM", "CATEGORY", "STATUS"])
        self.page_recon, self.table_recon = _create_card_table_page("GST & FINANCIAL RECONCILIATION EXCEPTIONS", ["CATEGORY", "DISCREPANCY DETAILS", "AMOUNT", "STATUS"])
        self.page_compliance, self.table_comp = _create_card_table_page("STATUTORY COMPLIANCE CHECKLIST STATUS", ["CHECKLIST", "SCOPE", "STATUS"])
        self.page_engs, self.table_engs = _create_card_table_page("CLIENT ENGAGEMENT HISTORY", ["FINANCIAL YEAR", "AUDIT TYPE", "STATUS", "CREATED", "ACTION"])
        self.page_act, self.table_act = _create_card_table_page("CLIENT AUDIT LOG TIMELINE", ["TIMESTAMP", "EVENT TYPE", "DETAILS", "USER"])

        for p in (self.page_overview, self.page_work, self.page_docs, self.page_requests, self.page_recon, self.page_compliance, self.page_engs, self.page_act):
            self.stack.addWidget(p)

        main_layout.addWidget(self.stack, stretch=1)
        self.refresh()

    def _on_sub_tab_clicked(self, idx: int) -> None:
        self.current_tab_idx = idx
        self.stack.setCurrentIndex(idx)

    def _on_engagement_changed(self, idx: int) -> None:
        eng_id = self.combo_engagements.itemData(idx)
        if eng_id and str(eng_id).startswith("eng:"):
            self.engagement_selected.emit(str(eng_id)[4:])

    def _create_overview_page(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color: #F8FAFC; border: none;")
        body = QWidget()
        body_l = QVBoxLayout(body)
        body_l.setContentsMargins(20, 16, 20, 20)
        body_l.setSpacing(14)
        m_row = QHBoxLayout()
        m_row.setSpacing(12)
        self.ov_card_docs = MetricCard("CLIENT EVIDENCE", "0", "Uploaded documents", accent_color="#0284C7")
        self.ov_card_pbc = MetricCard("PBC REQUESTS", "0", "Pending intake items", accent_color="#D97706")
        self.ov_card_work = MetricCard("OPEN TASKS & RISKS", "0", "Requiring audit review", accent_color="#DC2626")
        self.ov_card_recon = MetricCard("GST MISMATCHES", "0", "Reconciliation exceptions", accent_color="#7C3AED")
        for c in (self.ov_card_docs, self.ov_card_pbc, self.ov_card_work, self.ov_card_recon):
            m_row.addWidget(c, stretch=1)
        body_l.addLayout(m_row)

        op_card = CardWidget("ACTIVE AUDIT STATUS & NEXT ACTION")
        lbl_title = QLabel("Execute statutory audit planning, materiality calculations (SA 320), and ledger scrutiny.")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; color: #0F172A;")
        btn_go_matrix = QPushButton("Open Planning & SA 320 →")
        btn_go_matrix.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_go_matrix.setStyleSheet("QPushButton { background: #0284C7; color: #FFFFFF; font-weight: 600; font-size: 12px; border-radius: 5px; padding: 6px 14px; border: none; } QPushButton:hover { background: #0369A1; }")
        btn_go_matrix.clicked.connect(lambda: self.navigate_to_route.emit("audit_matrix"))
        op_l = QHBoxLayout()
        op_l.addWidget(lbl_title)
        op_l.addStretch()
        op_l.addWidget(btn_go_matrix)
        op_card.content_layout.addLayout(op_l)
        body_l.addWidget(op_card)
        body_l.addStretch(1)
        scroll.setWidget(body)
        return scroll

    def refresh(self) -> None:
        if not self.current_client_id:
            self.lbl_client_name.setText("No Client Selected")
            return
        try:
            summary = self.workspace_service.get_client_workspace_summary(self.current_client_id)
        except Exception:
            return
        self.current_summary = summary
        hdr = summary.header
        self.lbl_client_name.setText(hdr.client_name)
        self.badge_entity.setText(hdr.entity_type)
        self.lbl_meta_pan.setText(f"PAN: {hdr.pan or '—'}")
        self.lbl_meta_gstin.setText(f"GSTIN: {hdr.gstin or '—'}")
        self.lbl_meta_fy.setText(f"ACTIVE FY: {hdr.active_fy}")

        self.combo_engagements.blockSignals(True)
        self.combo_engagements.clear()
        if summary.engagements:
            for e in summary.engagements:
                self.combo_engagements.addItem(f"FY {e.financial_year} · {e.audit_type}", f"eng:{e.id}")
        else:
            self.combo_engagements.addItem("No engagements created", None)
        self.combo_engagements.blockSignals(False)

        self.ov_card_docs.set_value(str(summary.total_documents))
        self.ov_card_pbc.set_value(str(summary.pending_pbc_count))
        self.ov_card_work.set_value(str(summary.open_findings_count))
        self.ov_card_recon.set_value(str(summary.reconciliation_mismatches_count))

        self.table_work.setRowCount(0)
        for idx, item in enumerate(summary.work_items):
            self.table_work.insertRow(idx)
            self.table_work.setItem(idx, 0, QTableWidgetItem(item.item_type))
            self.table_work.setItem(idx, 1, QTableWidgetItem(f"{item.title} — {item.description}"))
            self.table_work.setItem(idx, 2, QTableWidgetItem(item.severity_risk))
            self.table_work.setItem(idx, 3, QTableWidgetItem(item.financial_year))
            self.table_work.setItem(idx, 4, QTableWidgetItem(item.status))

        self.table_engs.setRowCount(0)
        for idx, eng in enumerate(summary.engagements):
            self.table_engs.insertRow(idx)
            self.table_engs.setItem(idx, 0, QTableWidgetItem(f"FY {eng.financial_year}"))
            self.table_engs.setItem(idx, 1, QTableWidgetItem(eng.audit_type))
            self.table_engs.setItem(idx, 2, QTableWidgetItem(eng.status))
            self.table_engs.setItem(idx, 3, QTableWidgetItem(eng.created_at.strftime("%d %b %Y")))
            btn_open = QPushButton("Open →")
            btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_open.clicked.connect(lambda _, e_id=eng.id: self.engagement_selected.emit(e_id))
            self.table_engs.setCellWidget(idx, 4, btn_open)
