from pydantic import BaseModel, ConfigDict
from typing import Optional


class AuditProjectCreate(BaseModel):
    client_id: int
    financial_year: str = "2025-26"
    status: str = "Planning"
    risk_level: str = "Medium"


class AuditProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    financial_year: Optional[str] = None
    status: Optional[str] = None
    risk_level: Optional[str] = None
