"""Pure domain models, DTOs, and context formatters for Unified Search."""

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class SearchResultGroupEnum(StrEnum):
    CLIENTS = "CLIENTS"
    DOCUMENTS = "DOCUMENTS"
    WORK = "WORK"
    AUDIT = "AUDIT"
    FINANCIAL = "FINANCIAL"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class SearchScopeContext(DomainBaseModel):
    """Context holding user authentication and authorization boundary limits."""
    user_id: str | None = None
    firm_id: str | None = None
    allowed_client_ids: set[str] | None = None
    allowed_engagement_ids: set[str] | None = None


class SearchResultDTO(DomainBaseModel):
    """Unified Search result item with rich contextual metadata."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    entity_type: str = Field(..., min_length=1)  # CLIENT, ENGAGEMENT, DOCUMENT, WORKING_PAPER, TASK, FINDING, REQUEST, TRANSACTION
    group: SearchResultGroupEnum = Field(...)
    title: str = Field(..., min_length=1)
    subtitle: str = Field(default="")
    context_text: str = Field(..., min_length=1)  # e.g., "ABC Enterprises | March Bank Statement | FY 2025-26 | Documents"
    client_name: str | None = None
    client_id: str | None = None
    engagement_id: str | None = None
    route_key: str = Field(default="dashboard")
    payload: dict[str, Any] = Field(default_factory=dict)


def format_search_context(
    client_name: str | None,
    item_title: str,
    financial_year: str | None,
    category: str
) -> str:
    """Format unified context display string: Client Name | Title | FY 2025-26 | Category."""
    parts: list[str] = []
    if client_name and client_name.strip():
        parts.append(client_name.strip())
    parts.append(item_title.strip())
    if financial_year and financial_year.strip():
        fy_str = financial_year.strip()
        if not fy_str.startswith("FY"):
            fy_str = f"FY {fy_str}"
        parts.append(fy_str)
    if category and category.strip():
        parts.append(category.strip())
    return " | ".join(parts)
