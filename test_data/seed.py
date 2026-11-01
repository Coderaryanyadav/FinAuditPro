"""
Test Database Seeder
FinAuditPro - Test Data Architecture

*** TEST FIXTURES ONLY — NEVER USE THESE SEEDED CREDENTIALS IN PRODUCTION ENVIRONMENTS ***
"""

import os
import csv
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from backend.app.database import get_db_connection, init_db
from backend.app.auth import hash_password
from test_data.companies import ARYAN_COMPANY, HITANSH_COMPANY, JEET_COMPANY
from test_data.transactions import get_transactions_for_company, get_prior_year_transactions_for_company
from test_data.findings import get_test_findings_for_company
from test_data.working_papers import get_test_working_papers_for_company
from test_data.checklists import get_test_checklist_items
from backend.app.parsers.excel_csv import import_and_save_transactions, auto_detect_mapping
import pandas as pd

# Configurable passwords for test automation suites (TEST ONLY)
TEST_ADMIN_PASSWORD = os.environ.get("TEST_ADMIN_PASSWORD", "admin123")
TEST_AUDITOR_PASSWORD = os.environ.get("TEST_AUDITOR_PASSWORD", "audit123")
TEST_STAFF_PASSWORD = os.environ.get("TEST_STAFF_PASSWORD", "staff123")


def clean_currency(val) -> float:
    """Accurately normalizes monetary amounts to 2 decimal places using Decimal."""
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        d = Decimal(str(val))
    else:
        s = str(val).replace(",", "").replace("₹", "").replace("$", "").strip()
        try:
            d = Decimal(s)
        except Exception:
            return 0.0
    return float(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def seed_test_users(conn):
    """Explicitly seeds isolated test users for testing/development (NEVER FOR PRODUCTION)."""
    cursor = conn.cursor()
    now_str = datetime.now().isoformat()
    
    admin_hash = hash_password(TEST_ADMIN_PASSWORD)
    audit_hash = hash_password(TEST_AUDITOR_PASSWORD)
    staff_hash = hash_password(TEST_STAFF_PASSWORD)

    test_users = [
        (1, "admin", "admin@finauditpro.local", "System Administrator (FCA)", "Admin", admin_hash),
        (2, "auditor_aryan", "lead.aryan@finauditpro.in", "Auditor A (Aryan Lead Manager)", "Auditor", audit_hash),
        (3, "staff_aryan", "staff.aryan@finauditpro.in", "Staff A (Aryan Engagement Staff)", "Audit Staff", staff_hash),
        (4, "auditor_hitansh", "lead.hitansh@finauditpro.in", "Auditor B (Hitansh Lead Manager)", "Auditor", audit_hash),
        (5, "staff_hitansh", "staff.hitansh@finauditpro.in", "Staff B (Hitansh Engagement Staff)", "Audit Staff", staff_hash),
        (6, "auditor_jeet", "lead.jeet@finauditpro.in", "Auditor C (Jeet Lead Manager)", "Auditor", audit_hash),
        (7, "staff_jeet", "staff.jeet@finauditpro.in", "Staff C (Jeet Engagement Staff)", "Audit Staff", staff_hash),
        (8, "auditor", "senior@finauditpro.in", "Rohan Mehta (General Auditor)", "Auditor", audit_hash),
        (9, "staff", "assistant@finauditpro.in", "Pooja Verma (General Staff)", "Audit Staff", staff_hash),
    ]

    for uid, uname, uemail, ufullname, urole, uhash in test_users:
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, username, email, full_name, role, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (uid, uname, uemail, ufullname, urole, uhash, now_str))

