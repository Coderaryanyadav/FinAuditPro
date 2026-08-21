"""UI Theme, styling tokens, and reusable Qt components for FinAuditPro."""

from typing import Any

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class Colors:
    DARK_BG = "#0f1117"
    DARK_SURFACE = "#181b22"
    DARK_SURFACE_ALT = "#222732"
    BORDER = "#2a303c"
    BORDER_SUBTLE = "#1e2430"
    PRIMARY = "#0284c7"
    PRIMARY_HOVER = "#0369a1"
    ACCENT = "#38bdf8"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    DANGER = "#ef4444"
    RISK_LOW = "#38bdf8"
    RISK_MEDIUM = "#f59e0b"
    RISK_HIGH = "#f97316"
    RISK_CRITICAL = "#ef4444"
    TEXT_PRIMARY = "#f8fafc"
    TEXT_SECONDARY = "#94a3b8"
    TEXT_MUTED = "#64748b"


DARK_STYLESHEET = """
QMainWindow {
    background-color: #0f1117;
}

QWidget {
    font-family: "-apple-system", "BlinkMacSystemFont", "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
    font-size: 13px;
    color: #f8fafc;
}

QDialog {
    background-color: #181b22;
    border: 1px solid #2a303c;
    border-radius: 8px;
}

QFrame {
    background-color: transparent;
    color: #f8fafc;
}

QGroupBox {
    background-color: #181b22;
    border: 1px solid #2a303c;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 12px;
    font-weight: 700;
    color: #f8fafc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #38bdf8;
}

/* Sidebar Navigation */
#Sidebar {
    background-color: #12141a;
    border-right: 1px solid #2a303c;
    min-width: 230px;
    max-width: 230px;
}

#Sidebar QPushButton {
    background-color: transparent;
    color: #94a3b8;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    text-align: left;
    font-weight: 500;
    font-size: 13px;
}

#Sidebar QPushButton:hover {
    background-color: #1c202b;
    color: #f8fafc;
}

#Sidebar QPushButton:checked {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 600;
}

/* Header Context Bar */
#HeaderContextBar {
    background-color: #181b22;
    border-bottom: 1px solid #2a303c;
    padding: 8px 16px;
}

#HeaderTitle {
    font-size: 15px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #38bdf8;
}

#HeaderContextLabel {
    font-size: 12px;
    font-weight: 500;
    color: #94a3b8;
}

/* Buttons */
QPushButton {
    background-color: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #0369a1;
}

QPushButton:pressed {
    background-color: #075985;
}

QPushButton#SecondaryButton {
    background-color: #1e2430;
    color: #f8fafc;
    border: 1px solid #2a303c;
}

QPushButton#SecondaryButton:hover {
    background-color: #2a303c;
}

/* Inputs & Form Controls */
QLineEdit, QTextEdit, QComboBox {
    background-color: #0f1117;
    color: #f8fafc;
    border: 1px solid #2a303c;
    border-radius: 6px;
    padding: 6px 10px;
}

QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #38bdf8;
}

/* Tables */
QTableWidget {
    background-color: #14171f;
    gridline-color: #222732;
    border: 1px solid #2a303c;
    border-radius: 6px;
    color: #f8fafc;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #181b22;
    color: #94a3b8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2a303c;
    font-weight: 600;
    font-size: 12px;
}

/* ScrollBars */
QScrollBar:vertical {
    background-color: #0f1117;
    width: 8px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #2a303c;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #64748b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""


class CardWidget(QFrame):
    """Reusable styled card container."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #181b22;
                border: 1px solid #2a303c;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(14, 14, 14, 14)
        self.content_layout.setSpacing(8)

        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(
                "font-size: 13px; font-weight: 700; color: #f8fafc; border: none;"
            )
            self.content_layout.addWidget(self.title_label)


class MetricCard(QFrame):
    """Card showing KPI title, primary metric, and subtitle."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = Colors.ACCENT,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #181b22;
                border: 1px solid #2a303c;
                border-radius: 8px;
                border-left: 4px solid {accent_color};
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)

        title_lbl = QLabel(title.upper())
        title_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748b; border: none;")

        self.val_lbl = QLabel(value)
        self.val_lbl.setStyleSheet(
            "font-size: 22px; font-weight: 800; color: #f8fafc; border: none;"
        )

        layout.addWidget(title_lbl)
        layout.addWidget(self.val_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; border: none;")
            layout.addWidget(sub_lbl)

    def set_value(self, value: str) -> None:
        self.val_lbl.setText(value)


class StatusBadge(QLabel):
    """Pill badge displaying status text with semantic background and border colors."""

    def __init__(self, text: str, status_type: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        styles = {
            "success": "background-color: #064e3b; color: #34d399; border: 1px solid #059669;",
            "warning": "background-color: #78350f; color: #fbbf24; border: 1px solid #d97706;",
            "danger": "background-color: #7f1d1d; color: #f87171; border: 1px solid #dc2626;",
            "info": "background-color: #0c4a6e; color: #38bdf8; border: 1px solid #0284c7;",
            "muted": "background-color: #1e293b; color: #94a3b8; border: 1px solid #334155;",
        }
        style = styles.get(status_type, styles["info"])
        self.setStyleSheet(f"QLabel {{ {style} border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 600; }}")


def apply_theme(app: Any) -> None:
    """Apply default Qt palette and custom stylesheet."""
    app.setStyleSheet(DARK_STYLESHEET)
