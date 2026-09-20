"""PySide6 Unified Reconciliation Center view covering GST, Bank, Ledger, Invoices, Receivables, and Payables."""

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.dtos_reconciliation import (
    MatchStatusEnum,
    ReconciliationItemDTO,
    ReconciliationSummaryDTO,
    ReconciliationTabEnum,
)
from finauditpro.application.services.unified_reconciliation_service import (
    UnifiedReconciliationService,
)
from finauditpro.ui.theme import PageHeader


class ReconciliationItemCard(QFrame):
    """Card displaying source A vs source B records, status badge, difference, and View Source / Ask AI actions."""

    view_source_requested = Signal(object)
    ask_ai_requested = Signal(object)

    def __init__(self, item: ReconciliationItemDTO, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.setObjectName("ReconciliationItemCard")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame#ReconciliationItemCard {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header Row: Title & Status Badge
        hdr = QHBoxLayout()
        title_lbl = QLabel(item.title)
        title_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #F8FAFC;")
        hdr.addWidget(title_lbl)
        hdr.addStretch()

        badge_color = "#10B981" if item.match_status == MatchStatusEnum.MATCHED else (
            "#EF4444" if item.match_status == MatchStatusEnum.UNMATCHED else (
                "#8B5CF6" if item.match_status == MatchStatusEnum.POTENTIAL_MATCH else "#F59E0B"
            )
        )
        badge = QLabel(f"  {item.match_status.value}  ")
        badge.setStyleSheet(f"background-color: {badge_color}; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 2px 6px;")
        hdr.addWidget(badge)
        layout.addLayout(hdr)

        # Source A vs Source B Grid
        sources_layout = QHBoxLayout()
        src_a_box = self._create_source_box(item.source_a.label, item.source_a.reference, item.source_a.amount_rupees)
        src_b_box = self._create_source_box(item.source_b.label, item.source_b.reference, item.source_b.amount_rupees)
        diff_box = self._create_source_box("Difference", "", item.difference_rupees, is_diff=True)

        sources_layout.addWidget(src_a_box)
        sources_layout.addWidget(src_b_box)
        sources_layout.addWidget(diff_box)
        layout.addLayout(sources_layout)

        # Discrepancy Rationale / Details
        if item.discrepancy_reason:
            reason_lbl = QLabel(f"Rationale: {item.discrepancy_reason}")
            reason_lbl.setWordWrap(True)
            reason_lbl.setStyleSheet("color: #94A3B8; font-size: 12px; font-style: italic;")
            layout.addWidget(reason_lbl)

        # AI Explanation Container (Populated when Ask AI clicked)
        self.ai_box = QFrame()
        self.ai_box.setVisible(False)
        self.ai_box.setStyleSheet("background-color: #0F172A; border: 1px solid #3B82F6; border-radius: 6px; padding: 8px;")
        ai_lay = QVBoxLayout(self.ai_box)
        ai_lay.setContentsMargins(8, 8, 8, 8)
        self.ai_text = QLabel()
        self.ai_text.setWordWrap(True)
        self.ai_text.setStyleSheet("color: #60A5FA; font-size: 12px;")
        ai_lay.addWidget(self.ai_text)
        layout.addWidget(self.ai_box)

        # Action Buttons Row
        actions_row = QHBoxLayout()
        actions_row.addStretch()

        btn_source = QPushButton("View Source")
        btn_source.setStyleSheet("background-color: #334155; color: #F8FAFC; border-radius: 4px; padding: 5px 12px;")
        btn_source.clicked.connect(lambda: self.view_source_requested.emit(self.item))
        actions_row.addWidget(btn_source)

        btn_ai = QPushButton("Ask AI")
        btn_ai.setStyleSheet("background-color: #2563EB; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 5px 12px;")
        btn_ai.clicked.connect(lambda: self.ask_ai_requested.emit(self.item))
        actions_row.addWidget(btn_ai)

        layout.addLayout(actions_row)

    def _create_source_box(self, label: str, ref: str, amount_rupees: float, is_diff: bool = False) -> QFrame:
        box = QFrame()
        box.setStyleSheet("background-color: #0F172A; border-radius: 6px; padding: 8px;")
        lay = QVBoxLayout(box)
        lay.setContentsMargins(8, 6, 8, 6)

        lbl = QLabel(label)
        lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
        lay.addWidget(lbl)

        if ref:
            ref_lbl = QLabel(f"Ref: {ref}")
            ref_lbl.setStyleSheet("color: #64748B; font-size: 10px;")
            lay.addWidget(ref_lbl)

        amt_color = "#EF4444" if is_diff and amount_rupees > 0 else "#F8FAFC"
        amt_lbl = QLabel(f"₹{amount_rupees:,.2f}")
        amt_lbl.setStyleSheet(f"color: {amt_color}; font-size: 14px; font-weight: bold;")
        lay.addWidget(amt_lbl)

        return box

    def show_ai_explanation(self, explanation_text: str) -> None:
        self.ai_text.setText(explanation_text)
        self.ai_box.setVisible(True)


class UnifiedReconciliationView(QWidget):
    """Unified Reconciliation Center workspace orchestrating GST, Bank, Ledger, Invoices, Receivables, and Payables tabs."""

    view_source_clicked = Signal(object)

    def __init__(self, db_manager: Any, ai_service: Any = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.ai_service = ai_service
        self.recon_service = UnifiedReconciliationService(db_manager)
        self.current_engagement_id: str | None = None
        self.active_tab: ReconciliationTabEnum = ReconciliationTabEnum.GST
        self.active_status_filter: str | None = None
        self.item_cards: list[ReconciliationItemCard] = []

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        header = PageHeader(
            "Unified Reconciliation Center",
            "Deterministic matching across GST, Bank, Ledger, Invoices, Receivables, and Payables",
        )
        main_layout.addWidget(header)

        # Tab Navigation Bar (6 Tabs)
        tab_bar = QHBoxLayout()
        self.tab_group = QButtonGroup(self)
        self.tab_buttons: dict[ReconciliationTabEnum, QPushButton] = {}

        tabs = [
            (ReconciliationTabEnum.GST, "GST"),
            (ReconciliationTabEnum.BANK, "Bank"),
            (ReconciliationTabEnum.LEDGER, "Ledger"),
            (ReconciliationTabEnum.INVOICES, "Invoices"),
            (ReconciliationTabEnum.RECEIVABLES, "Receivables"),
            (ReconciliationTabEnum.PAYABLES, "Payables"),
        ]

        for idx, (tab_enum, title) in enumerate(tabs):
            btn = QPushButton(title)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1E293B; color: #94A3B8; font-weight: bold; border-radius: 6px; padding: 8px 16px;
                }
                QPushButton:checked {
                    background-color: #2563EB; color: #FFFFFF;
                }
            """)
            if idx == 0:
                btn.setChecked(True)
            self.tab_group.addButton(btn, idx)
            self.tab_buttons[tab_enum] = btn
            tab_bar.addWidget(btn)

        self.tab_group.idClicked.connect(self._on_tab_changed)
        tab_bar.addStretch()
        main_layout.addLayout(tab_bar)

        # Filter Bar: Status Filters (All, Matched, Unmatched, Potential Match, Needs Review)
        filter_bar = QHBoxLayout()
        filter_lbl = QLabel("Filter Status:")
        filter_lbl.setStyleSheet("color: #94A3B8; font-weight: bold;")
        filter_bar.addWidget(filter_lbl)

        self.filter_group = QButtonGroup(self)
        statuses = ["All", MatchStatusEnum.MATCHED.value, MatchStatusEnum.UNMATCHED.value, MatchStatusEnum.POTENTIAL_MATCH.value, MatchStatusEnum.NEEDS_REVIEW.value]
        for idx, st in enumerate(statuses):
            f_btn = QPushButton(st)
            f_btn.setCheckable(True)
            f_btn.setStyleSheet("""
                QPushButton { background-color: #334155; color: #CBD5E1; border-radius: 4px; padding: 4px 10px; }
                QPushButton:checked { background-color: #475569; color: #FFFFFF; font-weight: bold; }
            """)
            if idx == 0:
                f_btn.setChecked(True)
            self.filter_group.addButton(f_btn, idx)
            filter_bar.addWidget(f_btn)

        self.filter_group.idClicked.connect(self._on_filter_changed)
        filter_bar.addStretch()
        main_layout.addLayout(filter_bar)

        # Scrollable Cards Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        self.cards_layout.addStretch()

        scroll.setWidget(self.cards_container)
        main_layout.addWidget(scroll)

    def set_engagement_context(self, engagement_id: str) -> None:
        self.current_engagement_id = engagement_id
        self.reload_reconciliations()

    set_active_engagement = set_engagement_context

    def reload_reconciliations(self) -> None:
        if not self.current_engagement_id:
            return

        # Clear existing cards
        self.item_cards.clear()
        while self.cards_layout.count() > 1:
            child = self.cards_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        summary: ReconciliationSummaryDTO = self.recon_service.get_reconciliation_summary(
            self.current_engagement_id, tab=self.active_tab, status_filter=self.active_status_filter
        )

        if not summary.items:
            empty_lbl = QLabel("No reconciliation items found for the selected tab and filter.")
            empty_lbl.setStyleSheet("color: #64748B; font-size: 14px; font-style: italic; padding: 20px;")
            self.cards_layout.insertWidget(0, empty_lbl)
            return

        for item in summary.items:
            card = ReconciliationItemCard(item)
            card.view_source_requested.connect(self._on_view_source_requested)
            card.ask_ai_requested.connect(lambda itm, c=card: self._on_ask_ai_requested(itm, c))
            self.item_cards.append(card)
            self.cards_layout.insertWidget(self.cards_layout.count() - 1, card)

    def _on_tab_changed(self, idx: int) -> None:
        tabs = [
            ReconciliationTabEnum.GST, ReconciliationTabEnum.BANK, ReconciliationTabEnum.LEDGER,
            ReconciliationTabEnum.INVOICES, ReconciliationTabEnum.RECEIVABLES, ReconciliationTabEnum.PAYABLES
        ]
        if 0 <= idx < len(tabs):
            self.active_tab = tabs[idx]
            self.reload_reconciliations()

    def _on_filter_changed(self, idx: int) -> None:
        statuses = [None, MatchStatusEnum.MATCHED.value, MatchStatusEnum.UNMATCHED.value, MatchStatusEnum.POTENTIAL_MATCH.value, MatchStatusEnum.NEEDS_REVIEW.value]
        if 0 <= idx < len(statuses):
            self.active_status_filter = statuses[idx]
            self.reload_reconciliations()

    def _on_view_source_requested(self, item: ReconciliationItemDTO) -> None:
        self.view_source_clicked.emit(item)
        QMessageBox.information(
            self, "Reconciliation Source Records",
            f"Source A ({item.source_a.label}): {item.source_a.reference} = ₹{item.source_a.amount_rupees:,.2f}\n"
            f"Source B ({item.source_b.label}): {item.source_b.reference} = ₹{item.source_b.amount_rupees:,.2f}\n"
            f"Difference: ₹{item.difference_rupees:,.2f}\n\nRationale: {item.discrepancy_reason}"
        )

    def _on_ask_ai_requested(self, item: ReconciliationItemDTO, card: ReconciliationItemCard) -> None:
        explanation = self.recon_service.explain_exception_with_ai(item, ai_service=self.ai_service)
        card.show_ai_explanation(explanation)
