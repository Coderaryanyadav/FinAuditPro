"""Dialog rendering the 2-way Audit Traceability Navigation Graph."""

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_planning_dtos import TraceabilityGraphDTO
from finauditpro.application.services.traceability_service import TraceabilityService


class TraceabilityDialog(QDialog):
    """Modal dialog displaying two-way audit traceability graph."""

    def __init__(
        self,
        traceability_service: TraceabilityService,
        engagement_id: str,
        finding_id: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.traceability_service = traceability_service
        self.engagement_id = engagement_id
        self.finding_id = finding_id

        self.setWindowTitle("Audit Traceability Graph — End-to-End Lineage")
        self.resize(750, 480)

        self._init_ui()
        self._load_graph()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Traceability Graph: Finding ↔ Procedure ↔ Risk ↔ Assertion ↔ Evidence")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(4)
        self.nodes_table.setHorizontalHeaderLabels(
            ["Node Type", "Identifier / Label", "Detail / Status", "Source"]
        )
        self.nodes_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.nodes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.nodes_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self.nodes_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self.nodes_table.verticalHeader().setVisible(False)
        layout.addWidget(self.nodes_table)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close Graph")
        close_btn.setObjectName("SecondaryButton")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_graph(self) -> None:
        graph: TraceabilityGraphDTO = self.traceability_service.build_finding_traceability(
            self.engagement_id, self.finding_id
        )

        self.nodes_table.setRowCount(0)
        for row, node in enumerate(graph.nodes):
            self.nodes_table.insertRow(row)
            self.nodes_table.setItem(row, 0, QTableWidgetItem(node.get("type", "-")))
            self.nodes_table.setItem(row, 1, QTableWidgetItem(node.get("label", "-")))
            status = node.get("status") or node.get("severity") or node.get("romm") or "-"
            self.nodes_table.setItem(row, 2, QTableWidgetItem(status))
            self.nodes_table.setItem(row, 3, QTableWidgetItem(node.get("source", "-")))
