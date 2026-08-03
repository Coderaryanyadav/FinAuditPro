# Security & Governance Policy

## Threat Model & Security Architecture Overview

FinAuditPro is an air-gapped, privacy-first desktop application designed for Indian Chartered Accountant (CA) firms performing statutory audits. All AI processing (via Ollama local LLM and FAISS vector indices) and data storage remain strictly on-premises on the user's local hardware.

---

## 1. Cryptographic Safeguards

- **Password Hashing**: PBKDF2-HMAC-SHA256 with 600,000 iterations default and a strict, enforced floor of **100,000 iterations** (`MINIMUM_ITERATIONS` enforced in both `src/core/config.py` and `src/security/auth.py`). Each user account uses a unique 16-byte cryptographically secure random salt.
- **Fernet Cipher & Key Derivation**: AES-128-CBC encryption with HMAC-SHA256 authentication (via Fernet specification) used for session storage, persistent lockout state (`data/.login_lockouts.json`), and compressed backup archives (`.enc`). AES installation keys (`.crypto_key` and `.crypto_salt`) are cached per process to prevent inter-test decryption mismatches.
- **JWT Authentication & Anti-Replay Claims**: API tokens include standard RFC 7519 `jti` (unique 16-byte hexadecimal token identifier) claims. Revoked tokens are tracked in encrypted persistent storage (`.revoked_tokens.json`). Unique `jti` claims guarantee that duplicate logins for the same user yield cryptographically distinct token signatures, preventing revocation collisions.
- **CORS Middleware Hardening**: `api/main.py` dynamically detects wildcard origins (`"*"`) in `allowed_origins` and automatically enforces `allow_credentials=False`, preventing cross-origin credential theft vulnerabilities (CWE-942).
- **Live Database Security & At-Rest Encryption**:
  - Primary local database: Standard SQLite database (`finauditpro.db`) with SQLCipher (`pysqlcipher3`) transparent AES-256 page-level encryption enabled when driver is present.
  - Disk Encryption: OS-level full disk encryption (BitLocker on Windows, FileVault on macOS, LUKS on Linux) is strongly recommended for offline workstation protection.
- **Audit Ledger Hash-Chain Integrity**: Immutable hash chain (`entry_hash` including `previous_hash` with SHA-256) verified on application bootstrap (`src/deployment/bootstrap.py`). Integrity failures generate `CRITICAL` log alerts and self-log security tamper events.


---

## 2. Digital Signatures & Statutory Verification Notice

- **Internal Integrity Verification**: Cryptographic signing in `src/reporting/digital_signature.py` utilizes **Ed25519 asymmetric keypairs** (`Ed25519PrivateKey` / `Ed25519PublicKey`).
- **QR Code Verification**: QR payload strings include an **HMAC-SHA256 MAC** generated over canonical JSON data (`src/reporting/qr_verification.py`), guaranteeing payload tamper-detection.
- **Statutory Notice (Indian IT Act 2000 & ICAI Guidelines)**:
  > **IMPORTANT**: Ed25519 signatures and internal QR payloads verify *internal document and audit log hash-chain integrity*. They do **NOT** replace statutory Class 3 PKI X.509 Digital Signature Certificates (DSC) issued by licensed Certifying Authorities (e.g., eMudhra, nCode, Capricorn) on hardware USB tokens (PKCS#11) required for official filing of Form 3CA/3CB/3CD with tax authorities.

---

## 3. Authorization & Role-Based Access Control (RBAC)

- **Roles (6)**: `ADMINISTRATOR`, `AUDIT_PARTNER`, `AUDIT_MANAGER`, `SENIOR_AUDITOR`, `ARTICLED_ASSISTANT`, `READ_ONLY`.
- **Service-Layer Enforcement**: Authorization is strictly enforced within the service layer (`ClientService`, `DocumentService`, `WorkingPaperService`, `AuthenticationService`).
- **Unauthenticated Gating**: Any service invocation without an active session (`sm.current_session is None`) raises an `AuthError` exception immediately, preventing authorization bypasses via scripts or secondary UI layers.

---

## 4. Input Validation & Exploitation Defenses

- **Magic-Byte Sniffing**: `DocumentValidator` verifies raw file header magic bytes (`%PDF`, `\x89PNG`, `\xff\xd8\xff`, `PK\x03\x04`) alongside extension checks.
- **Zip-Slip Protection**: `BackupEngine._safe_extract` normalizes target extraction paths to prevent path traversal outside extraction directories.
- **Spreadsheet Formula Injection**: `ExcelExportEngine.sanitize_value` escapes potentially malicious leading characters (`=`, `+`, `-`, `@`, `\t`, `\r`) with a single quote (`'`).
- **AI Prompt Injection Encapsulation**: `PromptEngine._sanitize_and_wrap_context` sanitizes HTML entities (`html.escape`) and wraps untrusted input inside `<untrusted_document_context>` XML blocks with explicit system instructions forbidding inline instruction overrides across all 8 prompt builders.
