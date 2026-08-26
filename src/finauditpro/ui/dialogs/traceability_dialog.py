"""Dialog rendering the visual 2-way Audit Traceability Lineage Graph."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.audit_planning_dtos import TraceabilityGraphDTO
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.ui.theme import CardWidget


class TraceabilityDialog(QDialog):
    """Modal dialog displaying two-way audit traceability DAG graph."""

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

        self.setWindowTitle("Audit Traceability Graph — End-to-End SA Lineage")
        self.resize(850, 520)

        self._init_ui()
        self._load_graph()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("Audit Evidence Lineage Graph: Finding ↔ Procedure ↔ Risk ↔ Assertion ↔ Evidence")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #2563EB;")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Lineage Nodes Table
        table_card = CardWidget("TRACEABILITY NODES (DAG)")
        self.nodes_table = QTableWidget()
        self.nodes_table.setColumnCount(4)
        self.nodes_table.setHorizontalHeaderLabels(
            ["NODE TYPE", "IDENTIFIER / LABEL", "STATUS / ROMM", "SOURCE"]
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
        self.nodes_table.setAlternatingRowColors(True)
        self.nodes_table.itemSelectionChanged.connect(self._on_node_selected)
        table_card.content_layout.addWidget(self.nodes_table)
        splitter.addWidget(table_card)

        # Right: Relationship Flow Preview
        preview_card = CardWidget("AUDIT LINEAGE FLOW (RELATIONSHIPS)")
        self.flow_text = QTextEdit()
        self.flow_text.setReadOnly(True)
        self.flow_text.setStyleSheet("""
            QTextEdit {
                background: #0f172a;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #e2e8f0;
                font-family: 'SF Mono', Menlo, Consolas, monospace;
                font-size: 11px;
                padding: 10px;
            }
        """)
        preview_card.content_layout.addWidget(self.flow_text)
        splitter.addWidget(preview_card)

        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        layout.addWidget(splitter, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Close Graph")
        close_btn.setObjectName("SecondaryButton")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _load_graph(self) -> None:
        self.graph: TraceabilityGraphDTO = self.traceability_service.build_finding_traceability(
            self.engagement_id, self.finding_id
        )

        self.nodes_table.setRowCount(0)
        type_badges = {
            "Finding": "🚨 Finding",
            "Procedure": "⚙️ Procedure",
            "Risk": "⚠️ Risk",
            "Assertion": "🏷️ Assertion",
            "DocumentPage": "📄 PDF Page",
            "FinancialRow": "🔢 Ledger Row",
            "WorkingPaper": "📋 Workpaper",
        }

        for row, node in enumerate(self.graph.nodes):
            self.nodes_table.insertRow(row)
            n_type = node.get("type", "-")
            badge = type_badges.get(n_type, n_type)

            it_type = QTableWidgetItem(badge)
            it_label = QTableWidgetItem(node.get("label", "-"))
            status = node.get("status") or node.get("severity") or node.get("romm") or "-"
            it_status = QTableWidgetItem(status)
            it_source = QTableWidgetItem(node.get("source", "-"))

            self.nodes_table.setItem(row, 0, it_type)
            self.nodes_table.setItem(row, 1, it_label)
            self.nodes_table.setItem(row, 2, it_status)
            self.nodes_table.setItem(row, 3, it_source)

        # Build Flow Graph Summary Text
        flow_lines = [
            "===========================================================",
            " AUDIT EVIDENCE LINEAGE GRAPH (SA 230 / SA 500 / SA 315)",
            "===========================================================\n",
        ]

        if self.graph.edges:
            flow_lines.append("--- DIRECTED RELATIONSHIPS (EDGES) ---")
            for edge in self.graph.edges:
                src = edge.get("source", "")
                tgt = edge.get("target", "")
                rel = edge.get("relation", "CONNECTED_TO")
                flow_lines.append(f"• [{src}] ──({rel})──> [{tgt}]")
        else:
            flow_lines.append("• Single isolated node in current audit subgraph.")

        self.flow_text.setText("\n".join(flow_lines))

    def _on_node_selected(self) -> None:
        selected_rows = self.nodes_table.selectedItems()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < len(self.graph.nodes):
            node = self.graph.nodes[row]
            lines = [
                "===========================================================",
                f" NODE DETAILS: {node.get('label', '')}",
                f" Type: {node.get('type', '')} | ID: {node.get('id', '')}",
                "===========================================================\n",
            ]
            for k, v in node.items():
                if k not in ("id", "type", "label"):
                    lines.append(f"• {k.replace('_', ' ').title()}: {v}")
            self.flow_text.setText("\n".join(lines))
