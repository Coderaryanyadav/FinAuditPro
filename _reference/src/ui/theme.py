"""
FinAuditPro V2 — Design System Tokens
Single source of truth for all visual decisions.
Light mode default. Full dark mode support.
"""
from PySide6.QtCore import QObject, Signal


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

    CHART_LINE  = "#007AFF"
    CHART_AREA  = "rgba(0, 122, 255, 0.08)"
    CHART_GRID  = "#E5E5EA"
    CHART_LABEL = "#86868B"

    # Legacy compat aliases
    PRIMARY           = "#007AFF"
    PRIMARY_DARK      = "#0062CC"
    PRIMARY_HOVER     = "#0062CC"
    PRIMARY_LIGHT     = "rgba(0, 122, 255, 0.1)"
    PRIMARY_BG_SUBTLE = "rgba(0, 122, 255, 0.08)"
    BG_MAIN           = "#F5F5F7"
    SURFACE_WHITE     = "#FFFFFF"
    SURFACE_CARD      = "#FFFFFF"
    BORDER_LIGHT      = "#E5E5EA"
    BORDER_INPUT      = "#D2D2D7"
    TEXT_MAIN         = "#1D1D1F"
    TEXT_SUBTLE       = "#6E6E73"
    HEADER_BG         = "#FFFFFF"
    HEADER_BORDER     = "#E5E5EA"


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

    CHART_LINE  = "#0A84FF"
    CHART_AREA  = "rgba(10, 132, 255, 0.12)"
    CHART_GRID  = "#38383A"
    CHART_LABEL = "#8E8E93"

    # Legacy compat
    PRIMARY           = "#0A84FF"
    PRIMARY_DARK      = "#007AFF"
    PRIMARY_HOVER     = "#007AFF"
    PRIMARY_LIGHT     = "rgba(10, 132, 255, 0.15)"
    PRIMARY_BG_SUBTLE = "rgba(10, 132, 255, 0.1)"
    BG_MAIN           = "#1E1E1E"
    SURFACE_WHITE     = "#2D2D2F"
    SURFACE_CARD      = "#2D2D2F"
    BORDER_LIGHT      = "#38383A"
    BORDER_INPUT      = "#48484A"
    TEXT_MAIN         = "#FFFFFF"
    TEXT_SUBTLE       = "#8E8E93"
    HEADER_BG         = "#2D2D2F"
    HEADER_BORDER     = "#38383A"


Colors = LightColors


class Fonts:
    FAMILY      = "-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'SF Pro Display', 'Segoe UI', sans-serif"
    FAMILY_MONO = "'SF Mono', 'Menlo', 'Consolas', monospace"

    SIZE_XS   = "11px"
    SIZE_SM   = "12px"
    SIZE_BASE = "13px"
    SIZE_MD   = "14px"
    SIZE_LG   = "16px"
    SIZE_XL   = "20px"
    SIZE_2XL  = "28px"

    WEIGHT_NORMAL   = "400"
    WEIGHT_MEDIUM   = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD     = "700"


class Spacing:
    PX2  = 2;  PX4  = 4;  PX6  = 6;  PX8  = 8
    PX12 = 12; PX16 = 16; PX20 = 20; PX24 = 24
    PX32 = 32; PX40 = 40; PX48 = 48

    SIDEBAR_W_FULL      = 220
    SIDEBAR_W_COLLAPSED = 56
    HEADER_H            = 48
    NAV_ITEM_H          = 36
    INPUT_H             = 34
    BTN_RADIUS          = 8
    CARD_RADIUS         = 10
    MODAL_RADIUS        = 12
    INPUT_RADIUS        = 8

    # Legacy
    XS  = 4; SM  = 8; MD  = 12; LG  = 16; XL  = 24; XXL = 32


class ThemeManager(QObject):
    """Singleton for light/dark mode switching."""
    theme_changed = Signal(str)
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = "light"
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._initialized = True

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def is_dark(self) -> bool:
        return self._mode == "dark"

    def colors(self):
        return DarkColors if self._mode == "dark" else LightColors

    def set_mode(self, mode: str):
        if mode not in ("light", "dark"):
            return
        if self._mode != mode:
            self._mode = mode
            global Colors
            Colors = DarkColors if mode == "dark" else LightColors
            self.theme_changed.emit(mode)

    def toggle(self):
        self.set_mode("dark" if self._mode == "light" else "light")
