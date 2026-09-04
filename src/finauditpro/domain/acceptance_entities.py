"""Domain entities and communication workflows for SA 510 Predecessor Auditor NOC communications."""

from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class CommunicationModeEnum(StrEnum):
    REGISTERED_POST_AD = "Registered Post with A/D"
    SPEED_POST_TRACKED = "Speed Post (Tracked Delivery)"
    OFFICIAL_EMAIL = "Official Email (Registered Domain)"
    HAND_DELIVERY = "Hand Delivery with Acknowledgment"


class NOCStatusEnum(StrEnum):
    PENDING_DISPATCH = "Pending Dispatch"
    DISPATCHED_AWAITING_REPLY = "Dispatched - Awaiting Response"
    NOC_RECEIVED_NO_OBJECTION = "NOC Received - No Objections"
    OBJECTIONS_RAISED = "Objections Raised / Outstanding Dues"
    DEEMED_COMPLIANCE = "Deemed Compliance (15 Days Elapsed)"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class PredecessorCommunication(DomainBaseModel):
    """SA 510 & ICAI Code of Ethics (Clause 8, Part I, First Schedule) Predecessor Auditor communication log."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    predecessor_firm_name: str = Field(..., min_length=1)
    predecessor_partner_name: str = Field(default="")
    predecessor_email: str = Field(default="")
    predecessor_address: str = Field(default="")
    communication_mode: CommunicationModeEnum = Field(
        default=CommunicationModeEnum.REGISTERED_POST_AD
    )
    dispatch_date: str = Field(default="")
    tracking_reference: str = Field(default="")
    status: NOCStatusEnum = Field(default=NOCStatusEnum.PENDING_DISPATCH)
    response_received_date: str | None = Field(default=None)
    objection_details: str | None = Field(default=None)
    statutory_dues_cleared_by_client: bool = Field(default=True)
    documented_by: str = Field(default="Partner")
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


class SA210EngagementLetter(DomainBaseModel):
    """SA 210 Agreeing the Terms of Audit Engagements structured letter entity."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str = Field(...)
    client_name: str = Field(...)
    financial_year: str = Field(...)
    scope_of_audit: str = Field(
        default="Statutory Audit under Section 139 & 143 of Companies Act, 2013"
    )
    management_responsibilities: str = Field(
        default="Preparation and fair presentation of financial statements, internal financial controls, and unrestricted access to records."
    )
    auditor_responsibilities: str = Field(
        default="Expressing an independent opinion on financial statements in accordance with Standards on Auditing (SAs) issued by ICAI."
    )
    agreed_fee_paise: int = Field(default=0)
    is_signed_by_management: bool = Field(default=False)
    management_signatory_name: str = Field(default="")
    signed_date: str | None = Field(default=None)
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())
