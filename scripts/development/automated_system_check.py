#!/usr/bin/env python3
"""FinAuditPro Automated System Verification & AI Diagnostic Tool.

Probes system prerequisites, database schema migrations, UI view instantiations,
Fernet encryption, and local LM Studio REST endpoint availability.
"""

import shutil
import sys
from pathlib import Path

# Ensure src/ is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

def run_system_check() -> int:
    print("=" * 65)
    print(" FINAUDITPRO — AUTOMATED SYSTEM DIAGNOSTIC & AI VERIFICATION")
    print("=" * 65)

    failures = 0

    # 1. Environment & Runtime
    print("\n[1/6] Probing Python Runtime & Dependencies...")
    py_ver = sys.version.split()[0]
    print(f"  • Python Executable: {sys.executable}")
    print(f"  • Python Version: {py_ver}")

    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        print(f"  • Tesseract OCR Executable: PASS ({tesseract_path})")
    else:
        print("  • Tesseract OCR Executable: WARNING (Not found in PATH; OCR using PyMuPDF text mode)")

    # 2. Infrastructure & Data Directories
    print("\n[2/6] Probing App Data Directories & Database Migrations...")
    try:
        from finauditpro.infrastructure.first_run import (
            bootstrap_app_data_dirs,
            initialize_database,
        )
        db_dir, docs_dir, vector_dir, _ = bootstrap_app_data_dirs()
        db_manager = initialize_database()
        print(f"  • App Data Directory: PASS ({db_dir.parent})")
        print(f"  • SQLite Database Path: PASS ({db_manager.db_path})")
    except Exception as e:
        print(f"  • Infrastructure Bootstrap: FAIL ({e})")
        failures += 1
        db_manager = None

    # 3. Database Schema & Tables
    print("\n[3/6] Probing Database Schema Integrity (Migrations 1..9)...")
    if db_manager:
        try:
            from sqlalchemy import inspect
            inspector = inspect(db_manager.engine)
            tables = inspector.get_table_names()
            expected_tables = [
                "firms", "clients", "engagements", "audit_events",
                "documents", "trial_balance_lines", "findings", "working_papers"
            ]
            missing = [t for t in expected_tables if t not in tables]
            if not missing:
                print(f"  • Database Table Schema: PASS ({len(tables)} tables verified)")
            else:
                print(f"  • Database Table Schema: FAIL (Missing tables: {missing})")
                failures += 1
        except Exception as e:
            print(f"  • Database Inspection: FAIL ({e})")
            failures += 1

    # 4. Fernet Security & Column Encryption
    print("\n[4/6] Probing Fernet AES-128-CBC Encryption...")
    try:
        from finauditpro.infrastructure.security.encryption import (
            decrypt_sensitive_string,
            encrypt_sensitive_string,
        )
        test_str = "FinAuditPro-Diagnostic-Secret"
        enc = encrypt_sensitive_string(test_str)
        dec = decrypt_sensitive_string(enc)
        if dec == test_str:
            print("  • Fernet Encryption Engine: PASS")
        else:
            print("  • Fernet Encryption Engine: FAIL (Decrypted mismatch)")
            failures += 1
    except Exception as e:
        print(f"  • Fernet Encryption Engine: FAIL ({e})")
        failures += 1

    # 5. Local AI & LM Studio REST Endpoint Supervisor
    print("\n[5/6] Probing Local LM Studio Server Supervisor...")
    try:
        from finauditpro.infrastructure.ai.lmstudio_supervisor import LMStudioSupervisor
        ai_res = LMStudioSupervisor.ensure_ai_server_ready(auto_start=True)
        if ai_res["is_online"]:
            print(f"  • LM Studio HTTP Endpoint: PASS ({ai_res['url']}, Status: {ai_res['action_taken']})")
            if ai_res["models_loaded"]:
                print(f"    - Loaded Models: {', '.join(ai_res['models_loaded'][:3])}")
        else:
            print(f"  • LM Studio HTTP Endpoint: AIR-GAPPED FALLBACK (Offline on {ai_res['url']})")
            print("    [Info: FinAuditPro core audit engine operates fully air-gapped without cloud or AI server dependencies]")
    except Exception as e:
        print(f"  • LM Studio Server Supervisor: WARNING ({e})")

    # 6. UI Layer & Component Instantiation
    print("\n[6/6] Probing UI Layer Component Instantiation...")
    try:
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        from finauditpro.ui.theme import MetricCard, StatusBadge
        b = StatusBadge("Test Status", "success")
        m = MetricCard("Total Assets", "₹1,00,00,000")
        print("  • PySide6 UI Tokens & Base Widgets: PASS")
    except Exception as e:
        print(f"  • PySide6 UI Components: FAIL ({e})")
        failures += 1

    print("\n" + "=" * 65)
    if failures == 0:
        print(" SYSTEM DIAGNOSTIC STATUS: ALL MANDATORY CHECKS PASSED (100%)")
        print(" FINAUDITPRO IS READY FOR ZERO-FRICTION EXECUTION.")
    else:
        print(f" SYSTEM DIAGNOSTIC STATUS: {failures} FAILURES DETECTED.")
    print("=" * 65 + "\n")

    return failures

if __name__ == "__main__":
    sys.exit(run_system_check())
