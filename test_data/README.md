# FinAuditPro Test Data Architecture

This directory provides a completely independent, deterministic, and auditable test-data subsystem for **FinAuditPro**, configured strictly for the three approved test client entities:
1. **Aryan Fintech Pvt. Ltd. (ARYAN)**
2. **Hitansh Fintech Pvt. Ltd. (HITANSH)**
3. **Jeet Fintech Pvt. Ltd. (JEET)**

---

## 1. Approved Test Client Profiles

### Company 1: Aryan Fintech Pvt. Ltd. (ARYAN)
- **Industry**: Financial Technology / Software Services
- **Entity Type**: Private Limited Company
- **State**: Maharashtra (State Code `27`), Mumbai `400051`
- **PAN**: `AAPCA1111A` (Synthetic Test PAN)
- **GSTIN**: `27AAPCA1111A1Z1` (Synthetic Test GSTIN)
- **Primary Contact**: Aryan Sharma (`aryan@example.test`)
- **Financial Years**: Current FY 2025-26 & Prior FY 2024-25
- **Assigned Auditor & Staff**: `auditor_aryan` (UID 2), `staff_aryan` (UID 3)

### Company 2: Hitansh Fintech Pvt. Ltd. (HITANSH)
- **Industry**: Financial Technology / SaaS
- **Entity Type**: Private Limited Company
- **State**: Maharashtra (State Code `27`), Mumbai `400021`
- **PAN**: `AAHCH2222H` (Synthetic Test PAN)
- **GSTIN**: `27AAHCH2222H1Z2` (Synthetic Test GSTIN)
- **Primary Contact**: Hitansh Mehta (`hitansh@example.test`)
- **Financial Years**: Current FY 2025-26 & Prior FY 2024-25
- **Assigned Auditor & Staff**: `auditor_hitansh` (UID 4), `staff_hitansh` (UID 5)

### Company 3: Jeet Fintech Pvt. Ltd. (JEET)
- **Industry**: Financial Technology / Neo-Banking
- **Entity Type**: Private Limited Company
- **State**: Maharashtra (State Code `27`), Pune `411028`
- **PAN**: `AAJCJ3333J` (Synthetic Test PAN)
- **GSTIN**: `27AAJCJ3333J1Z3` (Synthetic Test GSTIN)
- **Primary Contact**: Jeet Patel (`jeet@example.test`)
- **Financial Years**: Current FY 2025-26 & Prior FY 2024-25
- **Assigned Auditor & Staff**: `auditor_jeet` (UID 6), `staff_jeet` (UID 7)

---

## 2. Directory Layout & Module Organization

All files in `test_data/` correspond directly to the platform's 5 core functional sections:

### Section I: AUDIT MANAGEMENT
- **Dashboard, Clients & Engagements**:
  - `companies.py`: Authoritative corporate metadata for Aryan, Hitansh, and Jeet.
  - `clients.py`: Client master record loaders.
  - `seed.py`: Deterministic database seeder for test users, clients, and engagements.
- **Data Import & Cleaning Logs**:
  - `transactions.py`: Ingestion & parsing for current and prior-year transactions.
  - `generator.py`: Generates verified input CSVs with zero date fabrication.

### Section II: CORE ACCOUNTING & AUDIT
- **Trial Balance & General Ledger**:
  - `trial_balance.py`: Standard accounting group chart of accounts & normal balances.
  - `{company}_fintech/transactions.csv`: General ledger debit/credit transactions.
- **Reconciliation (BRS / 2B)**:
  - `bank_data.py` & `{company}_fintech/bank_statement.csv`: Bank statements for BRS matching.
  - `gst_data.py` & `{company}_fintech/gst_portal.csv`: Auto-drafted GSTR-2B invoice datasets.
  - `{company}_fintech/sales_register.csv` & `purchase_register.csv`: GSTR-1 and GSTR-3B reconciliation.
- **Financial Statements & YoY Comparison**:
  - `{company}_fintech/prior_year_transactions.csv`: Comparative FY 2024-25 financials.
  - `{company}_fintech/expected_results.json`: Baseline mathematical totals & invariants.
- **Duplicates & Sequence Gaps**:
  - Anomaly test cases embedded in `{company}_fintech/transactions.csv`.

### Section III: AUDIT INTELLIGENCE
- **Anomaly Detection**:
  - `scenarios.py`: Configures `CLEAN` vs `STRESS` anomaly injection vectors (Sec 40A(3), Sec 269ST, weekend dates).
- **Risk & Findings**:
  - `findings.py`: Statutory findings catalog linked to standard ICAI rules.
- **Audit Assistant**:
  - Isolated test context builders ensuring strict tenant isolation across Aryan, Hitansh, and Jeet.

### Section IV: COMPLIANCE & OUTPUT
- **Audit Checklist**:
  - `checklists.py`: CARO 2020 and Schedule III statutory checklist fixtures.
- **Working Papers**:
  - `working_papers.py`: Standard SA 230 audit working papers for Revenue, Cash & Bank, and GST.
- **Audit Reports & Trail**:
  - Seeded tamper-evident SHA-256 event chains in `seed.py`.

### Section V: ADMINISTRATION
- **User Management & Settings**:
  - `seed.py`: Creates strict RBAC test accounts (`admin`, `auditor_aryan`, `staff_aryan`, `auditor_hitansh`, `staff_hitansh`, `auditor_jeet`, `staff_jeet`).

