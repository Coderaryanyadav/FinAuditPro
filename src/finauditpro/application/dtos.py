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
    partner: str | None = None
    manager: str | None = None
    assigned_team: list[str] = Field(default_factory=list)
    start_date: str | None = None
    reporting_date: str | None = None


class UpdateEngagementDTO(BaseModel):
    financial_year: str | None = None
    audit_type: AuditTypeEnum | None = None
    status: EngagementStatusEnum | None = None
    partner: str | None = None
    manager: str | None = None
    assigned_team: list[str] | None = None
    start_date: str | None = None
    reporting_date: str | None = None


class EngagementDashboardDTO(BaseModel):
    engagement_id: str
    client_id: str
    client_name: str
    firm_id: str
    firm_name: str
    financial_year: str
    engagement_type: str
    status: str
    partner: str | None = None
    manager: str | None = None
    team: list[str] = Field(default_factory=list)
    start_date: str | None = None
    reporting_date: str | None = None
    version: int = 1
    completion_percentage: float = 0.0
    open_working_papers: int = 0
    total_working_papers: int = 0
    open_review_notes: int = 0
    addressed_review_notes: int = 0
    cleared_review_notes: int = 0
    outstanding_pbc: int = 0
    unresolved_findings: int = 0
    high_risk_areas: list[str] = Field(default_factory=list)
    materiality_overall_paise: int = 0
    materiality_performance_paise: int = 0
    materiality_trivial_paise: int = 0
    financial_data_status: str = "Not Imported"
    tb_balanced: bool = False
    finalisation_status: str = "In Progress"
    is_locked: bool = False


class DashboardSummaryDTO(BaseModel):
    firm_id: str | None = None
    firm_name: str | None = None
    total_clients: int = 0
    active_engagements: int = 0
    completed_engagements: int = 0
    pending_documents: int = 0
    open_findings: int = 0
    recent_activities: list[dict[str, str]] = Field(default_factory=list)
    active_engagement_dashboard: EngagementDashboardDTO | None = None