def seed_company_engagement(conn, company: dict) -> dict:
    now_str = datetime.now().isoformat()
    cursor = conn.cursor()

    short_code = company.get("short_code")
    if short_code == "ARYAN":
        lead_auditor_id, assigned_staff_id = 2, 3
    elif short_code == "HITANSH":
        lead_auditor_id, assigned_staff_id = 4, 5
    else:
        lead_auditor_id, assigned_staff_id = 6, 7

    # 1. Insert Client with synthetic flag notes
    client_notes = f"[SYNTHETIC TEST DATASET - NOT REAL CLIENT DATA] {company.get('nature_of_business', '')}"
    cursor.execute("""
        INSERT INTO clients (name, pan, gstin, entity_type, contact_person, email, phone, address, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        company["name"], company["pan"], company["gstin"], company["company_type"],
        company["primary_contact"], company["email"], company["phone"], company["address"],
        client_notes, now_str, now_str
    ))
    client_id = cursor.lastrowid

    # 2. Insert Prior Year Engagement (FY 2024-25)
    cursor.execute("""
        INSERT INTO engagements (client_id, title, audit_type, financial_year, period_start, period_end, status, lead_auditor_id, assigned_staff_id, materiality_threshold, notes, created_at, updated_at)
        VALUES (?, ?, 'Statutory Audit', ?, ?, ?, 'Completed', ?, ?, 50000.0, ?, ?, ?)
    """, (
        client_id, f"Statutory Audit {company['prior_financial_year']}", company["prior_financial_year"],
        f"2024-04-01", f"2025-03-31", lead_auditor_id, assigned_staff_id,
        f"[TEST FIXTURE] Prior year audit records for {company['name']}", now_str, now_str
    ))
    py_eng_id = cursor.lastrowid

    # 3. Insert Current Year Engagement (FY 2025-26)
    cursor.execute("""
        INSERT INTO engagements (client_id, title, audit_type, financial_year, period_start, period_end, status, lead_auditor_id, assigned_staff_id, materiality_threshold, notes, created_at, updated_at)
        VALUES (?, ?, 'Statutory Audit', ?, ?, ?, 'In Progress', ?, ?, 50000.0, ?, ?, ?)
    """, (
        client_id, f"Statutory & Tax Audit {company['financial_year']}", company["financial_year"],
        f"2025-04-01", f"2026-03-31", lead_auditor_id, assigned_staff_id,
        f"[TEST FIXTURE] Current year active audit for {company['name']}", now_str, now_str
    ))
    cy_eng_id = cursor.lastrowid

    # 4. Insert PY Transactions
    py_txs = get_prior_year_transactions_for_company(company["short_code"])
    for t in py_txs:
        cursor.execute("""
            INSERT INTO transactions (
                engagement_id, date, voucher_no, invoice_no, ledger, account_group,
                description, debit, credit, amount, party_name, gstin,
                tax_amount, reference_no
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            py_eng_id, t["date"], t["voucher_no"], t["invoice_no"], t["ledger"], t["account_group"],
            t["description"], clean_currency(t["debit"]), clean_currency(t["credit"]), clean_currency(t["amount"]),
            t["party_name"], t["party_gstin"], clean_currency(t["tax_amount"]), t["reference"]
        ))

    # 5. Insert CY Transactions
    cy_txs = get_transactions_for_company(company["short_code"])
    for t in cy_txs:
        cursor.execute("""
            INSERT INTO transactions (
                engagement_id, date, voucher_no, invoice_no, ledger, account_group,
                description, debit, credit, amount, party_name, gstin,
                tax_amount, reference_no
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cy_eng_id, t["date"], t["voucher_no"], t["invoice_no"], t["ledger"], t["account_group"],
            t["description"], clean_currency(t["debit"]), clean_currency(t["credit"]), clean_currency(t["amount"]),
            t["party_name"], t["party_gstin"], clean_currency(t["tax_amount"]), t["reference"]
        ))

    # 6. Insert Checklists (for both PY and CY)
    for target_eng_id in [py_eng_id, cy_eng_id]:
        checklists = get_test_checklist_items(target_eng_id)
        for c in checklists:
            cursor.execute("""
                INSERT INTO audit_checklists (engagement_id, category, item_code, question, guidance, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (target_eng_id, c["category"], c["item_code"], c["question"], c["guidance"], c["status"], now_str))

    # 7. Insert Findings
    findings = get_test_findings_for_company(company["short_code"], cy_eng_id)
    for idx, f in enumerate(findings, 1):
        cursor.execute("""
            INSERT INTO audit_findings (
                engagement_id, finding_code, module, category, severity,
                risk_score, title, description, rule_used, engine_type,
                recommended_action, status, created_at
            )
            VALUES (?, ?, ?, 'Statutory Compliance', ?, 85.0, ?, ?, ?, 'DETERMINISTIC', ?, ?, ?)
        """, (
            cy_eng_id, f"FND-{company['short_code']}-{idx:03d}", "Compliance", f["severity"],
            f["title"], f["description"], f["rule_id"],
            f["recommendation"], f["status"], now_str
        ))

    # 8. Insert Working Papers
    wps = get_test_working_papers_for_company(company["short_code"], cy_eng_id)
    for wp in wps:
        cursor.execute("""
            INSERT INTO working_papers (
                engagement_id, wp_reference, title, area, category,
                description, status, prepared_by, prepared_date, notes, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'Substantive Testing', ?, ?, ?, ?, ?, ?, ?)
        """, (
            cy_eng_id, wp["wp_reference"], wp["title"], wp["module"],
            wp["objective"], wp["status"], wp["prepared_by"], now_str[:10], wp["notes"], now_str, now_str
        ))

    # 9. Register Uploaded Files & Ingest Live File Transactions
    for cat, fname in [
        ("General Ledger", "transactions.csv"),
        ("Sales Register", "sales_register.csv"),
        ("Purchase Register", "purchase_register.csv"),
        ("Bank Statement", "bank_statement.csv"),
        ("GST Data", "gst_portal.csv")
    ]:
        rel_path = f"test_data/{company['short_code'].lower()}_fintech/{fname}"
        abs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), rel_path)
        actual_row_count = 200
        if os.path.exists(abs_path):
            try:
                df_temp = pd.read_csv(abs_path)
                actual_row_count = len(df_temp)
            except Exception:
                pass

        cursor.execute("""
            INSERT INTO uploaded_files (engagement_id, file_name, file_type, file_path, source_type, data_category, row_count, successful_rows, uploaded_by, uploaded_at)
            VALUES (?, ?, 'CSV', ?, 'TEST_FIXTURE', ?, ?, ?, 'SYSTEM_TEST_SEED', ?)
        """, (
            cy_eng_id, f"{company['short_code'].lower()}_{fname}", rel_path, cat, actual_row_count, actual_row_count, now_str
        ))
        file_id = cursor.lastrowid

        # Ingest transactions directly through parser so data is 100% linked live
        if os.path.exists(abs_path):
            try:
                df = pd.read_csv(abs_path)
                mapping = auto_detect_mapping(df.columns.tolist())
                # For non-GL files (Sales, Purchase, Bank, GST), import transactions linked to file_id
                # For GL transactions.csv, link the existing 1097 transactions to file_id and add original_row_json
                if fname == "transactions.csv":
                    cursor.execute("""
                        UPDATE transactions SET file_id = ? WHERE engagement_id = ? AND file_id IS NULL
                    """, (file_id, cy_eng_id))
                    # Also populate original_row_json for GL transactions
                    for idx, row in df.iterrows():
                        row_dict = row.dropna().to_dict()
                        v_no = str(row_dict.get("voucher_no") or "")
                        d_val = str(row_dict.get("date") or "")
                        import json
                        cursor.execute("""
                            UPDATE transactions SET original_row_json = ? 
                            WHERE engagement_id = ? AND file_id = ? AND voucher_no = ? AND date = ?
                        """, (json.dumps(row_dict, default=str), cy_eng_id, file_id, v_no, d_val))
                else:
                    import_and_save_transactions(
                        engagement_id=cy_eng_id,
                        file_id=file_id,
                        file_path=abs_path,
                        file_type="CSV",
                        mapping=mapping,
                        data_category=cat
                    )
            except Exception as ex:
                print(f"[!] Warning: Live ingest failed for {fname}: {ex}")

    return {
        "client_id": client_id,
        "cy_engagement_id": cy_eng_id,
        "py_engagement_id": py_eng_id,
        "company": company["name"],
        "lead_auditor_id": lead_auditor_id,
        "assigned_staff_id": assigned_staff_id
    }

