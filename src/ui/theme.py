"""
Design System Tokens & Theme Definitions for FinAuditPro.
Provides centralized Color Palettes, Typography scale, Spacing tokens, and Theme configurations.
"""

class Colors:
    # Primary Palette
    PRIMARY = "#0ea5e9"       # Sky Blue 500
    PRIMARY_DARK = "#0284c7"  # Sky Blue 600
    PRIMARY_HOVER = "#0369a1" # Sky Blue 700
    PRIMARY_LIGHT = "#e0f2fe" # Sky Blue 100

    # Status / Functional Colors
    SUCCESS = "#10b981"       # Emerald 500
    SUCCESS_BG = "#dcfce7"    # Emerald 100
    WARNING = "#f59e0b"       # Amber 500
    WARNING_BG = "#fef3c7"    # Amber 100
    DANGER = "#ef4444"        # Red 500
    DANGER_DARK = "#dc2626"   # Red 600
    DANGER_BG = "#fee2e2"     # Red 100

    # Neutral / Slate Scale
    BG_MAIN = "#f8fafc"       # Slate 50
    SURFACE_WHITE = "#ffffff"
    BORDER_LIGHT = "#e2e8f0"  # Slate 200
    BORDER_DEFAULT = "#cbd5e1"# Slate 300
    
    TEXT_MAIN = "#0f172a"     # Slate 900
    TEXT_MUTED = "#64748b"    # Slate 500
    TEXT_SUBTLE = "#94a3b8"   # Slate 400

    # Dark Navigation Sidebar Colors
    NAV_BG = "#0b0f19"
    NAV_BORDER = "#1e293b"    # Slate 800
    NAV_ITEM_HOVER = "#1e293b"
    NAV_ITEM_ACTIVE = "#0ea5e9"


class Fonts:
    FAMILY = "'Inter', system-ui, -apple-system, sans-serif"
    
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
