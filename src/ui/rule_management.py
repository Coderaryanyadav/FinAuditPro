"""
Rule Management Widget for FinAuditPro.
Provides UI interface to view, filter, enable/disable, and monitor automated audit rules.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QFrame, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QLineEdit, QComboBox, QCheckBox)
from PySide6.QtCore import Qt
from rule_engine.rule_engine import AuditRuleEngine
from rule_engine.severity import RuleCategory, RuleSeverity
from .styles import apply_shadow

class RuleManagementWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f8fafc;")
        self.engine = AuditRuleEngine()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 32, 32, 32)
        main_layout.setSpacing(24)
        
        # Header
        header = QFrame()
        header.setStyleSheet("border: none; background: transparent;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        t_lbl = QLabel("Audit Rule Management")
        t_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a;")
        sub_lbl = QLabel("Configure, filter, and enable automated offline financial audit rules.")
        sub_lbl.setStyleSheet("font-size: 14px; color: #64748b;")
        title_box.addWidget(t_lbl)
        title_box.addWidget(sub_lbl)
        h_layout.addLayout(title_box)
        h_layout.addStretch()
        
        main_layout.addWidget(header)
        
        # Stat Cards
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(16)
        
        rules = self.engine.registry.get_all_rules()
        total_count = len(rules)
        active_count = len(self.engine.registry.get_active_rules())
        
        def create_stat(title, val, color):
            card = QFrame()
            card.setFixedHeight(90)
            card.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 8px;")
            l = QVBoxLayout(card)
            t = QLabel(title)
            t.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold;")
            v = QLabel(str(val))
            v.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: bold;")
            l.addWidget(t)
            l.addWidget(v)
            apply_shadow(card, blur=10, dy=2, alpha=10)
            return card
            
        stats_layout.addWidget(create_stat("Total Rules", total_count, "#0f172a"))
        stats_layout.addWidget(create_stat("Active Rules", active_count, "#0ea5e9"))
        stats_layout.addWidget(create_stat("Critical Severity", 2, "#ef4444"))
        stats_layout.addWidget(create_stat("High Severity", 3, "#f59e0b"))
        stats_layout.addWidget(create_stat("Medium/Low", 2, "#10b981"))
        
        main_layout.addLayout(stats_layout)
        
        # Filter Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px;")
        tb_layout = QHBoxLayout(toolbar)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search rules by ID or name...")
        self.search_box.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #f8fafc;")
        self.search_box.textChanged.connect(self.load_table_data)
        tb_layout.addWidget(self.search_box, 2)
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItem("All Categories")
        for cat in RuleCategory:
            self.cat_combo.addItem(cat.value)
        self.cat_combo.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.cat_combo.currentIndexChanged.connect(self.load_table_data)
        tb_layout.addWidget(self.cat_combo, 1)
        
        main_layout.addWidget(toolbar)
        
        # Table Widget
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Rule ID", "Rule Name", "Category", "Severity", "Standard", "Enabled"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 10px; font-weight: bold; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        
        main_layout.addWidget(self.table)
        self.load_table_data()

    def load_table_data(self):
        self.table.setRowCount(0)
        rules = self.engine.registry.get_all_rules()
        search_text = self.search_box.text().lower()
        selected_cat = self.cat_combo.currentText()
        
        row_idx = 0
        for r in rules:
            if search_text and (search_text not in r.rule_id.lower() and search_text not in r.rule_name.lower()):
                continue
            if selected_cat != "All Categories" and r.category.value != selected_cat:
                continue

            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(r.rule_id))
            self.table.setItem(row_idx, 1, QTableWidgetItem(r.rule_name))
            self.table.setItem(row_idx, 2, QTableWidgetItem(r.category.value))
            self.table.setItem(row_idx, 3, QTableWidgetItem(r.severity.value))
            self.table.setItem(row_idx, 4, QTableWidgetItem(r.accounting_standard))
            
            chk = QCheckBox()
            chk.setChecked(r.enabled)
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
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        from PySide6.QtWidgets import QMessageBox
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_RULES):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to manage audit rules.")
            self.load_table_data()
            return
        self.engine.registry.set_rule_enabled(rule_id, enabled)
