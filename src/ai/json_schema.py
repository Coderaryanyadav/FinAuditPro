from typing import List, Optional
from pydantic import BaseModel, Field

class AuditFindingSchema(BaseModel):
    """Strict schema for the AI to follow for all audit analysis."""
    summary: str = Field(description="Brief executive summary of the document or analysis.")
    risk_score: int = Field(ge=0, le=100, description="Calculated risk score from 0 to 100.")
    severity: str = Field(description="Must be High, Medium, or Low.")
    confidence: int = Field(ge=0, le=100, description="AI confidence score from 0 to 100.")
    accounting_standard: str = Field(description="Applicable accounting standard (e.g. SA 240).")
    evidence: List[str] = Field(description="List of specific evidence points extracted.")
    findings: List[str] = Field(description="List of identified anomalies or audit findings.")
    recommendations: List[str] = Field(description="List of recommended auditor actions.")
    working_paper_reference: str = Field(description="Suggested WP reference code.")
    next_audit_procedure: str = Field(description="The next logical audit procedure to perform.")
    citations: List[str] = Field(description="References to the source chunks used.")
    tokens_used: int = Field(default=0)
    processing_time: float = Field(default=0.0)
