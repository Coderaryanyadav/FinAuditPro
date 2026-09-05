# FinAuditPro — Final Forensic Blocker Table

**Date:** 2026-09-05  
**Commit:** `a7520b767ace6e4923e75bfc08a10ede5a83cd1b`

---

## P0 Blockers (Release-Critical)

None identified. All P0 controls independently verified.

---

## P1 Blockers (Significant — Must Document)

### BLOCKER-001: Lockout Bypass via Filesystem

| Field | Detail |
|-------|--------|
| **ID** | BLOCKER-001 |
| **Severity** | P1 |
| **Problem** | The failed-login lockout counter is stored entirely in `lockout.json` on the local filesystem. Any OS-level user with write access to the app data directory can delete this file and reset the lockout counter, bypassing brute-force protection. |
| **Reproduction** | 1. Fail login 5 times. 2. Verify lockout error. 3. `rm $FINAUDITPRO_APP_DATA_DIR/lockout.json`. 4. Login attempt succeeds (counter reset). |
| **Affected Component** | `src/finauditpro/infrastructure/security/lockout.py` |
| **Required Fix** | Supplement file-based counter with in-memory counter that persists for process lifetime. File deletion should not fully reset state during the current process run. |
| **Current Status** | Unresolved. Accepted risk for single-user desktop deployment where OS access = physical access. Must be documented in security posture. |

### BLOCKER-002: Test Order-Dependency (Encryption) — FIXED

| Field | Detail |
|-------|--------|
| **ID** | BLOCKER-002 |
| **Severity** | P1 (now resolved) |
| **Problem** | `test_column_encryption_and_decryption` failed when run in isolation; passed in full suite due to hidden dependency on global `_CIPHER` state initialized by an earlier test. `test_automated_system_check_execution` also failed for the same reason (system check called `encrypt_sensitive_string` without cipher context). |
| **Reproduction** | `uv run pytest tests/test_security_hardening.py::test_column_encryption_and_decryption` → 1 failed. |
| **Fix Applied** | Both tests now initialize isolated cipher via `monkeypatch`/transient temp-dir. |
| **Current Status** | **RESOLVED.** Both tests pass in isolation and in full suite. |

---

## P2 Findings (Non-Blocking — Must Document)

### FINDING-P2-001: Hardcoded Fallback Passphrase in Source Code

| Field | Detail |
|-------|--------|
| **ID** | FINDING-P2-001 |
| **Severity** | P2 |
| **Problem** | `get_fernet_cipher()` contains a discoverable hardcoded passphrase `"FinAuditPro-Local-Column-Secret-Key"` used as the fallback DEK initialization when no key file exists. This is in plaintext in the repository. |
| **Impact** | Only activates in test/legacy environments without a `.secret_key.key` file. A correctly bootstrapped production environment always has the key file and never hits this path. |
| **Required Action** | Document this explicitly in deployment guide. Consider removing the fallback and requiring explicit initialization in all code paths. |
| **Current Status** | Documented. Not fixed in this verification pass (would require test suite changes). |

---

## P3 Findings (Informational)

### FINDING-P3-001: Admin Role Has No RBAC Permission Entries

| Field | Detail |
|-------|--------|
| **Severity** | P3 |
| **Problem** | `_ROLE_PERMISSIONS` in `rbac.py` has no entry for `RoleEnum.ADMINISTRATOR`. `check_permission()` returns `False` for all permissions when called with an admin session. |
| **Impact** | Admin operations bypass RBAC checks entirely at the service layer (not through RBAC permission strings). This is by design but creates a gap where RBAC auditing cannot log admin permission usage uniformly. |
| **Required Action** | Document the design decision. Optionally add a wildcard admin permission entry for auditing clarity. |

