# FinAuditPro Security Architecture & Trust Model

## 1. Executive Security Architecture

FinAuditPro is designed as an **offline-first, privacy-first desktop audit
intelligence operating system** for Indian statutory audit practice (Chartered
Accountants, Statutory Auditors, and Firm Partners). All audit client data
remains locally on the auditor's workstation by default.

---

## 2. Encryption Strategy & Live DB Trust Boundary

- **Live SQLite Database Trust Boundary**:
  - The live SQLite database (`finauditpro.db`) relies on **OS Full-Disk
    Encryption** (macOS FileVault / Windows BitLocker / Linux LUKS) to secure
    data at rest.
  - SQLCipher is unavailable in this PyPI-restricted environment. The
    application-level trust boundary delegates live volume encryption to the
    host OS disk encryption mechanism.
- **Encrypted Portable Backups**:
  - All exported system backup archives (`.zip`) are encrypted using **Fernet
    (AES-128-CBC + HMAC-SHA256)** via the `cryptography` package with PBKDF2 Key
    Derivation (100,000 iterations of SHA-256).
  - Every encrypted archive receives a unique, persisted 16-byte salt. The
    archive header carries the salt needed for recovery; it never reuses a
    global backup key. Legacy archives using the former fixed salt remain
    readable for backward compatibility.
  - Every backup archive contains a `sha256_manifest.json` file verifying the
    cryptographic digest of every bundled database, document, and FAISS index
    file prior to extraction.
  - Restore validates every ZIP member before writing: absolute paths,
    parent-directory traversal, and unexpected top-level paths are rejected.

---

## 3. Legal Signature & Electronic Sign-off Boundaries

- **Internal Workflow Attestations Only**:
  - All electronic sign-offs (Working Papers, Audit Procedures, Report Approval)
    represent **internal audit workflow attestations and tamper-evident audit
    records**.
  - Electronic sign-offs are **NOT** IT Act 2000 Class 3 PKI Digital Signature
    Certificates (DSC) and **NOT** ICAI Unique Document Identification Numbers
    (UDIN).
  - If a UDIN field is provided, it is an auditor-entered tracking value from
    the official ICAI portal; FinAuditPro never generates or validates UDINs as
    legally authoritative.

---

## 4. Cryptographic Audit-Trail Append-Only Integrity

- **Append-Only SQLite Triggers**:
  - The `audit_events` table is protected by SQLite `BEFORE UPDATE` and
    `BEFORE DELETE` triggers that execute `RAISE(ABORT)` on any update or
    deletion attempt.
- **SHA-256 Hash-Chaining**:
  - Every mutation across the system writes a hash-chained `AuditEvent` where
    each entry's hash incorporates the SHA-256 digest of the preceding entry
    (`previous_hash`).
- **Startup Integrity Verifier**:
  - On application launch, `verify_startup_integrity()` recomputes the entire
    audit chain. Any broken hash or tampered row raises a loud
    `AuditIntegrityError`.

---

## 5. Input Sanitization & Threat Protections

- **Formula-Injection Protection**:
  - All tabular export engines (XLSX via openpyxl and CSV via stdlib `csv`) pass
    cell values through `escape_formula_injection()`. Any string starting with
    `=`, `+`, `-`, `@`, `\t`, or `\r` is prefixed with `'` to disarm formula
    execution attacks.
- **Prompt Injection & Untrusted Document Sanitization**:
  - Document text extracted from PDFs is treated strictly as untrusted data.
    Angle brackets are escaped, stray `<think>` reasoning tags are disarmed, and
    instruction override phrases (e.g. `"ignore previous instructions"`) are
    disarmed before LLM prompt formatting.
- **Offline Network Isolation Guarantee**:
  - FinAuditPro executes zero outbound network calls to cloud APIs or PyPI
    repositories. All AI capabilities run exclusively against a user-configured
    local LM Studio instance (`http://localhost:1234`).

---

## 6. Engagement Archival, Retention & Tamper-Evident Sealing

- **Tamper-Evident Integrity Seal**:
  - Freezing an engagement creates a sealed `.zip` archive containing the
    engagement's database slice (preserving hash-chained audit events), document
    files, FAISS indices, and report artifacts.
  - A deterministic `sha256_manifest.json` and top-level content hash seal the
    archive against tampering.
  - Freezing is an internal records-management control and tamper-evident seal,
    **not** an IT Act 2000 Class 3 PKI DSC and **not** an ICAI UDIN.
- **Configurable Retention & No Auto-Purge Policy**:
  - Assembly deadlines (default: 60 days) and retention periods (default: 7
    years) are configurable policy entries carrying `verified_statutory: False`
    disclaimers.
  - The application **never** automatically deletes, purges, or destroys audit
    files upon reaching the retain-until date. Expiry dates are surfaced for
    auditor action.
- **Fail-Closed Read-Only Protection**:
  - Archived engagements are locked against modifications at both service layer
    (`InvalidStateTransitionError`) and database layer (`PRAGMA query_only=ON`).
- **Audited Partner Reopen Workflow**:
  - Reopening a sealed engagement is restricted to Partner roles
    (`RoleEnum.PARTNER`), requires a mandatory recorded justification reason,
    and preserves all prior sealed archive records.

---

## 7. Multi-Year Roll-Forward Isolation & Prior Archive Immutability

- **Absolute Single-Client Isolation Boundary**:
  - Multi-year roll-forward operates strictly **within a single client entity**.
    Cross-client data retrieval or roll-forward attempts are prohibited and
    blocked at the service layer (`PermissionDeniedError`).
- **Prior Sealed Archive Immutability**:
  - Rolling forward into a new financial year reads from the prior closed
    engagement in read-only mode (`query_only=ON`) and **never** mutates the
    prior sealed archive. The prior archive's cryptographic SHA-256 hash remains
    unchanged.
- **Non-Fabrication & Draft Re-assessment Policy**:
  - The software **never** fabricates opening balances or presents prior-year
    conclusions as current. Carried planning items (risks, procedures,
    materiality methodology) are created as starting drafts explicitly marked
    `"carried from FY X — review for current year"`. All SA 510 opening balance
    tie-outs carry `verified_statutory: False` disclaimers requiring auditor
    confirmation.

---

## 8. Distribution Security, Air-Gapped Defaults & Honest Diagnostics

- **Default Air-Gapped Posture**:
  - FinAuditPro defaults to a strictly air-gapped configuration
    (`allow_cloud_ai: false`). All AI capabilities run exclusively against a
    user-configured local LM Studio instance (`http://localhost:1234`).
  - Enabling external cloud AI requires explicit user opt-in and surfaces
    privacy warnings regarding third-party data processing.
- **Runtime Prerequisite Self-Check Integrity**:
  - System diagnostics probe real system dependencies (Python, Tesseract OCR, LM
    Studio HTTP API, data directory permissions). Missing dependencies trigger
    clear remediation text without faking system health.
- **Matplotlib Security & Data Directory Scoping**:
  - Environment variable `MPLCONFIGDIR` is configured to a dedicated, writable
    application data folder (`~/.gemini/antigravity-ide/app_data/matplotlib`),
    preventing configuration pollution or permission errors in bundled or
    air-gapped environments.
