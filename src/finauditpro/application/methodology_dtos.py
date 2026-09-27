"""Data transfer objects for audit methodology configuration, versioning, and matrix instantiation."""

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApplyMethodologyDTO(BaseModel):
    """DTO for applying a specific version of audit methodology to an engagement."""

    model_config = ConfigDict(frozen=False)

    engagement_id: str = Field(..., min_length=1)
    methodology_version: str | None = Field(
        default=None, description="Target version to lock onto engagement (e.g. '2025.1.0')"
    )
    standard_codes: list[str] | None = Field(
        default=None, description="Optional list of standard codes to instantiate. If None, instantiates all."
    )
    actor: str = Field(default="Lead Engagement Partner")


@dataclass(frozen=True)
class StandardSummaryDTO:
    standard_code: str
    title: str
    category: str
    requirements_count: int
    risks_count: int
    procedures_count: int


@dataclass(frozen=True)
class MethodologyVersionSummaryDTO:
    version: str
    name: str
    release_date: str
    standards_count: int
    standards: list[StandardSummaryDTO]


@dataclass(frozen=True)
class MethodologyInstantiationResultDTO:
    engagement_id: str
    methodology_version: str
    risks_created_count: int
    procedures_created_count: int
    working_papers_created_count: int
    created_risk_ids: list[str] = field(default_factory=list)
    created_procedure_ids: list[str] = field(default_factory=list)
    created_wp_ids: list[str] = field(default_factory=list)
