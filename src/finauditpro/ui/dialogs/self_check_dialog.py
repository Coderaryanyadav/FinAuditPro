"""Environment Self-Check Diagnostics Dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.environment_service import EnvironmentChecker


class SelfCheckDialog(QDialog):
    """Dialog displaying diagnostic results of launch-time environment prerequisite probes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.checker = EnvironmentChecker()

        self.setWindowTitle("FinAuditPro System Environment Self-Check")
        self.resize(680, 420)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("<h3>System Environment Prerequisite Diagnostics</h3>"))

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Prerequisite Name", "Status", "Probe Message", "Actionable Remediation"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.refresh_btn = QPushButton("Re-Run Diagnostics")
        self.refresh_btn.clicked.connect(self._run_check)
        layout.addWidget(self.refresh_btn)

        self._run_check()

    def _run_check(self) -> None:
        status_dto = self.checker.run_all_checks()
        self.table.setRowCount(len(status_dto.items))

        for row, item in enumerate(status_dto.items):
            status_item = QTableWidgetItem(item.status)
            if item.status == "PASS":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif item.status == "WARN":
                status_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                status_item.setForeground(Qt.GlobalColor.red)

            self.table.setItem(row, 0, QTableWidgetItem(item.name))
            self.table.setItem(row, 1, status_item)
            self.table.setItem(row, 2, QTableWidgetItem(item.message))
            self.table.setItem(row, 3, QTableWidgetItem(item.remediation or "—"))
