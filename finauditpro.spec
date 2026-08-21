# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller Specification for FinAuditPro — macOS Apple Silicon (arm64).

Notice: PyInstaller build tooling is authored and maintained for Apple Silicon.
PyInstaller execution in this sandbox is BLOCKED due to no PyPI network access to install PyInstaller.
When building on an internet-connected build host:
  1. pip install -e .[ocr,ai] pyinstaller
  2. pyinstaller finauditpro.spec
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

datas = []
hiddenimports = [
    'PySide6',
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    'pydantic',
    'cryptography',
    'reportlab',
    'matplotlib',
]

a = Analysis(
    ['src/finauditpro/__main__.py'],
    pathex=['src'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='finauditpro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FinAuditPro',
)

app = BUNDLE(
    coll,
    name='FinAuditPro.app',
    icon=None,
    bundle_identifier='com.finauditpro.desktop',
    info_plist={
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '12.0',
        'CFBundleShortVersionString': '0.1.0',
    },
)
