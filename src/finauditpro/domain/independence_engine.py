"""Pure domain entities and conflict verification rules for SQM 1 / SQC 1 Independence & Conflict Registry."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from finauditpro.domain.clock import utc_now


class IndependenceThreatTypeEnum(StrEnum):
    NONE = "Clean - No Independence Impairment"
    FINANCIAL_INTEREST_EXCEEDS_LIMIT = "Direct Holding Exceeds Statutory Limit (>₹2,00,000 Face Value)"
    SECTION_144_PROHIBITED_SERVICE = "Prohibited Non-Audit Service under Section 144 of CA 2013"
    RELATIONSHIP_WITH_DIRECTOR_KMP = "Close Relative Holds Directorship / Key Position"
    INDEBTEDNESS_OR_GUARANTEE = "Indebtedness / Loan Guarantee Given to Audit Client"


class DomainBaseModel(BaseModel):
    model_config = ConfigDict(frozen=False, arbitrary_types_allowed=True)


class IndependenceDeclaration(DomainBaseModel):
    """Annual and engagement-specific independence declaration by partner/staff."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    firm_id: str = Field(...)
    engagement_id: str = Field(...)
    user_id: str = Field(...)
    user_name: str = Field(...)
    role: str = Field(...)
    financial_year: str = Field(...)
    holding_face_value_paise: int = Field(default=0, ge=0)
    has_prohibited_non_audit_services: bool = Field(default=False)
    has_relative_in_kmp: bool = Field(default=False)
    is_indebted_to_client: bool = Field(default=False)
    is_independent: bool = Field(default=True)
    threat_type: IndependenceThreatTypeEnum = Field(default=IndependenceThreatTypeEnum.NONE)
    mitigation_or_remark: str = Field(default="")
    declared_at: str = Field(default_factory=lambda: utc_now().isoformat())


@dataclass
class IndependenceEvaluationSummary:
    total_declarations: int
    clean_count: int
    impaired_count: int
    declarations: list[IndependenceDeclaration]
    firm_compliance_status: str


class IndependenceConflictEngine:
    """Evaluation engine for firm-wide independence and Section 144 non-audit service prohibitions."""

    STATUTORY_HOLDING_LIMIT_PAISE = 20000000  # ₹2,00,000.00 face value threshold under Section 141(3)(d)

    @classmethod
    def evaluate_team_independence(
        cls,
        firm_id: str,
        engagement_id: str,
        declarations: list[dict[str, Any]],
    ) -> IndependenceEvaluationSummary:
        """Evaluate staff and partner independence declarations against Section 141 and SQC 1."""
        records = []
        impaired = 0
        clean = 0

        for d in declarations:
            u_id = d.get("user_id", "")
            u_name = d.get("user_name", "Team Member")
            role = d.get("role", "Auditor")
            fy = d.get("financial_year", "2024-25")
            holding = int(d.get("holding_face_value_paise", d.get("holding_amount", 0) * 100))
            non_audit = d.get("has_prohibited_non_audit_services", False)
            rel_kmp = d.get("has_relative_in_kmp", False)
            indebted = d.get("is_indebted_to_client", False)

            threat = IndependenceThreatTypeEnum.NONE
            remark = "Independence verified without exceptions."
            is_ind = True

            if non_audit:
                threat = IndependenceThreatTypeEnum.SECTION_144_PROHIBITED_SERVICE
                remark = "Team/Firm provides prohibited non-audit services (accounting, internal audit, investment advisory) under Sec 144."
                is_ind = False
                impaired += 1
            elif holding > cls.STATUTORY_HOLDING_LIMIT_PAISE:
                threat = IndependenceThreatTypeEnum.FINANCIAL_INTEREST_EXCEEDS_LIMIT
                remark = f"Holding of ₹{holding/100:,.2f} exceeds statutory ₹2,00,000 threshold under Section 141(3)(d)."
                is_ind = False
                impaired += 1
            elif rel_kmp:
                threat = IndependenceThreatTypeEnum.RELATIONSHIP_WITH_DIRECTOR_KMP
                remark = "Close relative is Director / KMP in client entity. Disqualification under Section 141(3)(f)."
                is_ind = False
                impaired += 1
            elif indebted:
                threat = IndependenceThreatTypeEnum.INDEBTEDNESS_OR_GUARANTEE
                remark = "Auditor indebted to client exceeding statutory limits. Disqualification under Section 141(3)(d)(ii)."
                is_ind = False
                impaired += 1
            else:
                clean += 1

            records.append(
                IndependenceDeclaration(
                    firm_id=firm_id,
                    engagement_id=engagement_id,
                    user_id=u_id,
                    user_name=u_name,
                    role=role,
                    financial_year=fy,
                    holding_face_value_paise=holding,
                    has_prohibited_non_audit_services=non_audit,
                    has_relative_in_kmp=rel_kmp,
                    is_indebted_to_client=indebted,
                    is_independent=is_ind,
                    threat_type=threat,
                    mitigation_or_remark=remark,
                )
            )

        status_msg = "COMPLIANT" if impaired == 0 else f"IMPAIRED ({impaired} team members disqualified)"

        return IndependenceEvaluationSummary(
            total_declarations=len(declarations),
            clean_count=clean,
            impaired_count=impaired,
            declarations=records,
            firm_compliance_status=status_msg,
        )
