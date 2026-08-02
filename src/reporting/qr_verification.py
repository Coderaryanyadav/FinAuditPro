"""
QR Verification Payload & Token Generator for FinAuditPro.
Generates HMAC-SHA256 authenticated verification payload data for embedding QR code
security blocks in audit reports.

IMPORTANT: This provides tamper-detection for the QR payload itself (i.e., any
modification of the QR data after generation will be detected). This is NOT a
statutory IT Act 2000 Class 3 PKI Digital Signature. For legal ICAI signatures,
auditors must use a CA-issued USB hardware token (eMudhra / nCode / Capricorn).
"""

import hmac
import hashlib
import os
import json
import base64
from typing import Dict, Any, Optional


class QRVerificationManager:
    """Generates HMAC-SHA256 authenticated QR verification payload data strings for reports."""

    # Installation-scoped HMAC key: derived from installation crypto key, or a
    # per-process random key as a safe fallback. Either way the key is never
    # embedded in the QR — so forged QR payloads will fail verification.
    _hmac_key: Optional[bytes] = None

    @classmethod
    def _get_hmac_key(cls) -> bytes:
        """Return or initialize the installation HMAC key."""
        if cls._hmac_key is None:
            try:
                from security.crypto import _get_or_create_installation_key
                from core.config import config
                cls._hmac_key = _get_or_create_installation_key(config.data_dir)
            except Exception:
                # Safe fallback: per-process random key (survives within one session)
                cls._hmac_key = os.urandom(32)
        return cls._hmac_key

    @staticmethod
    def _compute_payload_hmac(payload: Dict[str, Any], key: bytes) -> str:
        """Compute a truncated HMAC-SHA256 over the canonical JSON of the payload (excluding the mac field)."""
        # Canonical serialization: sorted keys, no spaces, exclude 'mac' field itself
        payload_without_mac = {k: v for k, v in payload.items() if k != "mac"}
        canonical = json.dumps(payload_without_mac, sort_keys=True, separators=(",", ":"))
        mac = hmac.new(key, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        # Return first 32 hex chars (128 bits) — sufficient for integrity verification
        return mac[:32]

    @classmethod
    def generate_verification_payload(
        cls,
        report_id: str,
        client_name: str,
        gstin: str,
        document_hash: str,
        udin: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Constructs an HMAC-SHA256 authenticated QR verification dictionary payload.

        The 'mac' field authenticates the payload — any post-generation modification
        of any other field will invalidate the MAC. The MAC is verified by
        `verify_payload_mac()`.

        NOTE: 'status' reflects whether the report hash was recorded at generation
        time, not whether it is legally certified. Statutory certification requires
        ICAI UDIN + CA-issued PKI DSC hardware token.
        """
        payload: Dict[str, Any] = {
            "system": "FinAuditPro Internal Audit Integrity Verification",
            "report_id": report_id,
            "client_name": client_name,
            "gstin": gstin or "N/A",
            "document_hash_sha256": document_hash,
            "udin": udin or "UDIN PENDING — visit https://udin.icai.org/",
            "integrity_method": "HMAC-SHA256 (internal, non-PKI)",
            "statutory_notice": (
                "NOT a statutory IT Act 2000 Class 3 PKI DSC. "
                "For legal ICAI digital signatures, use a CA-issued USB hardware token."
            ),
        }
        key = cls._get_hmac_key()
        payload["mac"] = cls._compute_payload_hmac(payload, key)
        return payload

    @classmethod
    def verify_payload_mac(cls, payload: Dict[str, Any]) -> bool:
        """
        Verifies that a QR payload's 'mac' field matches a recomputed HMAC.
        Returns True if the payload is authentic (unmodified since generation),
        False if tampered or if the MAC is missing.
        """
        received_mac = payload.get("mac")
        if not received_mac:
            return False
        key = cls._get_hmac_key()
        expected_mac = cls._compute_payload_hmac(payload, key)
        return hmac.compare_digest(received_mac, expected_mac)

    @staticmethod
    def generate_qr_string(payload_dict: Dict[str, Any]) -> str:
        """Converts payload dictionary to base64-encoded verification string."""
        json_str = json.dumps(payload_dict, sort_keys=True)
        encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
        return f"FINAUDITPRO://VERIFY?data={encoded}"
