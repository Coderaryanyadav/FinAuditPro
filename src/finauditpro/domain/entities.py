"""Pure domain entities for FinAuditPro."""

import re
from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from finauditpro.domain.clock import utc_now
from finauditpro.domain.exceptions import ValidationError


class RoleEnum(StrEnum):
    PARTNER = "Partner"
    MANAGER = "Manager"
    SENIOR = "Senior"
    SENIOR_AUDITOR = "Senior"
    ASSOCIATE = "Associate"
    ADMINISTRATOR = "Administrator"


class AuditTypeEnum(StrEnum):
    STATUTORY_AUDIT = "Statutory Audit"
    TAX_AUDIT = "Tax Audit"
    GST_AUDIT = "GST Audit"
    INTERNAL_AUDIT = "Internal Audit"
    CONCURRENT_AUDIT = "Concurrent Audit"
    STOCK_AUDIT = "Stock Audit"


class EngagementStatusEnum(StrEnum):
    PLANNING = "Planning"
    DOCUMENT_COLLECTION = "Document Collection"
    FINANCIAL_ANALYSIS = "Financial Analysis"
    AUDIT_PROCEDURES = "Audit Procedures"
    REVIEW = "Review"
    COMPLETED = "Completed"
    FINALIZING = "Finalizing"
    ARCHIVED = "Archived"
    REOPENED = "Reopened"


class EntityTypeEnum(StrEnum):
    PVT_LTD = "Private Limited Company"
    PUBLIC_LTD = "Public Limited Company"
    LLP = "Limited Liability Partnership"
    PARTNERSHIP = "Partnership Firm"
    PROPRIETORSHIP = "Sole Proprietorship"
    TRUST = "Trust"
    SOCIETY = "Society"
    INDIVIDUAL = "Individual"


_PAN_REGEX = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$")
_GSTIN_REGEX = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def validate_pan(pan: str | None) -> str | None:
    if pan is None or not pan.strip():
        return None
    cleaned = pan.strip().upper()
    if not _PAN_REGEX.match(cleaned):
        raise ValidationError(
            f"Invalid PAN format: '{pan}'. Expected 10-character alphanumeric format (e.g. ABCDE1234F)."
        )
    return cleaned


def validate_gstin(gstin: str | None) -> str | None:
    if gstin is None or not gstin.strip():
        return None
    cleaned = gstin.strip().upper()
    if not _GSTIN_REGEX.match(cleaned):
        raise ValidationError(
            f"Invalid GSTIN format: '{gstin}'. Expected 15-character Indian GSTIN format."
        )
    return cleaned


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class Firm(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=255)
    registration_number: str | None = Field(default=None, max_length=100)
    pan: str | None = Field(default=None)
    gstin: str | None = Field(default=None)
    address: str | None = Field(default=None)
    phone: str | None = Field(default=None)
    email: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("name")
    @classmethod
    def check_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Firm name cannot be empty.")
        return v.strip()

    @field_validator("pan")
    @classmethod
    def check_pan(cls, v: str | None) -> str | None:
        return validate_pan(v)

    @field_validator("gstin")
    @classmethod
    def check_gstin(cls, v: str | None) -> str | None:
        return validate_gstin(v)


class Client(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    firm_id: str = Field(...)
    name: str = Field(..., min_length=1, max_length=255)
    entity_type: EntityTypeEnum = Field(default=EntityTypeEnum.PVT_LTD)
    pan: str | None = Field(default=None)
    gstin: str | None = Field(default=None)
    registered_address: str | None = Field(default=None)
    industry: str | None = Field(default=None)
    contact_person: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("name")
    @classmethod
    def check_name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Client name cannot be empty.")
        return v.strip()

    @field_validator("pan")
    @classmethod
    def check_pan(cls, v: str | None) -> str | None:
        return validate_pan(v)

    @field_validator("gstin")
    @classmethod
    def check_gstin(cls, v: str | None) -> str | None:
        return validate_gstin(v)


class Engagement(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    firm_id: str = Field(...)
    client_id: str = Field(...)
    financial_year: str = Field(..., min_length=4, max_length=10)
    audit_type: AuditTypeEnum = Field(default=AuditTypeEnum.STATUTORY_AUDIT)
    status: EngagementStatusEnum = Field(default=EngagementStatusEnum.PLANNING)
    prior_engagement_id: str | None = Field(default=None)
    assigned_team: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("financial_year")
    @classmethod
    def check_fy(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Financial Year cannot be empty.")
        return v.strip()


class AuditEvent(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str | None = Field(default=None)
    actor: str = Field(default="System")
    action: str = Field(...)
    details: str | None = Field(default=None)
    previous_hash: str | None = Field(default=None)
    entry_hash: str | None = Field(default=None)
    timestamp: datetime = Field(default_factory=utc_now)


class User(DomainBaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    username: str = Field(..., min_length=1, max_length=255)
    password_hash: str = Field(...)
    salt: str = Field(...)
    role: RoleEnum = Field(default=RoleEnum.ASSOCIATE)
    is_active: bool = Field(default=True)
    must_change_password: bool = Field(default=False)
    totp_secret: str | None = Field(default=None)
    is_totp_enabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("username")
    @classmethod
    def check_username(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValidationError("Username cannot be empty.")
        return v.strip().lower()
