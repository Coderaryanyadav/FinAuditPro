"""Data Transfer Objects (DTOs) for application services."""

from pydantic import BaseModel, Field

from finauditpro.domain.entities import AuditTypeEnum, EngagementStatusEnum, EntityTypeEnum


class CreateFirmDTO(BaseModel):
    name: str = Field(..., min_length=1)
    registration_number: str | None = None
    pan: str | None = None
    gstin: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class UpdateFirmDTO(BaseModel):
    name: str | None = None
    registration_number: str | None = None
    pan: str | None = None
    gstin: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class CreateClientDTO(BaseModel):
    firm_id: str = Field(...)
    name: str = Field(..., min_length=1)
    entity_type: EntityTypeEnum = EntityTypeEnum.PVT_LTD
    pan: str | None = None
    gstin: str | None = None
    registered_address: str | None = None
    industry: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None


class UpdateClientDTO(BaseModel):
    name: str | None = None
    entity_type: EntityTypeEnum | None = None
    pan: str | None = None
    gstin: str | None = None
    registered_address: str | None = None
    industry: str | None = None
    contact_person: str | None = None
    contact_email: str | None = None


class CreateEngagementDTO(BaseModel):
    firm_id: str = Field(...)
    client_id: str = Field(...)
    financial_year: str = Field(..., min_length=4)
    audit_type: AuditTypeEnum = AuditTypeEnum.STATUTORY_AUDIT
    status: EngagementStatusEnum = EngagementStatusEnum.PLANNING
    assigned_team: list[str] = Field(default_factory=list)


class UpdateEngagementDTO(BaseModel):
    financial_year: str | None = None
    audit_type: AuditTypeEnum | None = None
    status: EngagementStatusEnum | None = None
    assigned_team: list[str] | None = None


class DashboardSummaryDTO(BaseModel):
    firm_id: str | None = None
    firm_name: str | None = None
    total_clients: int = 0
    active_engagements: int = 0
    completed_engagements: int = 0
    pending_documents: int = 0
    open_findings: int = 0
    recent_activities: list[dict[str, str]] = Field(default_factory=list)
