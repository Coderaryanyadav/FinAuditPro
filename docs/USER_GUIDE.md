# FinAuditPro v1.0.0 — User Guide & Practitioner Manual

**Application Version:** 1.0.0  
**Target Audience:** Statutory Auditors, Audit Partners, Senior Reviewers, and Audit Associates  

---

## 1. Statutory Audit Workflow Lifecycle

FinAuditPro follows the standard statutory audit workflow from onboarding to multi-year roll-forward:

```text
First-Run Wizard
      ↓
Firm Profile Setup
      ↓
Client Creation
      ↓
Engagement Initialization (FY & Audit Type)
      ↓
Planning & Risk Assessment (SA 315 / SA 330)
      ↓
Materiality Calculation (SA 320)
      ↓
Financial Data Ingestion (Trial Balance & GL)
      ↓
Deterministic Financial Analytics (Benford, Duplicates, Cutoff)
      ↓
Substantive Audit Procedures & Sampling Execution
      ↓
Working Paper Documentation & Evidence Linking (SA 230 / SA 500)
      ↓
Maker-Checker Review & Senior / Partner Sign-Off
      ↓
Misstatement Accumulation & Evaluation (SA 450)
      ↓
Going Concern (SA 570) & Subsequent Events (SA 560)
      ↓
Report Assembly & Statutory Audit Report Generation
      ↓
Finalization Checklist Gates & Archival Sealing
      ↓
Encrypted Backup Archive & Next-Year Roll-Forward (SA 510)
```

---

## 2. Step-by-Step Operations

### Step 1: Initial Launch & Administrator Setup
1. Launch FinAuditPro.
2. The **Administrator Setup Wizard** will appear automatically.
3. Configure your custom administrator email and master password (minimum 8 characters, containing letters and numbers/symbols).
4. Note your credentials; no default backdoors exist.

### Step 2: Firm & Client Configuration
1. Navigate to **Dashboard / Settings**.
2. Add your CA Firm profile (Name, FRN, PAN, Email).
3. Create client corporate records (Entity Type, PAN, GSTIN, CIN).

### Step 3: Create Audit Engagement
1. Create a new engagement selecting the client, financial year (e.g., `2024-25`), and audit type (Statutory Audit, Tax Audit, Internal Audit).
2. Assign engagement team members with appropriate RBAC roles (Partner, Manager, Senior, Associate).

### Step 4: Import Financial Data
1. Navigate to **Financial Data**.
2. Import Trial Balance and General Ledger CSV or XLSX files.
3. Verify trial balance tie-out (Debits == Credits). Any discrepancy will flag an out-of-balance warning.

### Step 5: Materiality & Risk Assessment
1. Open **Materiality Engine** and select benchmark (e.g., Revenue, PBT, Total Assets).
2. Calculate Overall Materiality, Performance Materiality, and Clearly Trivial Thresholds.
3. Document qualitative risks and link them to financial statement assertions.

### Step 6: Working Papers & Maker-Checker Sign-Off
1. Create working papers indexed by audit area (e.g., `B-10` for Cash & Bank, `REV-01` for Revenue).
2. Attach extracted evidence and document test lines.
3. Submit for review. Preparers cannot sign off on their own workpapers.
4. Reviewers and Partners execute two-tier sign-off.

### Step 7: Finalization & Sealing
1. Complete mandatory finalization checklist gates (MRL chronology, open review notes resolution, Going Concern assessment).
2. Seal the engagement. This permanently freezes all working papers and trial balances against post-audit mutation.

---

## 3. Important Warnings & Irreversible Actions

* **Sealing an Engagement:** Archival sealing calculates an irreversible SHA-256 manifest hash and locks all records. Reopening requires a justified Partner override that is logged to the immutable audit trail.
* **Backup Passphrases:** Encrypted backups use client-side AES-128 encryption. If the backup passphrase is lost, the backup cannot be recovered.
