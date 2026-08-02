from pydantic import BaseModel, ConfigDict
from typing import Optional


class IndexCreate(BaseModel):
    engagement_id: int
    section_code: str
    section_name: str


class WorkingPaperCreate(BaseModel):
    index_id: int
    title: str
    prepared_by_id: int


class StatusUpdate(BaseModel):
    status: str


class WorkingPaperRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    index_id: Optional[int] = None
    title: Optional[str] = None
    status: Optional[str] = None
    observation: Optional[str] = None
    evidence: Optional[str] = None
