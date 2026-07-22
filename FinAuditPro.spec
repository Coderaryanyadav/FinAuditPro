# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('HTML', 'HTML'),
        ('src/data', 'data'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtCharts',
        'sqlalchemy',
        'sqlalchemy.ext.declarative',
        'ollama',
        'requests',
        'pypdf',
        'pdfplumber',
        'matplotlib',
        'cryptography',
        'pydantic',
        'faiss',
        'sentence_transformers',
        'torch',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

import platform
import os

os_name = platform.system()
icon_path = 'assets/icon.ico' if os_name == 'Windows' else 'assets/icon.icns' if os_name == 'Darwin' else 'assets/icon.png'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FinAuditPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Disable console for production desktop app
    disable_windowed_traceback=False,
    argv_emulation=True if os_name == 'Darwin' else False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
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
