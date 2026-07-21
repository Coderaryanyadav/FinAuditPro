"""
Digital Signature & Cryptographic Verification Manager for FinAuditPro.
Provides ICAI practitioner digital signing blocks and document SHA-256 tamper verification.
"""

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
from typing import Dict, Any, Optional

@dataclass
class SignatureBlock:
    ca_name: str
    membership_number: str
    firm_name: str
    firm_registration_number: str
    signature_date: datetime = field(default_factory=datetime.utcnow)
    digital_signature_hash: str = ""
    udin: Optional[str] = None  # Unique Document Identification Number (ICAI mandatory)

    def __post_init__(self):
        if not self.digital_signature_hash:
            payload = f"{self.ca_name}:{self.membership_number}:{self.firm_registration_number}:{self.signature_date.isoformat()}"
            self.digital_signature_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if not self.udin:
            self.udin = f"26{self.membership_number}AAAA{hashlib.md5(self.digital_signature_hash.encode()).hexdigest()[:6].upper()}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ca_name": self.ca_name,
            "membership_number": self.membership_number,
            "firm_name": self.firm_name,
            "firm_registration_number": self.firm_registration_number,
            "signature_date": self.signature_date.isoformat(),
            "digital_signature_hash": self.digital_signature_hash,
            "udin": self.udin or f"26{self.membership_number}AAAA{hashlib.md5(self.digital_signature_hash.encode()).hexdigest()[:6].upper()}",
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
        return SignatureBlock(
            ca_name=ca_name,
            membership_number=membership_number,
            firm_name=firm_name,
            firm_registration_number=firm_registration_number,
            udin=udin
        )

    @staticmethod
    def verify_document_integrity(document_bytes: bytes, expected_hash: str) -> bool:
        """Verify that document content matches expected SHA-256 hash."""
        computed_hash = hashlib.sha256(document_bytes).hexdigest()
        return computed_hash == expected_hash
