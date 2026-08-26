"""
FinAuditPro Enterprise — Design System Tokens, Theme Manager & UI Kit
Single source of truth for visual tokens, typography, badges, INR currency formatting, and empty/loading states.
"""

from typing import Any

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def format_inr(val: Any) -> str:
    """Format numeric values according to Indian numbering system (e.g. ₹1,25,000.00)."""
    try:
        if val is None or val == "": return "₹0.00"
        if isinstance(val, str): val = float(val.replace("₹", "").replace(",", "").strip() or 0)
        neg = val < 0
        s = f"{abs(float(val)):.2f}"
        int_part, dec_part = s.split(".")
        if len(int_part) <= 3:
            res = int_part
        else:
            last3, rest = int_part[-3:], int_part[:-3]
            chunks: list[str] = []
            while len(rest) > 2:
                chunks.insert(0, rest[-2:])
                rest = rest[:-2]
            if rest: chunks.insert(0, rest)
            res = ",".join(chunks) + "," + last3
        return f"{'-' if neg else ''}₹{res}.{dec_part}"
    except Exception:
        return f"₹{val}"


class LightColors:
    BG_BASE, BG_SURFACE, BG_ELEVATED, BG_SUBTLE, BG_HOVER = "#F8FAFC", "#FFFFFF", "#FFFFFF", "#F1F5F9", "#E2E8F0"
    BORDER_DEFAULT, BORDER_STRONG, BORDER_FOCUS = "#E2E8F0", "#CBD5E1", "#2563EB"
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DISABLED = "#0F172A", "#475569", "#64748B", "#94A3B8"
    ACCENT, ACCENT_HOVER, ACCENT_SUBTLE, ACCENT_BORDER = "#2563EB", "#1D4ED8", "rgba(37, 99, 235, 0.1)", "rgba(37, 99, 235, 0.25)"
    SUCCESS, SUCCESS_SUBTLE = "#16A34A", "rgba(22, 163, 74, 0.1)"
    WARNING, WARNING_SUBTLE = "#D97706", "rgba(217, 119, 6, 0.1)"
    DANGER, DANGER_SUBTLE = "#DC2626", "rgba(220, 38, 38, 0.1)"
    INFO, INFO_SUBTLE = "#4F46E5", "rgba(79, 70, 229, 0.1)"
    NAV_BG, NAV_BORDER, NAV_TEXT, NAV_TEXT_ACTIVE, NAV_ACTIVE_BG = "#FFFFFF", "#E2E8F0", "#475569", "#2563EB", "#EFF6FF"


class DarkColors:
    BG_BASE, BG_SURFACE, BG_ELEVATED, BG_SUBTLE, BG_HOVER = "#0F172A", "#1E293B", "#334155", "#1E293B", "#334155"
    BORDER_DEFAULT, BORDER_STRONG, BORDER_FOCUS = "#334155", "#475569", "#3B82F6"
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_DISABLED = "#F8FAFC", "#CBD5E1", "#94A3B8", "#64748B"
    ACCENT, ACCENT_HOVER, ACCENT_SUBTLE, ACCENT_BORDER = "#3B82F6", "#2563EB", "rgba(59, 130, 246, 0.15)", "rgba(59, 130, 246, 0.3)"
    SUCCESS, SUCCESS_SUBTLE = "#22C55E", "rgba(34, 197, 94, 0.15)"
    WARNING, WARNING_SUBTLE = "#F59E0B", "rgba(245, 158, 11, 0.15)"
    DANGER, DANGER_SUBTLE = "#EF4444", "rgba(239, 68, 68, 0.15)"
    INFO, INFO_SUBTLE = "#6366F1", "rgba(99, 102, 241, 0.15)"
    NAV_BG, NAV_BORDER, NAV_TEXT, NAV_TEXT_ACTIVE, NAV_ACTIVE_BG = "#0F172A", "#1E293B", "#94A3B8", "#3B82F6", "rgba(59, 130, 246, 0.18)"


Colors = LightColors


