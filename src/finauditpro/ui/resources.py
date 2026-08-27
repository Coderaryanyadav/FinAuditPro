"""Application icon and asset resource loading via importlib.resources."""

from importlib import resources
from pathlib import Path

from PySide6.QtGui import QIcon


def get_asset_path(subpath: str) -> Path:
    """Resolve relative path within finauditpro.assets package."""
    parts = subpath.strip("/\\").replace("\\", "/").split("/")
    traversable = resources.files("finauditpro.assets")
    for part in parts:
        traversable = traversable.joinpath(part)
    return Path(str(traversable))


def get_app_icon() -> QIcon:
    """Return QIcon for application window and dock."""
    for filename in ("FinAuditPro.icns", "FinAuditPro.ico", "finauditpro_icon.png", "icons/FinAuditPro.icns", "icons/FinAuditPro.ico", "icons/finauditpro_icon.png"):
        p = get_asset_path(filename)
        if p.exists():
            return QIcon(str(p))
    return QIcon()
