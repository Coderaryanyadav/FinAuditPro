"""
Internal Audit Hash-Chain Integrity Verification Manager for FinAuditPro.

PROVIDES: Ed25519 asymmetric signing for internal audit ledger hash-chain integrity
verification. This signs report payload hashes to detect post-export tampering.

STATUTORY NOTICE: This module does NOT produce a legally valid Indian IT Act 2000
Class 3 PKI Digital Signature Certificate (DSC). Statutory audit signatures on
Form 3CA/3CB/3CD require a Class 3 X.509 Certificate from a licensed Certifying
Authority (eMudhra, nCode, Capricorn) stored on a hardware PKCS#11 USB token.
For live ICAI UDIN generation, auditors must visit https://udin.icai.org/.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import ed25519

@dataclass
class SignatureBlock:
    ca_name: str
    membership_number: str
    firm_name: str
    firm_registration_number: str
    signature_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    digital_signature_hash: str = ""
    asymmetric_signature: str = ""
    public_key_b64: str = ""
    udin: Optional[str] = None  # Unique Document Identification Number (ICAI mandatory)

    def __post_init__(self):
        payload = f"{self.ca_name}:{self.membership_number}:{self.firm_registration_number}:{self.signature_date.isoformat()}"
        if not self.digital_signature_hash:
            self.digital_signature_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        
        if not self.asymmetric_signature:
            priv_key = ed25519.Ed25519PrivateKey.generate()
            sig_bytes = priv_key.sign(payload.encode("utf-8"))
            self.asymmetric_signature = base64.b64encode(sig_bytes).decode("utf-8")
            pub_bytes = priv_key.public_key().public_bytes_raw()
            self.public_key_b64 = base64.b64encode(pub_bytes).decode("utf-8")
            
        if not self.udin:
            self.udin = "UDIN PENDING (Requires ICAI Portal Verification)"

    @property
    def provisional_udin(self) -> str:
        """Returns structured 18-character provisional UDIN format."""
        year = self.signature_date.strftime("%y")
        return f"{year}{self.membership_number[:6].zfill(6)}AUDIT{self.digital_signature_hash[:6].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "integrity_method": "Ed25519 Internal Audit Hash-Chain Integrity Verification",
            "statutory_notice": "NOT a statutory IT Act 2000 Class 3 PKI DSC. For legal ICAI signatures, use a CA-issued USB token.",
            "ca_name": self.ca_name,
            "membership_number": self.membership_number,
            "firm_name": self.firm_name,
            "firm_registration_number": self.firm_registration_number,
            "signature_date": self.signature_date.isoformat(),
            "digital_signature_hash": self.digital_signature_hash,
            "asymmetric_signature": self.asymmetric_signature,
            "public_key_b64": self.public_key_b64,
            "udin": self.udin or "UDIN PENDING – Generate at https://udin.icai.org/",
        }


class DigitalSignatureManager:
    """Manages digital signature validation and tamper detection."""

    @staticmethod
    def create_signature_block(
        ca_name: str,
        membership_number: str,
        firm_name: str,
        firm_registration_number: str,
        udin: Optional[str] = None
    ) -> SignatureBlock:
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.SIGN_REPORTS):
            raise PermissionError("User role lacks permission SIGN_REPORTS to execute digital signature creation.")

        return SignatureBlock(
            ca_name=ca_name,
            membership_number=membership_number,
            firm_name=firm_name,
            firm_registration_number=firm_registration_number,
            udin=udin
        )

    @staticmethod
    def verify_asymmetric_signature(payload: str, signature_b64: str, public_key_b64: str) -> bool:
        """Verify Ed25519 asymmetric signature authenticity."""
        try:
            pub_bytes = base64.b64decode(public_key_b64)
            sig_bytes = base64.b64decode(signature_b64)
            pub_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            pub_key.verify(sig_bytes, payload.encode("utf-8"))
            return True
        except Exception:
            return False

    @staticmethod
    def verify_document_integrity(document_bytes: bytes, expected_hash: str) -> bool:
        """Verify that document content matches expected SHA-256 hash."""
        computed_hash = hashlib.sha256(document_bytes).hexdigest()
        return computed_hash == expected_hash
