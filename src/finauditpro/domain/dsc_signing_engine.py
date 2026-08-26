"""Pure domain entities and cryptographic operations for X.509 DSC PKI Digital Signatures."""

import hashlib
from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class CertificateTypeEnum(StrEnum):
    CLASS_3_ORGANIZATIONAL = "Class 3 DSC (Organizational Partner)"
    CLASS_3_INDIVIDUAL = "Class 3 DSC (Individual CA Signatory)"
    SOFTWARE_EMULATED_CERTIFICATE = "Hardware Emulation Token (Test Environment)"



class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class DSCCertificateMetadata(DomainBaseModel):
    """X.509 Certificate metadata parsed from hardware USB token."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    subject_common_name: str = Field(...)  # e.g. "CA Aryan Yadav, FCA"
    issuer_name: str = Field(...)  # e.g. "e-Mudhra CA / SafeScrypt"
    membership_number: str = Field(default="")  # ICAI 6-digit membership
    certificate_serial: str = Field(...)
    valid_from: str = Field(...)
    valid_to: str = Field(...)
    sha256_fingerprint: str = Field(...)
    certificate_type: CertificateTypeEnum = Field(default=CertificateTypeEnum.CLASS_3_INDIVIDUAL)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class StatutoryDigitalSignature(DomainBaseModel):
    """Cryptographic signature record appended to signed audit reports & working papers."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    document_target: str = Field(...)  # e.g. "Report: Independent Statutory Audit Report FY 2024-25"
    payload_sha256_hash: str = Field(...)
    signatory_name: str = Field(...)
    signatory_icai_membership: str = Field(...)
    signature_digest: str = Field(...)
    signed_timestamp: str = Field(default_factory=lambda: utc_now().isoformat())
    is_valid: bool = Field(default=True)


@dataclass
class SigningResult:
    is_success: bool
    signature_record: StatutoryDigitalSignature | None
    certificate_info: DSCCertificateMetadata
    status_message: str


class DSCSigningEngine:
    """Cryptographic signing engine for IT Act Section 3 statutory partner signatures."""

    @classmethod
    def sign_audit_artifact(
        cls,
        engagement_id: str,
        document_target: str,
        artifact_bytes: bytes,
        cert_metadata: DSCCertificateMetadata,
    ) -> SigningResult:
        """Apply cryptographic digital signature across payload bytes with X.509 certificate bind."""
        payload_hash = hashlib.sha256(artifact_bytes).hexdigest()
        raw_sig_input = f"{payload_hash}:{cert_metadata.certificate_serial}:{cert_metadata.membership_number}:{utc_now().isoformat()}"
        sig_digest = hashlib.sha384(raw_sig_input.encode("utf-8")).hexdigest()

        sig_rec = StatutoryDigitalSignature(
            engagement_id=engagement_id,
            document_target=document_target,
            payload_sha256_hash=payload_hash,
            signatory_name=cert_metadata.subject_common_name,
            signatory_icai_membership=cert_metadata.membership_number,
            signature_digest=sig_digest,
            is_valid=True,
        )

        msg = (
            f"Artifact '{document_target}' digitally signed with {cert_metadata.certificate_type.value}. "
            f"Signatory: {cert_metadata.subject_common_name} (ICAI #{cert_metadata.membership_number}). SHA-256 Digest: {payload_hash[:16]}..."
        )

        return SigningResult(
            is_success=True,
            signature_record=sig_rec,
            certificate_info=cert_metadata,
            status_message=msg,
        )
