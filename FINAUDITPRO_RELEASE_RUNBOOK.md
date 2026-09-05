# FINAUDITPRO — PRODUCTION RELEASE RUNBOOK

**Document Version:** 1.0.0  
**Target Audience:** Audit Firm IT Administrators, Practice Managers, Managing Partners  
**Applies to:** FinAuditPro v1.2.0 (Enterprise Edition)  

---

## 1. System Requirements & Architecture Overview

FinAuditPro is an **offline-first**, zero-cloud desktop application engineered specifically for Indian Chartered Accountancy firms. All client financial data, audit evidence, and cryptographically chained audit trails remain on the local workstation or firm-managed local network storage.

### Hardware Prerequisites
- **Processor:** 64-bit x86_64 or Apple Silicon (arm64)
- **RAM:** 8 GB minimum (16 GB recommended for high-volume ledger analytics > 500,000 vouchers)
- **Storage:** 2 GB for application binary and base libraries; SSD storage strongly recommended for database and document vaults

### Software Prerequisites
- **Operating System:** macOS 12+ (Monterey, Ventura, Sonoma, Sequoia), Windows 10/11 64-bit, or Ubuntu Linux 22.04 LTS+
- **Python Runtime:** Python 3.12 or newer (standard distribution)
- **Virtual Environment:** Dedicated virtual environment isolated from system packages

---

## 2. Installation & Clean-Room Deployment

### Step 2.1: Clone and Environment Isolation
```bash
# Clone the repository
git clone https://github.com/Coderaryanyadav/FinAuditPro.git
cd FinAuditPro

# Create and activate virtual environment
python3.12 -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate

# Upgrade packaging tools and install production dependencies
pip install --upgrade pip setuptools wheel
pip install -e .
```

### Step 2.2: Environment Variable Configuration
Configure the target data directory if running outside default user paths:
```bash
# Default path is ~/.finauditpro
export FINAUDITPRO_DATA_DIR="/Volumes/SecureStorage/finauditpro_data"
```

### Step 2.3: Initial Database & Security Vault Setup
Launch the application setup routine:
```bash
# Automated initialization of SQLite WAL database and schema tables
python -m finauditpro
```
On first launch, the Onboarding Wizard will guide the Managing Partner through:
1. Defining the **Firm Profile** (Firm Name, FRN, Address).
2. Generating the **Master Passcode** (anchoring Scrypt Key Wrapping Key).
3. Enrolling the Initial **Administrator Account** and setting up RFC 6238 TOTP 2FA.

---

## 3. Cryptographic Key Management & Passcode Rotation

FinAuditPro protects sensitive client financial data and identity fields using envelope encryption:
- **DEK (Data Encryption Key):** High-entropy 256-bit AES key used for column-level encryption.
- **KWK (Key Wrapping Key):** Derived from the firm master passcode via Scrypt (`N=32768, r=8, p=1`).

### Passcode Rotation Procedure
When the practice master passcode must be changed (e.g. partner transition or periodic hygiene):
1. Launch the interactive key rotation utility:
   ```bash
   python -c "
   from finauditpro.infrastructure.security.encryption import rotate_passcode
   old_pass = input('Current Master Passcode: ')
   new_pass = input('New Master Passcode: ')
   rotate_passcode(old_pass, new_pass)
   print('Master passcode successfully rotated. All DEK wrappings updated.')
   "
   ```
2. Verify that the application starts cleanly and existing encrypted fields decrypt as expected.

---

## 4. Daily Operational Procedures

### 4.1 User Provisioning & Segregation of Duties (SoD)
Only users holding the `Administrator` or `Partner` role can create new user accounts.
- **Roles:**
  - `Partner`: Unrestricted access, final audit report sign-off, UDIN attribution, archival sealing.
  - `Manager`: Engagement supervision, sample selection approval, review note clearing.
  - `Senior`: Audit procedure execution, substantive testing, working paper initial review.
  - `Associate`: Data entry, document ingestion, voucher sampling, preparatory workpapers.

### 4.2 Standard Engagement Lifecycle
1. **Planning:** Define materiality benchmarks (SA 320), document significant risks (SA 315), and map substantive procedures (SA 330).
2. **Execution:** Ingest client General Ledgers, Bank Statements, and Registers. Run deterministic analytics, formulate AJE adjustments, and collect SHA-256 verified evidence.
3. **Review:** Clear all review notes. Senior review followed by Partner review.
4. **Finalization Gate:** Address all 10 mandatory gate categories (SA 570 Going Concern, SA 580 MRL, SA 450 Misstatements, CARO 2020 completeness).
5. **Sealing:** Partner signs off with UDIN. The engagement transitions to `COMPLETED` and becomes **read-only / immutable**.

---

## 5. Backup & Disaster Recovery Runbook

### 5.1 Automated Encrypted Backup
FinAuditPro backups are self-contained, encrypted `.fapb` archives containing the SQLite database snapshot, document storage vault, and cryptographic manifests.

To execute an ad-hoc backup:
```bash
python -c "
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.application.services.backup_restore_service import BackupRestoreService

db = initialize_database()
svc = BackupRestoreService(db)
svc.create_backup('/path/to/backup_target.fapb', passphrase='FirmBackupSecretPassword#2026')
print('Encrypted backup generated successfully.')
"
```

### 5.2 Disaster Recovery / Restoring from Scratch
In the event of hardware failure, ransomware containment, or system loss:
1. Reinstall FinAuditPro on a clean workstation as per Section 2.
2. Restore the latest encrypted backup:
   ```bash
   python -c "
   from finauditpro.infrastructure.first_run import initialize_database
   from finauditpro.application.services.backup_restore_service import BackupRestoreService

   db = initialize_database()
   svc = BackupRestoreService(db)
   svc.restore_backup('/path/to/backup_target.fapb', passphrase='FirmBackupSecretPassword#2026')
   print('Complete system and engagement vault restored successfully.')
   "
   ```
3. Verify audit trail integrity:
   ```bash
   python -c "
   from finauditpro.infrastructure.first_run import initialize_database
   from finauditpro.infrastructure.persistence.repositories import AuditEventRepository

   db = initialize_database()
   with db.session_scope() as session:
       is_valid = AuditEventRepository(session).verify_chain()
       print('Audit Event Hash-Chain Status:', 'VALID (INTACT)' if is_valid else 'CORRUPT')
   "
   ```

---

## 6. Emergency Recovery & Troubleshooting FAQ

### Issue 1: "Tamper-Seal Invariant Violated" on closed engagement
- **Root Cause:** A user is attempting to add an adjustment, edit working papers, or re-sign off on an engagement that has already been finalized (`COMPLETED` or `ARCHIVED`).
- **Resolution:** By design under ICAI standards and SA 230, sealed audit files cannot be modified. If new facts emerge (SA 560 Subsequent Events), the Partner must use the formal **Reopen Engagement** workflow with mandatory justification notes and peer partner concurrence.

### Issue 2: "SQLite DateTime type only accepts Python datetime objects"
- **Resolution:** Ensure all custom scripts pass native `datetime` objects with timezone awareness (`datetime.now(UTC)`) rather than raw ISO formatted strings to ORM models.

### Issue 3: Workstation UI Locked
- **Resolution:** Click the unlock prompt, enter the Scrypt master passcode (or use TouchID / Windows Hello if biometrics are enabled in Settings).

---

## 7. Operational Acceptance Sign-Off

This runbook has been verified and validated against the production release candidate.

- **Author:** FinAuditPro Release Engineering Team  
- **Reviewer:** CA Rajesh Sharma, FCA (Senior Partner)  
- **Effective Date:** 2026-09-05  
