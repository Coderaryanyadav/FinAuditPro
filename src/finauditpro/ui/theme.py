"""
FinAuditPro Enterprise — Design System Tokens & Theme Manager
Single source of truth for visual tokens. Light mode default, full dark mode support.
"""

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class LightColors:
    """Apple macOS Light mode semantic design tokens."""
    BG_BASE     = "#F5F5F7"
    BG_SURFACE  = "#FFFFFF"
    BG_ELEVATED = "#FFFFFF"
    BG_SUBTLE   = "#F2F2F7"
    BG_HOVER    = "#E5E5EA"

    BORDER_DEFAULT = "#E5E5EA"
    BORDER_STRONG  = "#D2D2D7"
    BORDER_FOCUS   = "#007AFF"

    TEXT_PRIMARY     = "#1D1D1F"
    TEXT_SECONDARY   = "#6E6E73"
    TEXT_MUTED       = "#86868B"
    TEXT_DISABLED    = "#C7C7CC"
    TEXT_PLACEHOLDER = "#AEAEB2"

    ACCENT         = "#007AFF"
    ACCENT_HOVER   = "#0062CC"
    ACCENT_PRESSED = "#004999"
    ACCENT_SUBTLE  = "rgba(0, 122, 255, 0.1)"
    ACCENT_BORDER  = "rgba(0, 122, 255, 0.25)"

    SUCCESS        = "#34C759"
    SUCCESS_SUBTLE = "rgba(52, 199, 89, 0.1)"
    SUCCESS_BORDER = "rgba(52, 199, 89, 0.25)"

    WARNING        = "#FF9F0A"
    WARNING_SUBTLE = "rgba(255, 159, 10, 0.1)"
    WARNING_BORDER = "rgba(255, 159, 10, 0.25)"

    DANGER         = "#FF3B30"
    DANGER_SUBTLE  = "rgba(255, 59, 48, 0.1)"
    DANGER_BORDER  = "rgba(255, 59, 48, 0.25)"

    INFO           = "#5856D6"
    INFO_SUBTLE    = "rgba(88, 86, 214, 0.1)"
    INFO_BORDER    = "rgba(88, 86, 214, 0.25)"

    NAV_BG          = "#F5F5F7"
    NAV_BORDER      = "#E5E5EA"
    NAV_TEXT        = "#6E6E73"
    NAV_TEXT_ACTIVE = "#007AFF"
    NAV_ACTIVE_BG   = "rgba(0, 122, 255, 0.12)"
    NAV_HOVER_BG    = "rgba(0, 0, 0, 0.04)"
    NAV_ACCENT_DOT  = "#007AFF"


class DarkColors:
    """Apple macOS Dark mode semantic design tokens."""
    BG_BASE     = "#1E1E1E"
    BG_SURFACE  = "#2D2D2F"
    BG_ELEVATED = "#3A3A3C"
    BG_SUBTLE   = "#2C2C2E"
    BG_HOVER    = "#3A3A3C"

    BORDER_DEFAULT = "#38383A"
    BORDER_STRONG  = "#48484A"
    BORDER_FOCUS   = "#0A84FF"

    TEXT_PRIMARY     = "#FFFFFF"
    TEXT_SECONDARY   = "#EBEBF5"
    TEXT_MUTED       = "#8E8E93"
    TEXT_DISABLED    = "#636366"
    TEXT_PLACEHOLDER = "#48484A"

    ACCENT         = "#0A84FF"
    ACCENT_HOVER   = "#007AFF"
    ACCENT_PRESSED = "#0062CC"
    ACCENT_SUBTLE  = "rgba(10, 132, 255, 0.15)"
    ACCENT_BORDER  = "rgba(10, 132, 255, 0.3)"

    SUCCESS        = "#30D158"
    SUCCESS_SUBTLE = "rgba(48, 209, 88, 0.15)"
    SUCCESS_BORDER = "rgba(48, 209, 88, 0.3)"

    WARNING        = "#FFD60A"
    WARNING_SUBTLE = "rgba(255, 214, 10, 0.15)"
    WARNING_BORDER = "rgba(255, 214, 10, 0.3)"

    DANGER         = "#FF453A"
    DANGER_SUBTLE  = "rgba(255, 69, 58, 0.15)"
    DANGER_BORDER  = "rgba(255, 69, 58, 0.3)"

    INFO           = "#5E5CE6"
    INFO_SUBTLE    = "rgba(94, 92, 230, 0.15)"
    INFO_BORDER    = "rgba(94, 92, 230, 0.3)"

    NAV_BG          = "#1E1E1E"
    NAV_BORDER      = "#2C2C2E"
    NAV_TEXT        = "#8E8E93"
    NAV_TEXT_ACTIVE = "#0A84FF"
    NAV_ACTIVE_BG   = "rgba(10, 132, 255, 0.18)"
    NAV_HOVER_BG    = "rgba(255, 255, 255, 0.05)"
    NAV_ACCENT_DOT  = "#0A84FF"


Colors = LightColors


class ThemeManager(QObject):
    """Singleton Theme Manager controlling global application light/dark state."""

    theme_changed = Signal(bool)  # True = Dark, False = Light
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
    """Re-usable styled card surface for content panels."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contentCard")
        self.setStyleSheet("""
            QFrame#contentCard {
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        if title:
            header_lbl = QLabel(title)
            header_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #1D1D1F;")
            layout.addWidget(header_lbl)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(10)
        layout.addWidget(self.content_widget)


class MetricCard(QFrame):
    """Stat summary card for KPI dashboard metrics."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        accent_color: str = "#007AFF",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setStyleSheet(f"""
            QFrame#metricCard {{
                background-color: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                border-left: 4px solid {accent_color};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        self.title_lbl = QLabel(title)
        self.title_lbl.setObjectName("metricTitle")
        self.value_lbl = QLabel(value)
        self.value_lbl.setObjectName("metricValue")
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 11px; color: #86868B;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addWidget(self.sub_lbl)

    def set_value(self, val: str) -> None:
        self.value_lbl.setText(val)


class Fonts:
    FAMILY      = "'SF Pro Text', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif"
    FAMILY_MONO = "'SF Mono', 'Menlo', 'Consolas', monospace"


class StatusBadge(QLabel):
    """Pill badge for status indication."""

    def __init__(self, text: str, status_type: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        styles = {
            "success": "color: #34C759; background: rgba(52, 199, 89, 0.12); border: 1px solid rgba(52, 199, 89, 0.25);",
            "warning": "color: #FF9F0A; background: rgba(255, 159, 10, 0.12); border: 1px solid rgba(255, 159, 10, 0.25);",
            "danger": "color: #FF3B30; background: rgba(255, 59, 48, 0.12); border: 1px solid rgba(255, 59, 48, 0.25);",
            "info": "color: #007AFF; background: rgba(0, 122, 255, 0.12); border: 1px solid rgba(0, 122, 255, 0.25);",
        }
        st = styles.get(status_type, styles["info"])
        self.setStyleSheet(f"font-size: 11px; font-weight: 700; border-radius: 6px; padding: 3px 8px; {st}")
