#!/usr/bin/env python3
"""
FinAuditPro - Master Production & Development Seeder
TempAudit Audit Platform

Populates the SQLite database with all 3 standard test fintech entities:
  1. Aryan Fintech Pvt. Ltd. (ARYAN)
  2. Hitansh Fintech Pvt. Ltd. (HITANSH)
  3. Jeet Fintech Pvt. Ltd. (JEET)

Includes:
  - Clean client master records & statutory IDs (PAN, GSTIN, CIN)
  - Prior Year (FY 2024-25) & Current Year (FY 2025-26) Engagements
  - Standardized user accounts (Admin, Auditors, Staff)
  - Full General Ledger transactions with real statutory anomalies
  - Bank Statements, Sales & Purchase Registers, GSTR-2B portal downloads
  - Pre-computed Ledgers for Trial Balance
  - Working Papers, Audit Checklists, and Audit Findings
  - Firm Profile & Completed Setup Wizard Settings

Usage:
    python scripts/seed_test_data.py
    or:
    python scripts/seed_test_data.py --reset
"""

import sys
import os
import argparse

# Add repository root to sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from test_data.seed import seed_test_database
from backend.app.database import get_db_path, init_db

def main():
    parser = argparse.ArgumentParser(description="FinAuditPro Master Test Data Seeder")
    parser.add_argument("--reset", action="store_true", help="Recreate pristine database schema before seeding")
    args = parser.parse_args()

    print("=" * 80)
    print("FINAUDITPRO - MASTER TEST DATA SEEDER")
    print(f"Target Database: {get_db_path()}")
    print("=" * 80)

    if args.reset:
        print("[*] Reinitializing clean database schema...")
        db_path = get_db_path()
        if os.path.exists(db_path):
            os.remove(db_path)
        for ext in ["-wal", "-shm"]:
            if os.path.exists(db_path + ext):
                os.remove(db_path + ext)
        init_db()

    print("[*] Seeding all 3 corporate entities from test_data/...")
    res = seed_test_database()

    print("\n[✓] Successfully seeded all entities:")
    for key, data in res.items():
        print(f"  • {data['company']} ({key.upper()}):")
        print(f"      Client ID: {data['client_id']}")
        print(f"      CY Engagement #{data['cy_engagement_id']} (FY 2025-26 - In Progress)")
        print(f"      PY Engagement #{data['py_engagement_id']} (FY 2024-25 - Completed)")

    print("\n[✓] Active User Accounts Provisioned:")
    print("  • Lead Partner / Admin: admin / admin123")
    print("  • Aryan Lead Auditor:   auditor_aryan / audit123 (Staff: staff_aryan / staff123)")
    print("  • Hitansh Lead Auditor: auditor_hitansh / audit123 (Staff: staff_hitansh / staff123)")
    print("  • Jeet Lead Auditor:    auditor_jeet / audit123 (Staff: staff_jeet / staff123)")
    print("=" * 80)

if __name__ == "__main__":
    main()
