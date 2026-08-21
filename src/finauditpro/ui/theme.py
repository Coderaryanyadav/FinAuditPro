"""
FinAuditPro Enterprise — Design System Tokens & Theme Manager
Single source of truth for visual tokens, typography, and status badges.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class LightColors:
    """Apple macOS / Linear Light mode semantic design tokens."""
    BG_BASE     = "#F8FAFC"
    BG_SURFACE  = "#FFFFFF"
    BG_ELEVATED = "#FFFFFF"
    BG_SUBTLE   = "#F1F5F9"
    BG_HOVER    = "#E2E8F0"

    BORDER_DEFAULT = "#E2E8F0"
    BORDER_STRONG  = "#CBD5E1"
    BORDER_FOCUS   = "#2563EB"

    TEXT_PRIMARY     = "#0F172A"
    TEXT_SECONDARY   = "#475569"
    TEXT_MUTED       = "#64748B"
    TEXT_DISABLED    = "#94A3B8"

    ACCENT         = "#2563EB"
    ACCENT_HOVER   = "#1D4ED8"
    ACCENT_SUBTLE  = "rgba(37, 99, 235, 0.1)"
    ACCENT_BORDER  = "rgba(37, 99, 235, 0.25)"

    SUCCESS        = "#16A34A"
    SUCCESS_SUBTLE = "rgba(22, 163, 74, 0.1)"

    WARNING        = "#D97706"
    WARNING_SUBTLE = "rgba(217, 119, 6, 0.1)"

    DANGER         = "#DC2626"
    DANGER_SUBTLE  = "rgba(220, 38, 38, 0.1)"

    INFO           = "#4F46E5"
    INFO_SUBTLE    = "rgba(79, 70, 229, 0.1)"

    NAV_BG          = "#FFFFFF"
    NAV_BORDER      = "#E2E8F0"
    NAV_TEXT        = "#475569"
    NAV_TEXT_ACTIVE = "#2563EB"
    NAV_ACTIVE_BG   = "#EFF6FF"


class DarkColors:
    """Apple macOS Dark mode semantic design tokens."""
    BG_BASE     = "#0F172A"
    BG_SURFACE  = "#1E293B"
    BG_ELEVATED = "#334155"
    BG_SUBTLE   = "#1E293B"
    BG_HOVER    = "#334155"

    BORDER_DEFAULT = "#334155"
    BORDER_STRONG  = "#475569"
    BORDER_FOCUS   = "#3B82F6"

    TEXT_PRIMARY     = "#F8FAFC"
    TEXT_SECONDARY   = "#CBD5E1"
    TEXT_MUTED       = "#94A3B8"
    TEXT_DISABLED    = "#64748B"

    ACCENT         = "#3B82F6"
    ACCENT_HOVER   = "#2563EB"
    ACCENT_SUBTLE  = "rgba(59, 130, 246, 0.15)"
    ACCENT_BORDER  = "rgba(59, 130, 246, 0.3)"

    SUCCESS        = "#22C55E"
    SUCCESS_SUBTLE = "rgba(34, 197, 94, 0.15)"

    WARNING        = "#F59E0B"
    WARNING_SUBTLE = "rgba(245, 158, 11, 0.15)"

    DANGER         = "#EF4444"
    DANGER_SUBTLE  = "rgba(239, 68, 68, 0.15)"

    INFO           = "#6366F1"
    INFO_SUBTLE    = "rgba(99, 102, 241, 0.15)"

    NAV_BG          = "#0F172A"
    NAV_BORDER      = "#1E293B"
    NAV_TEXT        = "#94A3B8"
    NAV_TEXT_ACTIVE = "#3B82F6"
    NAV_ACTIVE_BG   = "rgba(59, 130, 246, 0.18)"


Colors = LightColors


class ThemeManager(QObject):
    """Singleton Theme Manager controlling global application light/dark state."""

    theme_changed = Signal(bool)
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_dark = False
        return cls._instance

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    @property
    def tokens(self):
        return DarkColors if self._is_dark else LightColors

    def set_dark_mode(self, enabled: bool):
        if self._is_dark != enabled:
            self._is_dark = enabled
            global Colors
            Colors = DarkColors if enabled else LightColors
            self.theme_changed.emit(enabled)

    def toggle_theme(self):
        self.set_dark_mode(not self._is_dark)


class CardWidget(QFrame):
    """Re-usable styled card surface with subtle divider line."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contentCard")
        self.setStyleSheet("""
            QFrame#contentCard {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        if title:
            header_row = QHBoxLayout()
            header_lbl = QLabel(title)
            header_lbl.setStyleSheet(
                "font-size: 12px; font-weight: 800; color: #475569; border: none; background: transparent; letter-spacing: 0.6px;"
            )
            header_row.addWidget(header_lbl)
            header_row.addStretch()
            layout.addLayout(header_row)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        layout.addWidget(self.content_widget)


class MetricCard(QFrame):
    """Compact KPI summary module (90px height)."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = "#2563EB",
        action_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setFixedHeight(94)
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                border-left: 3px solid {accent_color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 10px; font-weight: 800; color: #64748B; border: none; background: transparent; letter-spacing: 0.6px;")
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #0F172A; border: none; background: transparent; letter-spacing: -0.6px;")

        sub_row = QHBoxLayout()
        sub_row.setContentsMargins(0, 0, 0, 0)
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #94A3B8; border: none; background: transparent;")
        sub_row.addWidget(self.sub_lbl)

        if action_text:
            sub_row.addStretch()
            self.act_lbl = QLabel(action_text)
            self.act_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #2563EB; border: none; background: transparent;")
            sub_row.addWidget(self.act_lbl)

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addLayout(sub_row)

    def set_value(self, val: str) -> None:
        self.value_lbl.setText(val)


class Fonts:
    FAMILY      = "'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif"
    FAMILY_MONO = "'SF Mono', 'Menlo', 'Consolas', monospace"


class StatusBadge(QLabel):
    """Subtle semantic status badge."""

    def __init__(self, text: str, status_type: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        styles = {
            "success": "color: #15803D; background: #DCFCE7; border: 1px solid #86EFAC;",
            "warning": "color: #B45309; background: #FEF3C7; border: 1px solid #FDE68A;",
            "danger": "color: #B91C1C; background: #FEE2E2; border: 1px solid #FCA5A5;",
            "info": "color: #1D4ED8; background: #DBEAFE; border: 1px solid #93C5FD;",
            "neutral": "color: #475569; background: #F1F5F9; border: 1px solid #E2E8F0;",
        }
        st = styles.get(status_type, styles["neutral"])
        self.setStyleSheet(f"font-size: 11px; font-weight: 700; border-radius: 6px; padding: 2px 8px; {st}")
