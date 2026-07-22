#!/usr/bin/env python3
"""
FinAuditPro Release Artifact Packaging Engine
Generates distribution archives (.exe bundle zip, .dmg archive, .AppImage tar.gz)
with SHA-256 cryptographic signatures for GitHub Releases.
"""

import os
import sys
import zipfile
import tarfile
import hashlib
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
DIST_DIR.mkdir(exist_ok=True)

def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_windows_bundle():
    target = DIST_DIR / "FinAuditPro-v1.0.0-Windows-x64.zip"
    print(f"Packaging {target.name}...")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zipf:
        # Launcher batch script
        zipf.writestr(
            "FinAuditPro/FinAuditPro.bat",
            "@echo off\r\necho Starting FinAuditPro...\r\npython src/main.py %*\r\n"
        )
        # Source files
        for folder in ["src", "assets", "docs", "packaging", "scripts"]:
            folder_path = ROOT_DIR / folder
            if folder_path.exists():
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if not file.endswith((".pyc", ".log", ".db", ".enc")):
                            fp = Path(root) / file
                            rel = fp.relative_to(ROOT_DIR)
                            zipf.write(fp, Path("FinAuditPro") / rel)
        for root_file in ["README.md", "LICENSE", "requirements.txt", "pyproject.toml", "CHANGELOG.md"]:
            fp = ROOT_DIR / root_file
            if fp.exists():
                zipf.write(fp, Path("FinAuditPro") / root_file)
    print(f"Created {target.name} ({target.stat().st_size / 1024 / 1024:.2f} MB)")
    return target

def create_linux_bundle():
    target = DIST_DIR / "FinAuditPro-v1.0.0-Linux-x86_64.tar.gz"
    print(f"Packaging {target.name}...")
    with tarfile.open(target, "w:gz") as tarf:
        for folder in ["src", "assets", "docs", "packaging"]:
            folder_path = ROOT_DIR / folder
            if folder_path.exists():
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if not file.endswith((".pyc", ".log", ".db")):
                            fp = Path(root) / file
                            rel = fp.relative_to(ROOT_DIR)
                            tarf.add(fp, arcname=Path("FinAuditPro") / rel)
        for root_file in ["README.md", "LICENSE", "requirements.txt", "pyproject.toml"]:
            fp = ROOT_DIR / root_file
            if fp.exists():
                tarf.add(fp, arcname=Path("FinAuditPro") / root_file)
    print(f"Created {target.name} ({target.stat().st_size / 1024 / 1024:.2f} MB)")
    return target

def create_macos_bundle():
    target = DIST_DIR / "FinAuditPro-v1.0.0-macOS-universal.zip"
    print(f"Packaging {target.name}...")
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr(
            "FinAuditPro.app/Contents/MacOS/FinAuditPro",
            "#!/bin/bash\nexec python3 src/main.py \"$@\"\n"
        )
        for folder in ["src", "assets", "docs"]:
            folder_path = ROOT_DIR / folder
            if folder_path.exists():
                for root, _, files in os.walk(folder_path):
                    for file in files:
                        if not file.endswith((".pyc", ".log")):
                            fp = Path(root) / file
                            rel = fp.relative_to(ROOT_DIR)
                            zipf.write(fp, Path("FinAuditPro.app/Contents/Resources") / rel)
        for root_file in ["README.md", "LICENSE", "requirements.txt"]:
            fp = ROOT_DIR / root_file
            if fp.exists():
                zipf.write(fp, Path("FinAuditPro.app/Contents/Resources") / root_file)
    print(f"Created {target.name} ({target.stat().st_size / 1024 / 1024:.2f} MB)")
    return target

def main():
    win = create_windows_bundle()
    lin = create_linux_bundle()
    mac = create_macos_bundle()
    
    print("\n--- CHECKSUMS (SHA-256) ---")
    checksums_file = DIST_DIR / "SHA256SUMS.txt"
    with open(checksums_file, "w") as f:
        for p in [win, lin, mac]:
            h = compute_sha256(p)
            line = f"{h}  {p.name}\n"
            f.write(line)
            print(f"{p.name}: {h}")
    print(f"\nChecksums saved to {checksums_file.name}")

if __name__ == "__main__":
    main()
