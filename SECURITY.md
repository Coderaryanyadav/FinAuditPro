# Security Policy

## Supported Versions

Currently, FinAuditPro is in active development. Only the latest release is supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Core Security Tenets

FinAuditPro handles highly sensitive financial data and audit trails. Therefore, we abide by the following security principles:
1. **Offline-First**: Financial data and models must reside locally. The app should not enforce cloud connectivity.
2. **Zero-Trust Storage**: All sensitive fields in the SQLite database and exported files should be encrypted at rest using AES-256 (via PBKDF2 key derivation from hardware identifiers).
3. **Immutable Auditing**: All critical actions (Logins, Engagements, Finding Resolutions) must be logged in a local, cryptographically signed ledger that is resistant to tampering.

## Reporting a Vulnerability

If you discover a security vulnerability in FinAuditPro, please **DO NOT** open a public issue. We take security extremely seriously and appreciate your efforts to responsibly disclose your findings.

Please report security issues via email to:
**security@finauditpro.com**

In your email, please include:
- A description of the vulnerability.
- Steps to reproduce the vulnerability.
- The version of FinAuditPro affected.
- Potential impact and recommended mitigation if known.

We will acknowledge receipt of your vulnerability report within 48 hours and strive to send you regular updates about our progress. If a fix is required, we will credit you (if desired) in our release notes and Security Advisories.
