"""
Rule Management Widget for FinAuditPro.
Provides UI interface to view, filter, enable/disable, and monitor automated audit rules.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QLineEdit, QComboBox, QCheckBox, QMessageBox)
from PySide6.QtCore import Qt
from rule_engine.rule_engine import AuditRuleEngine
from rule_engine.severity import RuleCategory, RuleSeverity
from security.security_manager import SecurityManager
from security.rbac import Permission
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget

class RuleManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f0f6ff;")
        self.engine = AuditRuleEngine()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 24, 28, 28)
        main_layout.setSpacing(20)

        # Header Frame
        header = QFrame()
        header.setFixedHeight(68)
        header.setObjectName("headerBar")
        header.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4; border-radius: 12px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 0, 20, 0)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        t_lbl = QLabel("Audit Rule Management")
        t_lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.4px; border: none; background: transparent;")
        sub_lbl = QLabel("Configure, filter, and enable automated offline financial audit rules.")
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748b; border: none; background: transparent;")
        title_box.addWidget(t_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()

        main_layout.addWidget(header)

        # Stat Cards (Item 48: Dynamically compute severity counts!)
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)

        rules = self.engine.registry.get_all_rules()
        total_count = len(rules)
        active_count = len(self.engine.registry.get_active_rules())

        # Count actual severities from registry
        crit_count = sum(1 for r in rules if r.severity == RuleSeverity.CRITICAL)
        high_count = sum(1 for r in rules if r.severity == RuleSeverity.HIGH)
        med_low_count = sum(1 for r in rules if r.severity in (RuleSeverity.MEDIUM, RuleSeverity.LOW))

        def create_stat(title, val, color_hex):
            card = QFrame()
            card.setFixedHeight(84)
            card.setStyleSheet("QFrame { background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 12px; } QFrame:hover { border-color: #0284c7; }")
            l = QVBoxLayout(card)
            l.setContentsMargins(16, 12, 16, 12)
            l.setSpacing(4)
            t = QLabel(title)
            t.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 600; letter-spacing: 0.4px; border: none;")
            v = QLabel(str(val))
            v.setStyleSheet(f"color: {color_hex}; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; border: none;")
            l.addWidget(t)
            l.addWidget(v)
            apply_shadow(card, blur=12, dy=2, alpha=10)
            return card

        stats_layout.addWidget(create_stat("Total Rules", total_count, "#0f172a"))
        stats_layout.addWidget(create_stat("Active Rules", active_count, "#0284c7"))
        stats_layout.addWidget(create_stat("Critical Severity", crit_count, "#dc2626"))
        stats_layout.addWidget(create_stat("High Severity", high_count, "#d97706"))
        stats_layout.addWidget(create_stat("Medium / Low", med_low_count, "#047857"))

        main_layout.addLayout(stats_layout)

        # Filter Toolbar (Item 1: Strong focus policies)
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 10px; padding: 6px;")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 6, 12, 6)
        tb_layout.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search rules by ID or name...")
        self.search_box.setToolTip("Filter rule registry by rule ID or rule name (Item 1)")
        self.search_box.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.search_box.setStyleSheet("QLineEdit { padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 6px; background-color: #ffffff; color: #0f172a; font-size: 12px; } QLineEdit:focus { border-color: #0284c7; }")
        self.search_box.textChanged.connect(self.load_table_data)
        tb_layout.addWidget(self.search_box, 2)

        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All Categories")
        self.cat_combo.setToolTip("Filter rules by statutory classification category")
        self.cat_combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        for cat in RuleCategory:
            # Item 84: Clean display names
            display_name = cat.value.replace("_", " ").title()
            self.cat_combo.addItem(display_name, cat.value)
        self.cat_combo.setStyleSheet("QComboBox { padding: 8px 12px; border: 1px solid #e1e8f4; border-radius: 6px; background-color: #ffffff; color: #0f172a; font-size: 12px; } QComboBox:focus { border-color: #0284c7; }")
        self.cat_combo.currentIndexChanged.connect(self.load_table_data)
        tb_layout.addWidget(self.cat_combo, 1)

        main_layout.addWidget(toolbar)

        # Table Widget
        self.table = QTableWidget(0, 6)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.setToolTip("Automated Audit Rule Registry Table")
        self.table.setHorizontalHeaderLabels(["Rule ID", "Rule Name", "Category", "Severity", "Standard", "Enabled"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: #ffffff; border: 1px solid #e1e8f4; border-radius: 10px; gridline-color: #f0f6ff; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: 700; font-size: 11px; border: none; border-bottom: 1px solid #e1e8f4; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f0f6ff; color: #334155; font-size: 12px; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)

        main_layout.addWidget(self.table)
        self.load_table_data()

    def load_table_data(self):
        self.table.setRowCount(0)
        rules = self.engine.registry.get_all_rules()
        search_text = self.search_box.text().lower().strip()
        selected_cat_data = self.cat_combo.currentData()

        row_idx = 0
        for r in rules:
            if search_text and (search_text not in r.rule_id.lower() and search_text not in r.rule_name.lower()):
                continue
            if selected_cat_data and r.category.value != selected_cat_data:
                continue

            self.table.insertRow(row_idx)
            
            id_item = QTableWidgetItem(r.rule_id)
            id_item.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            self.table.setItem(row_idx, 0, id_item)
            
            name_item = QTableWidgetItem(r.rule_name)
            self.table.setItem(row_idx, 1, name_item)
            
            # Item 2: Category item with tooltip
            cat_text = r.category.value.replace("_", " ").title()
            cat_item = QTableWidgetItem(cat_text)
            cat_item.setToolTip(f"Category: {cat_text}")
            self.table.setItem(row_idx, 2, cat_item)
            
            # Item 2: Severity item with tooltip
            sev_item = QTableWidgetItem(r.severity.value)
            sev_item.setToolTip(f"Rule Severity Level: {r.severity.value}")
            sev_item.setFont(QFont("Inter", 9, QFont.Weight.Bold))
            if r.severity == RuleSeverity.CRITICAL:
                sev_item.setForeground(QColor("#dc2626"))
            elif r.severity == RuleSeverity.HIGH:
                sev_item.setForeground(QColor("#d97706"))
            else:
                sev_item.setForeground(QColor("#047857"))
            self.table.setItem(row_idx, 3, sev_item)

            std_item = QTableWidgetItem(r.accounting_standard)
            std_item.setToolTip(f"ICAI / Statutory Accounting Standard Basis: {r.accounting_standard}")
            self.table.setItem(row_idx, 4, std_item)

            chk = QCheckBox()
            chk.setChecked(r.enabled)
            chk.setToolTip(f"Toggle rule {r.rule_id} status")
            chk.stateChanged.connect(lambda state, rid=r.rule_id: self.toggle_rule(rid, state == 2))

            # Align checkbox center
            cell_widget = QWidget()
            layout = QHBoxLayout(cell_widget)
            layout.addWidget(chk)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(row_idx, 5, cell_widget)

            row_idx += 1

    def toggle_rule(self, rule_id, enabled):
        sm = SecurityManager()
        if not sm.current_session or not sm.check_permission(Permission.MANAGE_RULES):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to manage audit rules.")
            self.load_table_data()
            return
        self.engine.registry.set_rule_enabled(rule_id, enabled)
