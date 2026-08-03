"""
Design System Tokens & Theme Definitions for FinAuditPro.
Provides centralized Color Palettes, Typography scale, Spacing tokens, and Theme configurations.
"""

class Colors:
    # Primary Trust Palette (Sky / Corporate Blue)
    PRIMARY = "#0284c7"       # Sky Blue 600
    PRIMARY_DARK = "#0369a1"  # Sky Blue 700
    PRIMARY_HOVER = "#0369a1" # Sky Blue 700
    PRIMARY_LIGHT = "#e0f2fe" # Sky Blue 100
    PRIMARY_BG_SUBTLE = "#eff6ff" # Soft Trust Blue Tint

    # Status / Functional Colors
    SUCCESS = "#16a34a"       # Green 600
    SUCCESS_BG = "#dcfce7"    # Green 100
    WARNING = "#d97706"       # Amber 600
    WARNING_BG = "#fef3c7"    # Amber 100
    DANGER = "#dc2626"        # Red 600
    DANGER_DARK = "#991b1b"   # Red 800
    DANGER_BG = "#fee2e2"     # Red 100
    INFO = "#0284c7"          # Sky 600
    INFO_BG = "#e0f2fe"       # Sky 100

    # Neutral / Crisp Light Slate Scale
    BG_MAIN = "#f8fafc"       # Slate 50
    SURFACE_WHITE = "#ffffff"
    SURFACE_CARD = "#ffffff"
    BORDER_LIGHT = "#f1f5f9"  # Slate 100
    BORDER_DEFAULT = "#e2e8f0"# Slate 200
    BORDER_INPUT = "#cbd5e1"  # Slate 300
    
    TEXT_MAIN = "#0f172a"     # Slate 900 (High contrast text)
    TEXT_MUTED = "#475569"    # Slate 600 (Secondary text)
    TEXT_SUBTLE = "#64748b"   # Slate 500 (Captions / Labels)
    TEXT_PLACEHOLDER = "#94a3b8" # Slate 400

    # Navigation Sidebar Colors
    NAV_BG = "#ffffff"
    NAV_BORDER = "#e2e8f0"    # Slate 200
    NAV_ITEM_HOVER = "#f8fafc"
    NAV_ITEM_ACTIVE = "#e0f2fe"
    NAV_TEXT_ACTIVE = "#0284c7"


class Fonts:
    FAMILY = "'Segoe UI', -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif"
    
    # Font Sizes
    SIZE_XS = "10px"
    SIZE_SM = "12px"
    SIZE_BASE = "13px"
    SIZE_MD = "14px"
    SIZE_LG = "16px"
    SIZE_XL = "18px"
    SIZE_2XL = "24px"

    # Font Weights
    WEIGHT_NORMAL = "400"
    WEIGHT_MEDIUM = "500"
    WEIGHT_SEMIBOLD = "600"
    WEIGHT_BOLD = "700"
    WEIGHT_EXTRABOLD = "800"


class Spacing:
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 24
    XXL = 32
