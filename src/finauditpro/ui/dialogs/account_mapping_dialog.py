"""CA-oriented interactive Schedule III Account Mapping and Validation Dialog."""

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.account_mapping_dtos import (
    BulkMapAccountsDTO,
    MapAccountDTO,
    ValidateMappingsDTO,
)
from finauditpro.application.services.account_mapping_service import AccountMappingService
from finauditpro.domain.account_mapping_entities import MappingStatusEnum, ScheduleIIIHead


class AccountMappingDialog(QDialog):
    """Practical CA interface for grouping and mapping trial balance accounts into Schedule III heads."""

    def __init__(
        self,
        mapping_service: AccountMappingService,
        engagement_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.mapping_service = mapping_service
        self.engagement_id = engagement_id
        self.taxonomy = self.mapping_service.get_taxonomy()
        self.all_mappings: list[Any] = []
        self.displayed_mappings: list[Any] = []

        self.setWindowTitle("Schedule III Trial Balance Account Grouping & Mapping")
        self.resize(1150, 680)
        self.setModal(True)

        self._init_ui()
        self._load_data()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        self.header_lbl = QLabel("Schedule III Account Classification & Lead Schedule Mapper")
        self.header_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A;")
        layout.addWidget(self.header_lbl)

        self.stats_lbl = QLabel("Loading classification status...")
        self.stats_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; padding: 6px 12px; background: #F1F5F9; border-radius: 6px;"
        )
        layout.addWidget(self.stats_lbl)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search account code or name...")
        self.search_input.textChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.search_input, 2)

        self.status_filter = QComboBox()
        self.status_filter.addItems(
            ["All Accounts", "Unmapped Only", "New Accounts Only", "Mapped Only", "Locked Only", "Review Required"]
        )
        self.status_filter.currentIndexChanged.connect(self._apply_filter)
        filter_bar.addWidget(self.status_filter, 1)
        layout.addLayout(filter_bar)

        action_bar = QHBoxLayout()
        action_bar.setSpacing(6)
        self.bulk_category_combo = QComboBox()
        self.bulk_category_combo.addItem("— Select Schedule III Category —", None)
        for h in self.taxonomy:
            self.bulk_category_combo.addItem(f"{h.lead_schedule_ref} - {h.category} > {h.line_item}", h)
        action_bar.addWidget(self.bulk_category_combo, 3)

        self.bulk_apply_btn = QPushButton("Map Selected")
        self.bulk_apply_btn.setObjectName("primaryButton")
        self.bulk_apply_btn.clicked.connect(self._on_bulk_apply_clicked)
        action_bar.addWidget(self.bulk_apply_btn)

        self.lock_btn = QPushButton("Lock Selected")
        self.lock_btn.clicked.connect(self._on_lock_clicked)
        action_bar.addWidget(self.lock_btn)

        self.unlock_btn = QPushButton("Unlock")
        self.unlock_btn.clicked.connect(self._on_unlock_clicked)
        action_bar.addWidget(self.unlock_btn)

        self.flag_review_btn = QPushButton("Flag Review")
        self.flag_review_btn.clicked.connect(self._on_flag_review_clicked)
        action_bar.addWidget(self.flag_review_btn)

        self.history_btn = QPushButton("History")
        self.history_btn.clicked.connect(self._on_view_history_clicked)
        action_bar.addWidget(self.history_btn)
        layout.addLayout(action_bar)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["SELECT", "ACCOUNT CODE", "ACCOUNT NAME", "STATUS", "NEW?", "SCHEDULE III CATEGORY", "LINE ITEM", "LEAD SCHED"]
        )
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for c in (0, 1, 3, 4, 5, 6, 7):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.cellDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.table, 1)

        bottom_bar = QHBoxLayout()
        self.sel_all_btn = QPushButton("Select All")
        self.sel_all_btn.clicked.connect(self._on_select_all_clicked)
        bottom_bar.addWidget(self.sel_all_btn)
        self.desel_all_btn = QPushButton("Deselect All")
        self.desel_all_btn.clicked.connect(self._on_deselect_all_clicked)
        bottom_bar.addWidget(self.desel_all_btn)

        self.validate_btn = QPushButton("Validate Quality Gate")
        self.validate_btn.clicked.connect(self._on_validate_clicked)
        bottom_bar.addWidget(self.validate_btn)

        bottom_bar.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        layout.addLayout(bottom_bar)

    def _load_data(self) -> None:
        self.all_mappings = self.mapping_service.list_mappings(self.engagement_id)
        self._update_stats_banner()
        self._apply_filter()

    def _update_stats_banner(self) -> None:
        rep = self.mapping_service.validate_mappings(ValidateMappingsDTO(engagement_id=self.engagement_id))
        col = "#16A34A" if rep.is_valid_for_finalization else "#DC2626"
        self.stats_lbl.setText(
            f"Accounts: {rep.total_accounts} | Mapped: {rep.mapped_count} | Unmapped: {rep.unmapped_count} (Material: {rep.material_unmapped_count}) | New: {rep.new_accounts_count}"
        )
        self.stats_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {col}; padding: 6px 12px; background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px;")

    def _render_table(self, mappings: list[Any]) -> None:
        self.displayed_mappings = mappings
        self.table.setRowCount(len(mappings))
        for r, m in enumerate(mappings):
            chk = QTableWidgetItem()
            chk.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            chk.setCheckState(Qt.CheckState.Unchecked)
            self.table.setItem(r, 0, chk)
            self.table.setItem(r, 1, QTableWidgetItem(m.account_code))
            self.table.setItem(r, 2, QTableWidgetItem(m.account_name))

            st = m.status.value if hasattr(m.status, "value") else str(m.status)
            st_item = QTableWidgetItem(st)
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if m.status == MappingStatusEnum.MAPPED:
                st_item.setForeground(Qt.GlobalColor.darkGreen)
            elif m.status == MappingStatusEnum.LOCKED:
                st_item.setForeground(Qt.GlobalColor.darkBlue)
            elif m.status == MappingStatusEnum.UNMAPPED:
                st_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(r, 3, st_item)

            new_it = QTableWidgetItem("★ NEW" if m.is_new else "")
            if m.is_new:
                new_it.setForeground(Qt.GlobalColor.darkBlue)
            self.table.setItem(r, 4, new_it)
            self.table.setItem(r, 5, QTableWidgetItem(m.schedule_iii_category or "—"))
            self.table.setItem(r, 6, QTableWidgetItem(m.schedule_iii_line_item or "—"))
            self.table.setItem(r, 7, QTableWidgetItem(m.lead_schedule_ref or "—"))

    def _apply_filter(self) -> None:
        q = self.search_input.text().strip().lower()
        idx = self.status_filter.currentIndex()
        filtered = []
        for m in self.all_mappings:
            mq = not q or (q in m.account_code.lower() or q in m.account_name.lower())
            ms = True
            if idx == 1:
                ms = m.status == MappingStatusEnum.UNMAPPED
            elif idx == 2:
                ms = m.is_new
            elif idx == 3:
                ms = m.status == MappingStatusEnum.MAPPED
            elif idx == 4:
                ms = m.status == MappingStatusEnum.LOCKED
            elif idx == 5:
                ms = m.status == MappingStatusEnum.REVIEW_REQUIRED
            if mq and ms:
                filtered.append(m)
        self._render_table(filtered)

    def _get_selected_codes(self) -> list[str]:
        codes = [
            self.table.item(r, 1).text()
            for r in range(self.table.rowCount())
            if self.table.item(r, 0) and self.table.item(r, 0).checkState() == Qt.CheckState.Checked and self.table.item(r, 1)
        ]
        if not codes:
            cr = self.table.currentRow()
            if 0 <= cr < len(self.displayed_mappings):
                codes = [self.displayed_mappings[cr].account_code]
        return codes

    def _on_select_all_clicked(self) -> None:
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0):
                self.table.item(r, 0).setCheckState(Qt.CheckState.Checked)

    def _on_deselect_all_clicked(self) -> None:
        for r in range(self.table.rowCount()):
            if self.table.item(r, 0):
                self.table.item(r, 0).setCheckState(Qt.CheckState.Unchecked)

    def _on_bulk_apply_clicked(self) -> None:
        head: ScheduleIIIHead | None = self.bulk_category_combo.currentData()
        if not head:
            QMessageBox.warning(self, "Selection Required", "Please select a Schedule III category.")
            return
        codes = self._get_selected_codes()
        if not codes:
            QMessageBox.information(self, "No Accounts", "Select accounts to map.")
            return
        self.mapping_service.bulk_map_accounts(
            BulkMapAccountsDTO(
                engagement_id=self.engagement_id,
                account_codes=codes,
                schedule_iii_category=head.category,
                schedule_iii_line_item=head.line_item,
                lead_schedule_ref=head.lead_schedule_ref,
                account_type=head.account_type,
            )
        )
        self._load_data()

    def _on_row_double_clicked(self, row: int, col: int) -> None:
        if 0 <= row < len(self.displayed_mappings):
            m = self.displayed_mappings[row]
            head: ScheduleIIIHead | None = self.bulk_category_combo.currentData()
            if head:
                self.mapping_service.map_single_account(
                    MapAccountDTO(
                        engagement_id=self.engagement_id,
                        account_code=m.account_code,
                        schedule_iii_category=head.category,
                        schedule_iii_line_item=head.line_item,
                        lead_schedule_ref=head.lead_schedule_ref,
                        account_type=head.account_type,
                    )
                )
                self._load_data()
            else:
                QMessageBox.information(self, "Account Mapping", f"Selected: {m.account_code} - {m.account_name}\nSelect a category above to map.")

    def _on_lock_clicked(self) -> None:
        for code in self._get_selected_codes():
            try:
                self.mapping_service.lock_mapping(self.engagement_id, code)
            except Exception as e:
                QMessageBox.warning(self, "Lock Error", str(e))
        self._load_data()

    def _on_unlock_clicked(self) -> None:
        for code in self._get_selected_codes():
            try:
                self.mapping_service.unlock_mapping(self.engagement_id, code)
            except Exception as e:
                QMessageBox.warning(self, "Unlock Error", str(e))
        self._load_data()

    def _on_flag_review_clicked(self) -> None:
        for code in self._get_selected_codes():
            self.mapping_service.mark_review_required(self.engagement_id, code, "Review required")
        self._load_data()

    def _on_view_history_clicked(self) -> None:
        cr = self.table.currentRow()
        if not (0 <= cr < len(self.displayed_mappings)):
            return
        m = self.displayed_mappings[cr]
        history = self.mapping_service.get_mapping_history(m.id)
        if not history:
            QMessageBox.information(self, "History", f"No history for '{m.account_code}'.")
            return
        hist_dialog = QDialog(self)
        hist_dialog.setWindowTitle(f"History — {m.account_code}")
        hist_dialog.resize(600, 300)
        lay = QVBoxLayout(hist_dialog)
        tbl = QTableWidget(len(history), 4)
        tbl.setHorizontalHeaderLabels(["TIME", "BY", "PREVIOUS", "NEW"])
        tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        for r, h in enumerate(history):
            tbl.setItem(r, 0, QTableWidgetItem(h.changed_at[:19]))
            tbl.setItem(r, 1, QTableWidgetItem(h.changed_by))
            tbl.setItem(r, 2, QTableWidgetItem(h.previous_category or "—"))
            tbl.setItem(r, 3, QTableWidgetItem(f"{h.new_category} > {h.new_line_item}"))
        lay.addWidget(tbl)
        hist_dialog.exec()

    def _on_validate_clicked(self) -> None:
        rep = self.mapping_service.validate_mappings(ValidateMappingsDTO(engagement_id=self.engagement_id))
        msg = "\n".join(rep.validation_messages)
        if rep.is_valid_for_finalization:
            QMessageBox.information(self, "Quality Gate Passed", f"Validation PASSED!\n\n{msg}")
        else:
            QMessageBox.warning(self, "Quality Gate Incomplete", f"Validation FAILED:\n\n{msg}")