class ThemeManager(QObject):
    theme_changed = Signal(bool)
    _instance: Any = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._is_dark = False
        return cls._instance  # type: ignore[no-any-return]

    @property

    def is_dark(self) -> bool:
        return bool(getattr(self, "_is_dark", False))

    @property
    def tokens(self) -> Any:
        return DarkColors if self.is_dark else LightColors

    def set_dark_mode(self, enabled: bool) -> None:
        if getattr(self, "_is_dark", False) != enabled:
            self._is_dark = enabled
            global Colors
            Colors = DarkColors if enabled else LightColors  # type: ignore[assignment]
            self.theme_changed.emit(enabled)

    def toggle_theme(self) -> None:
        self.set_dark_mode(not self.is_dark)


class CardWidget(QFrame):
    def __init__(self, title: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("contentCard")
        self.setStyleSheet("QFrame#contentCard { background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        if title:
            h_row = QHBoxLayout()
            h_lbl = QLabel(title)
            h_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #64748B; border: none; background: transparent; letter-spacing: 0.5px;")
            h_row.addWidget(h_lbl)
            h_row.addStretch()
            layout.addLayout(h_row)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent; border: none;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(6)
        layout.addWidget(self.content_widget)


class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, title: str, value: str, subtitle: str = "", accent_color: str = "#2563EB", action_text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setFixedHeight(88)
        self.setStyleSheet(f"QFrame#metricCard {{ background-color: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; border-top: 2px solid {accent_color}; }}")
        if action_text:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(2)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #64748B; border: none; background: transparent; letter-spacing: 0.5px;")
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet("font-size: 24px; font-weight: 600; color: #0F172A; border: none; background: transparent; letter-spacing: -0.6px;")
        sub_row = QHBoxLayout()
        sub_row.setContentsMargins(0, 0, 0, 0)
        self.sub_lbl = QLabel(subtitle)
        self.sub_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; border: none; background: transparent;")
        sub_row.addWidget(self.sub_lbl)
        if action_text:
            sub_row.addStretch()
            self.act_lbl = QLabel(action_text)
            self.act_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #2563EB; border: none; background: transparent;")
            self.act_lbl.setCursor(Qt.CursorShape.PointingHandCursor)
            sub_row.addWidget(self.act_lbl)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        layout.addLayout(sub_row)

    def mousePressEvent(self, event: Any) -> None:
        super().mousePressEvent(event)
        self.clicked.emit()

    def set_value(self, val: str) -> None:
        self.value_lbl.setText(val)



class Fonts:
    FAMILY = "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif"
    FAMILY_MONO = "'JetBrains Mono', 'SF Mono', 'Menlo', 'Consolas', monospace"


class StatusBadge(QLabel):
    def __init__(self, text: str, status_type: str = "info", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self._update_style(status_type)

    def set_status(self, text: str, status_type: str = "info") -> None:
        self.setText(text)
        self._update_style(status_type)

    def _update_style(self, status_type: str) -> None:
        st = status_type.lower()
        if st in ("success", "completed", "signed off", "matched", "ready", "indexed", "compliant", "verified", "tied out"):
            style = "color: #15803D; background: #DCFCE7; border: 1px solid #BBF7D0;"
        elif st in ("warning", "in progress", "open", "medium", "rate mismatch", "mismatch", "unconfirmed", "under review"):
            style = "color: #B45309; background: #FEF3C7; border: 1px solid #FDE68A;"
        elif st in ("danger", "high", "critical", "failed", "quarantined", "missing in 2b", "ineligible", "difference"):
            style = "color: #B91C1C; background: #FEE2E2; border: 1px solid #FECACA;"
        elif st in ("info", "planning", "draft", "low", "prepared"):
            style = "color: #1D4ED8; background: #DBEAFE; border: 1px solid #BFDBFE;"
        else:
            style = "color: #475569; background: #F1F5F9; border: 1px solid #E2E8F0;"
        self.setStyleSheet(f"font-size: 11px; font-weight: 500; border-radius: 4px; padding: 2px 8px; {style}")


class RiskBadge(QLabel):
    def __init__(self, risk_level: str, parent: QWidget | None = None) -> None:
        super().__init__(f"● {risk_level}", parent)
        rl = risk_level.lower()
        if "critical" in rl or "high" in rl: st = "color: #DC2626; background: #FEE2E2; border: 1px solid #FECACA;"
        elif "medium" in rl or "moderate" in rl: st = "color: #D97706; background: #FEF3C7; border: 1px solid #FDE68A;"
        elif "low" in rl: st = "color: #15803D; background: #DCFCE7; border: 1px solid #BBF7D0;"
        else: st = "color: #64748B; background: #F1F5F9; border: 1px solid #E2E8F0;"
        self.setStyleSheet(f"font-size: 11px; font-weight: 500; border-radius: 4px; padding: 2px 8px; {st}")


class EmptyStateWidget(QFrame):
    def __init__(self, title: str, description: str, action_text: str = "", action_callback: object = None, glyph: str = "◇", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("emptyStateWidget")
        self.setStyleSheet("QFrame#emptyStateWidget { background-color: #FFFFFF; border: 1px dashed #CBD5E1; border-radius: 8px; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 36, 32, 36)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g_lbl = QLabel(glyph)
        g_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        g_lbl.setStyleSheet("font-size: 22px; color: #94A3B8; background: #F1F5F9; border-radius: 18px; width: 36px; height: 36px;")
        layout.addWidget(g_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        t_lbl = QLabel(title)
        t_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #0F172A; border: none; background: transparent;")
        layout.addWidget(t_lbl)
        d_lbl = QLabel(description)
        d_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d_lbl.setWordWrap(True)
        d_lbl.setMaximumWidth(680)
        d_lbl.setStyleSheet("font-size: 12px; color: #64748B; border: none; background: transparent; line-height: 1.4;")
        layout.addWidget(d_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        if action_text and action_callback:
            btn = QPushButton(action_text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 500; border-radius: 6px; padding: 7px 16px; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
            btn.clicked.connect(action_callback)
            layout.addSpacing(4)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


class LoadingStateWidget(QFrame):
    def __init__(self, message: str = "Loading audit records...", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl = QLabel("")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 20px;")
        msg = QLabel(message)
        msg.setStyleSheet("font-size: 13px; font-weight: 500; color: #64748B;")
        layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)


class ErrorStateWidget(QFrame):
    def __init__(self, title: str = "Unable to load data", message: str = "Local audit database could not be queried. No changes were made.", retry_callback: object = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 32, 24, 32)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t_lbl = QLabel(f"{title}")
        t_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #DC2626;")
        m_lbl = QLabel(message)
        m_lbl.setWordWrap(True)
        m_lbl.setStyleSheet("font-size: 12px; color: #64748B; max-width: 420px;")
        layout.addWidget(t_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(m_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        if retry_callback:
            btn = QPushButton("Retry")
            btn.setStyleSheet("background-color: #DC2626; color: #FFFFFF; font-size: 13px; font-weight: 500; border-radius: 6px; padding: 6px 14px;")
            btn.clicked.connect(retry_callback)
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)


class PageHeader(QFrame):
    def __init__(self, title: str, subtitle: str = "", action_text: str = "", action_callback: object = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("background: transparent; border: none;")
        self.action_layout = QHBoxLayout(self)
        self.action_layout.setContentsMargins(0, 0, 0, 0)
        self.action_layout.setSpacing(12)
        left_v = QVBoxLayout()
        left_v.setSpacing(2)

        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 600; color: #0F172A; letter-spacing: -0.4px; border: none; background: transparent;")
        left_v.addWidget(self.title_lbl)
        if subtitle:
            self.subtitle_lbl = QLabel(subtitle)
            self.subtitle_lbl.setStyleSheet("font-size: 12px; color: #64748B; border: none; background: transparent;")
            left_v.addWidget(self.subtitle_lbl)
        self.action_layout.addLayout(left_v)
        self.action_layout.addStretch()
        if action_text and action_callback:
            self.action_btn = QPushButton(action_text)
            self.action_btn.setObjectName("primaryButton")
            self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.action_btn.setStyleSheet("QPushButton { background-color: #2563EB; color: #FFFFFF; font-size: 13px; font-weight: 500; border-radius: 6px; padding: 7px 16px; border: none; } QPushButton:hover { background-color: #1D4ED8; }")
            self.action_btn.clicked.connect(action_callback)
            self.action_layout.addWidget(self.action_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

