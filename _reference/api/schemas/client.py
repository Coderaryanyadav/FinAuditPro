from pydantic import BaseModel, ConfigDict
from typing import Optional, List


class ClientCreate(BaseModel):
    name: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    cin: Optional[str] = None
    industry_id: Optional[int] = None
    industry_name: Optional[str] = None
    registered_address: Optional[str] = None


class ClientUpdate(BaseModel):
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    industry: Optional[str] = None


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    cin: Optional[str] = None
    registered_address: Optional[str] = None
