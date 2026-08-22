#!/usr/bin/env python3
"""Batch verification utility for engagement sealed archives and SHA-256 manifests."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

# Ensure src/ is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from finauditpro.infrastructure.first_run import get_app_data_dir


def verify_archive(zip_path: Path) -> bool:
    print(f"\nVerifying archive: {zip_path.name}")
    if not zipfile.is_zipfile(zip_path):
        print("  ✗ File is not a valid ZIP archive.")
        return False

    with zipfile.ZipFile(zip_path, "r") as zf:
        namelist = zf.namelist()
        if "manifest.json" not in namelist:
            print("  ✗ manifest.json missing from archive.")
            return False

        manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
        files_manifest = manifest_data.get("files", {})

        all_ok = True
        for member_name, expected_hash in files_manifest.items():
            if member_name not in namelist:
                print(f"  ✗ Missing member file: {member_name}")
                all_ok = False
                continue

            content = zf.read(member_name)
            computed_hash = hashlib.sha256(content).hexdigest()
            if computed_hash != expected_hash:
                print(f"  ✗ Checksum mismatch on {member_name}: expected {expected_hash}, got {computed_hash}")
                all_ok = False
            else:
                print(f"  ✓ {member_name} (SHA-256: {computed_hash[:16]}...)")

        if all_ok:
            print("  ✓ Archive manifest seal verification PASS.")
        return all_ok


def main() -> None:
    app_data = get_app_data_dir()
    archives_dir = app_data / "archives"

    if not archives_dir.exists():
        print(f"No archives directory found at: {archives_dir}")
        return

    archives = list(archives_dir.glob("*.zip"))
    if not archives:
        print(f"No sealed archives found in: {archives_dir}")
        return

    print(f"Scanning {len(archives)} sealed engagement archive(s)...")
    passed = 0
    for arch in archives:
        if verify_archive(arch):
            passed += 1

    print(f"\nArchive Integrity Verification Summary: {passed}/{len(archives)} PASS")


if __name__ == "__main__":
    main()