def seed_test_database():
    """Seeds the SQLite database with both Aryan Fintech and Hitansh Fintech datasets, firm settings, and test users."""
    env = os.environ.get("FINAUDIT_ENV", os.environ.get("ENVIRONMENT", "development")).lower()
    if env == "production":
        raise RuntimeError(
            "FATAL: test_data/seed.py cannot be executed in a production environment. "
            "Seeding default test credentials into a live database is strictly prohibited."
        )

    init_db()
    conn = get_db_connection()
    now_str = datetime.now().isoformat()

    # Clean slate for idempotent test seeding (prevents duplicate clients / engagements)
    tables_to_clear = [
        "reconciliation_items", "reconciliations", "uploaded_files",
        "audit_findings", "working_papers", "audit_checklists",
        "transactions", "ledgers", "duplicate_group_reviews",
        "missing_sequence_reviews", "anomaly_reviews", "yoy_comparison_reviews",
        "evidence_items", "engagements", "clients"
    ]
    for tbl in tables_to_clear:
        try:
            conn.execute(f"DELETE FROM {tbl}")
        except Exception:
            pass
    try:
        placeholders = ",".join(f"'{tbl}'" for tbl in tables_to_clear)
        conn.execute(f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})")
    except Exception:
        pass
    conn.commit()

    # Seed app_settings so that the setup wizard does not trap demo users
    default_settings = [
        ("is_initial_setup_completed", "1"),
        ("firm_name", "Alpha & Associates Chartered Accountants"),
        ("firm_registration_no", "FRN-109283W"),
        ("firm_email", "admin@finauditpro.local"),
        ("firm_phone", "+91 98765 43210"),
        ("firm_address", "Suite 401, Nariman Point, Mumbai - 400021"),
        ("system_currency", "INR"),
        ("default_financial_year", "2025-26")
    ]
    for key, val in default_settings:
        conn.execute("""
            INSERT OR REPLACE INTO app_settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, val, now_str))

    seed_test_users(conn)
    res_aryan = seed_company_engagement(conn, ARYAN_COMPANY)
    res_hitansh = seed_company_engagement(conn, HITANSH_COMPANY)
    res_jeet = seed_company_engagement(conn, JEET_COMPANY)

    # Seed initial reconciliations for all 3 entities
    try:
        from backend.app.services.gst_reconciliation_engine import run_gst_reconciliation
        from backend.app.services.bank_reconciliation_engine import run_bank_reconciliation
        from backend.app.services.sales_purchase_reconciliation_engine import run_sales_purchase_reconciliation

        recon_configs = [
            (res_aryan["cy_engagement_id"], "Aryan Fintech", "HDFC Bank Ltd", "aryan"),
            (res_hitansh["cy_engagement_id"], "Hitansh Fintech", "ICICI Bank Ltd", "hitansh"),
            (res_jeet["cy_engagement_id"], "Jeet Fintech", "Axis Bank Ltd", "jeet")
        ]

        for eid, cname, bank_ldg, prefix in recon_configs:
            f_map = {r["file_name"]: r["id"] for r in conn.execute("SELECT id, file_name FROM uploaded_files WHERE engagement_id = ?", (eid,)).fetchall()}
            # 1. GST Reconciliation (GSTR-2B vs Purchase Register)
            if f_map.get(f"{prefix}_gst_portal.csv") and f_map.get(f"{prefix}_purchase_register.csv"):
                run_gst_reconciliation(
                    engagement_id=eid,
                    source_a_file_id=f_map[f"{prefix}_gst_portal.csv"],
                    source_a_type="PORTAL",
                    source_b_file_id=f_map[f"{prefix}_purchase_register.csv"],
                    source_b_type="PURCHASE",
                    ledger_name="GST Input Tax Credit",
                    recon_title=f"GSTR-2B vs Purchase Register ({cname})",
                    created_by="SYSTEM_SEED"
                )
            # 2. Bank Reconciliation (BRS)
            if f_map.get(f"{prefix}_bank_statement.csv"):
                run_bank_reconciliation(
                    engagement_id=eid,
                    bank_ledger_name=bank_ldg,
                    file_b_id=f_map[f"{prefix}_bank_statement.csv"],
                    title=f"Bank Reconciliation Statement - {bank_ldg} ({cname})",
                    created_by="SYSTEM_SEED"
                )
            # 3. Sales Register vs GL
            if f_map.get(f"{prefix}_sales_register.csv"):
                run_sales_purchase_reconciliation(
                    engagement_id=eid,
                    recon_type="Sales Reconciliation",
                    register_file_id=f_map[f"{prefix}_sales_register.csv"],
                    ledger_name="Sales Revenue",
                    title=f"Sales Register vs General Ledger ({cname})",
                    created_by="SYSTEM_SEED"
                )
            # 4. Purchase Register vs GL
            if f_map.get(f"{prefix}_purchase_register.csv"):
                run_sales_purchase_reconciliation(
                    engagement_id=eid,
                    recon_type="Purchase Reconciliation",
                    register_file_id=f_map[f"{prefix}_purchase_register.csv"],
                    ledger_name="Cost of Goods Sold",
                    title=f"Purchase Register vs General Ledger ({cname})",
                    created_by="SYSTEM_SEED"
                )
    except Exception as recon_err:
        print(f"[!] Warning: Pre-computing reconciliations in seed failed: {recon_err}")

    conn.commit()
    conn.close()
    return {
        "aryan": res_aryan,
        "hitansh": res_hitansh,
        "jeet": res_jeet
    }

if __name__ == "__main__":
    out = seed_test_database()
    print("Test Database successfully seeded with Aryan Fintech and Hitansh Fintech:")
    print(out)
