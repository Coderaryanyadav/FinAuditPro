"""
FinAuditPro Design System — Core Component Library.
Reusable, polished UI primitives for enterprise audit applications.
Adheres to Apple macOS & Linear/Stripe design standards.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QProgressBar, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor

class MetricCard(QFrame):
    """Uniform Enterprise Metric Block (100px fixed height)."""
    def __init__(self, title: str, value: str, subtitle: str, badge_bg: str, badge_fg: str, accent_hex: str = "#007AFF", icon_str: str = "", parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(104)
        self.setObjectName("metricCard")
        self.setStyleSheet("""
            QFrame#metricCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(4)
        
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(6)

        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        text_sub = "#8E8E93" if is_dark else "#86868B"

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {text_clr}; border: none; background: transparent; background-color: transparent; letter-spacing: -0.8px;")
        
        self.badge_lbl = QLabel(subtitle)
        self.badge_lbl.setStyleSheet(f"color: {badge_fg}; font-size: 10px; font-weight: 600; background-color: {badge_bg}; padding: 3px 8px; border-radius: 6px; border: none;")
        
        top_row.addWidget(self.val_lbl)
        top_row.addStretch()
        top_row.addWidget(self.badge_lbl, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet(f"color: {text_sub}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; border: none; background: transparent; background-color: transparent;")
        
        layout.addLayout(top_row)
        layout.addWidget(self.title_lbl)

    def update_value(self, value):
        self.val_lbl.setText(str(value))

class StatusBadge(QLabel):
    """Semantic status pill badge."""
    def __init__(self, text: str, bg_color: str = "rgba(0, 122, 255, 0.1)", fg_color: str = "#007AFF", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {fg_color}; background-color: {bg_color}; padding: 3px 8px; border-radius: 6px; border: none;")

class RiskBadge(QLabel):
    """Semantic risk level pill badge."""
    def __init__(self, level: str, parent=None):
        super().__init__(level.upper(), parent)
        is_dark = ThemeManager().is_dark
        if level.lower() in ("high", "critical"):
            bg, fg = ("rgba(255, 69, 58, 0.2)", "#FF453A") if is_dark else ("rgba(255, 59, 48, 0.1)", "#FF3B30")
        elif level.lower() in ("medium", "warning"):
            bg, fg = ("rgba(255, 214, 10, 0.2)", "#FFD60A") if is_dark else ("rgba(255, 159, 10, 0.1)", "#FF9F0A")
        else:
            bg, fg = ("rgba(48, 209, 88, 0.2)", "#30D158") if is_dark else ("rgba(52, 199, 89, 0.1)", "#34C759")
        self.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {fg}; background-color: {bg}; padding: 2px 7px; border-radius: 4px; border: none;")

class EmptyStateWidget(QVBoxLayout):
    """Compact, centered empty state layout container."""
    def __init__(self, title="Nothing here yet", description="No records found.", icon="○", action_text=None, action_callback=None, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(16, 14, 16, 14)
        self.setSpacing(4)

        is_dark = ThemeManager().is_dark
        text_clr = "#F5F5F7" if is_dark else "#1D1D1F"
        text_sub = "#8E8E93" if is_dark else "#86868B"

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size: 22px; border: none; background: transparent; background-color: transparent; color: {text_sub};")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {text_clr}; border: none; background: transparent; background-color: transparent;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(f"font-size: 12px; color: {text_sub}; border: none; background: transparent; background-color: transparent; line-height: 1.4;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setMaximumWidth(520)
        desc_lbl.setMinimumHeight(40)

        self.addWidget(icon_lbl)
        self.addWidget(title_lbl)
        self.addWidget(desc_lbl)

        if action_text and action_callback:
            btn = QPushButton(action_text)
            btn.setObjectName("primaryBtn")
            btn.setFixedWidth(160)
            btn.clicked.connect(action_callback)
            btn.setStyleSheet("margin-top: 8px;")
            self.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

class PrimaryButton(QPushButton):
    """Apple-style primary action button."""
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("primaryBtn")
        self.setStyleSheet("""
            QPushButton#primaryBtn {
                background-color: #007AFF;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 13px;
                border: none;
                border-radius: 8px;
                padding: 7px 14px;
            }
            QPushButton#primaryBtn:hover {
                background-color: #0062CC;
            }
            QPushButton#primaryBtn:pressed {
                background-color: #004999;
            }
        """)
