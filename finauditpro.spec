# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller Specification for FinAuditPro — Enterprise Desktop Release.

Supports:
- macOS Apple Silicon (arm64) and Intel (x86_64 / Universal) Application Bundle (.app)
- Windows x64 Standalone Executable (.exe)
"""

import os
import platform
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

PROJECT_ROOT = Path(os.path.abspath(SPECPATH))
SRC_DIR = PROJECT_ROOT / "src"

is_darwin = sys.platform == "darwin"
is_windows = sys.platform == "win32"
is_arm64 = platform.machine() in ("arm64", "aarch64")

block_cipher = None

# Collect all finauditpro application submodules
hiddenimports = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtPrintSupport",
    "sqlalchemy",
    "sqlalchemy.dialects.sqlite",
    "sqlalchemy.orm",
    "pydantic",
    "pydantic_core",
    "cryptography",
    "cryptography.fernet",
    "cryptography.hazmat.primitives",
    "cryptography.hazmat.primitives.kdf.pbkdf2",
    "reportlab",
    "reportlab.platypus",
    "reportlab.lib",
    "reportlab.pdfgen",
    "openpyxl",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "httpx",
]
hiddenimports += collect_submodules("finauditpro")

datas = []
# Include application icons and resources
icons_dir = SRC_DIR / "finauditpro" / "assets" / "icons"
if icons_dir.exists():
    datas.append((str(icons_dir), "finauditpro/assets/icons"))

a = Analysis(
    [str(SRC_DIR / "finauditpro" / "__main__.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "pytest",
        "_pytest",
        "IPython",
        "jupyter",
        "notebook",
        "sphinx",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Target icon determination
if is_darwin:
    app_icon = str(icons_dir / "FinAuditPro.icns") if (icons_dir / "FinAuditPro.icns").exists() else None
elif is_windows:
    app_icon = str(icons_dir / "FinAuditPro.ico") if (icons_dir / "FinAuditPro.ico").exists() else None
else:
    app_icon = str(icons_dir / "finauditpro_icon.png") if (icons_dir / "finauditpro_icon.png").exists() else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FinAuditPro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64" if (is_darwin and is_arm64) else None,
    codesign_identity=os.environ.get("APPLE_SIGNING_IDENTITY"),
    entitlements_file=None,
    icon=app_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FinAuditPro",
)

if is_darwin:
    app = BUNDLE(
        coll,
        name="FinAuditPro.app",
        icon=app_icon,
        bundle_identifier="com.finauditpro.desktop",
        info_plist={
            "CFBundleName": "FinAuditPro",
            "CFBundleDisplayName": "FinAuditPro",
            "CFBundleExecutable": "FinAuditPro",
            "CFBundleIdentifier": "com.finauditpro.desktop",
            "CFBundleVersion": "1.0.0",
            "CFBundleShortVersionString": "1.0.0",

            "NSHighResolutionCapable": "True",
            "LSMinimumSystemVersion": "12.0",
            "NSHumanReadableCopyright": "Copyright © 2026 FinAuditPro. All rights reserved.",
            "NSPrincipalClass": "NSApplication",
            "LSApplicationCategoryType": "public.app-category.finance",
        },
    )
