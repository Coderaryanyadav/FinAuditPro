"""Pure domain models representing versioned, configurable Indian audit standards and methodologies."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from finauditpro.domain.audit_matrix_entities import AssertionEnum


class StandardCategoryEnum(StrEnum):
    STANDARD_ON_AUDITING = "Standards on Auditing (SA)"
    COMPANIES_ACT_SCHEDULE_III = "Schedule III Financial Statement Framework"
    CARO_2020 = "Companies (Auditor's Report) Order 2020"
    TAXATION_GST = "GST Audit & Statutory Compliance"
    TAXATION_TDS = "Income Tax TDS / TCS Compliance"
    MCA_SECRETARIAL = "MCA & Secretarial Statutory Checks"
    RELATED_PARTIES_SEC188 = "Related Party Disclosures & Sec 188"
    STATUTORY_COMPLIANCE = "Statutory Dues & Labor Law Compliance"


@dataclass(frozen=True)
class MethodologyProcedureTemplate:
    """Configurable audit procedure linked to risk, assertion, evidence, and working paper."""

    procedure_code_prefix: str
    title: str
    objective: str
    procedure_type: str
    assertions: list[AssertionEnum]
    population_definition: str
    methodology_guidance: str
    expected_evidence: str
    working_paper_ref: str
    working_paper_title: str
    wp_sections: list[tuple[int, str, str]] = field(default_factory=list)
    review_checklist: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MethodologyRiskTemplate:
    """Risk template mapped to statutory requirement and assertion."""

    risk_code_prefix: str
    risk_title: str
    audit_area: str
    inherent_risk_level: str
    assertions: list[AssertionEnum]
    procedures: list[MethodologyProcedureTemplate] = field(default_factory=list)


@dataclass(frozen=True)
class StandardRequirement:
    """Specific statutory/auditing requirement within a standard."""

    requirement_code: str
    title: str
    description: str
    statutory_reference: str
    risks: list[MethodologyRiskTemplate] = field(default_factory=list)


@dataclass(frozen=True)
class StandardDefinition:
    """Top-level definition of an ICAI standard or statutory regulatory framework."""

    standard_code: str
    title: str
    category: StandardCategoryEnum
    authoritative_source: str
    effective_date: str
    requirements: list[StandardRequirement] = field(default_factory=list)


@dataclass(frozen=True)
class AuditMethodologyPackage:
    """Immutable, versioned bundle of auditing standards and statutory compliance checks."""

    version: str
    name: str
    release_date: str
    standards: list[StandardDefinition] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_standard(self, code: str) -> StandardDefinition | None:
        c_upper = code.strip().upper()
        for std in self.standards:
            if std.standard_code.strip().upper() == c_upper:
                return std
        return None

    def list_all_standards(self) -> list[StandardDefinition]:
        return list(self.standards)

    def list_by_category(self, category: StandardCategoryEnum) -> list[StandardDefinition]:
        return [s for s in self.standards if s.category == category]
