from pydantic import BaseModel, ConfigDict
from typing import Optional


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_name: str
    file_path: str
    document_type: Optional[str] = None
    engagement_id: Optional[int] = None
    audit_id: Optional[int] = None
    is_vectorized: bool = False
