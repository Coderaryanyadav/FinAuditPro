"""Application service orchestrating versioned, configurable Indian audit methodologies and matrix instantiation."""

import copy
from typing import Any
from uuid import uuid4

from finauditpro.application.audit_matrix_dtos import (
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.methodology_dtos import (
    ApplyMethodologyDTO,
    MethodologyInstantiationResultDTO,
    MethodologyVersionSummaryDTO,
    StandardSummaryDTO,
)
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.domain.audit_matrix_entities import RiskSeverityEnum
from finauditpro.domain.entities import AuditEvent
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.domain.methodology_catalog import get_sa_standards_catalog
from finauditpro.domain.methodology_entities import (
    AuditMethodologyPackage,
    StandardDefinition,
)
from finauditpro.domain.methodology_statutory_catalog import get_statutory_standards_catalog
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    AuditEventRepository,
    EngagementRepository,
)


def _build_default_2025_package() -> AuditMethodologyPackage:
    all_stds = get_sa_standards_catalog() + get_statutory_standards_catalog()
    return AuditMethodologyPackage(
        version="2025.1.0",
        name="ICAI Standards on Auditing & Statutory Compliance Framework (FY 2024-25)",
        release_date="2024-04-01",
        standards=all_stds,
        metadata={"jurisdiction": "India", "regulatory_body": "ICAI / MCA / CBIC / CBDT"},
    )


def _build_default_2026_package() -> AuditMethodologyPackage:
    all_stds = get_sa_standards_catalog() + get_statutory_standards_catalog()
    return AuditMethodologyPackage(
        version="2026.1.0",
        name="ICAI Standards on Auditing & Statutory Compliance Framework (FY 2025-26)",
        release_date="2025-04-01",
        standards=all_stds,
        metadata={"jurisdiction": "India", "regulatory_body": "ICAI / MCA / CBIC / CBDT"},
    )


class MethodologyService:
    """Service managing versioned auditing methodology packages and engagement matrix instantiation."""

    _registry: dict[str, AuditMethodologyPackage] = {
        "2025.1.0": _build_default_2025_package(),
        "2026.1.0": _build_default_2026_package(),
    }

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    @classmethod
    def register_methodology_package(cls, package: AuditMethodologyPackage) -> None:
        """Register a new immutable methodology package version without mutating existing versions."""
        cls._registry[package.version] = package

    @classmethod
    def get_methodology_package(cls, version: str) -> AuditMethodologyPackage:
        if version not in cls._registry:
            raise EntityNotFoundError("Audit Methodology Package Version", version)
        return copy.deepcopy(cls._registry[version])

    @classmethod
    def list_available_versions(cls) -> list[str]:
        return sorted(list(cls._registry.keys()), reverse=True)

    @classmethod
    def get_version_summary(cls, version: str) -> MethodologyVersionSummaryDTO:
        pkg = cls.get_methodology_package(version)
        std_summaries = []
        for s in pkg.standards:
            req_cnt = len(s.requirements)
            rsk_cnt = sum(len(r.risks) for r in s.requirements)
            proc_cnt = sum(len(r.procedures) for req in s.requirements for r in req.risks)
            std_summaries.append(
                StandardSummaryDTO(
                    standard_code=s.standard_code,
                    title=s.title,
                    category=s.category.value,
                    requirements_count=req_cnt,
                    risks_count=rsk_cnt,
                    procedures_count=proc_cnt,
                )
            )
        return MethodologyVersionSummaryDTO(
            version=pkg.version,
            name=pkg.name,
            release_date=pkg.release_date,
            standards_count=len(pkg.standards),
            standards=std_summaries,
        )

    def apply_methodology_to_engagement(
        self, dto: ApplyMethodologyDTO
    ) -> MethodologyInstantiationResultDTO:
        """Instantiate Standard -> Requirement -> Risk -> Assertion -> Procedure -> Working Paper chain."""
        with self.db_manager.session_scope() as session:
            eng = EngagementRepository(session).get_by_id(dto.engagement_id)
            if not eng:
                raise EntityNotFoundError("Engagement", dto.engagement_id)

        target_version = dto.methodology_version or "2026.1.0"
        pkg = self.get_methodology_package(target_version)

        selected_standards: list[StandardDefinition] = []
        if dto.standard_codes:
            filter_codes = {c.strip().upper() for c in dto.standard_codes}
            selected_standards = [
                s for s in pkg.standards if s.standard_code.strip().upper() in filter_codes
            ]
        else:
            selected_standards = list(pkg.standards)

        matrix_service = AuditMatrixService(self.db_manager)
        wp_service = WorkingPaperService(self.db_manager)

        created_risk_ids: list[str] = []
        created_proc_ids: list[str] = []
        created_wp_ids: list[str] = []

        for std in selected_standards:
            for req in std.requirements:
                for rsk_tmpl in req.risks:
                    # 1. Create Risk
                    sev = (
                        RiskSeverityEnum.HIGH
                        if rsk_tmpl.inherent_risk_level.upper() in ("HIGH", "CRITICAL")
                        else RiskSeverityEnum.MEDIUM
                    )
                    risk_code = f"{rsk_tmpl.risk_code_prefix}-{uuid4().hex[:4].upper()}"
                    risk_entity = matrix_service.create_risk(
                        CreateRiskDTO(
                            engagement_id=dto.engagement_id,
                            risk_code=risk_code,
                            category=rsk_tmpl.audit_area,
                            title=f"[{std.standard_code}] {rsk_tmpl.risk_title}",
                            description=f"Requirement: {req.title}\n{req.description}\nStandard: {std.title} ({req.statutory_reference})",
                            inherent_risk=sev,
                            control_risk=RiskSeverityEnum.MEDIUM,
                            severity=sev,
                        )
                    )
                    created_risk_ids.append(risk_entity.id)

                    for proc_tmpl in rsk_tmpl.procedures:
                        # 2. Create Procedure
                        proc_code = f"{proc_tmpl.procedure_code_prefix}-{uuid4().hex[:4].upper()}"
                        proc_entity = matrix_service.create_procedure(
                            CreateProcedureDTO(
                                engagement_id=dto.engagement_id,
                                risk_id=risk_entity.id,
                                procedure_code=proc_code,
                                objective=proc_tmpl.objective,
                                procedure_type=proc_tmpl.procedure_type,
                                evidence_requirement=proc_tmpl.expected_evidence,
                                account_area=rsk_tmpl.audit_area,
                                population=proc_tmpl.population_definition,
                                methodology=f"{proc_tmpl.methodology_guidance} (Version: {pkg.version})",
                                assertion=proc_tmpl.assertions[0] if proc_tmpl.assertions else None,
                            )
                        )
                        created_proc_ids.append(proc_entity.id)

                        # 3. Create Working Paper
                        wp_idx = f"{proc_tmpl.working_paper_ref}-{uuid4().hex[:4].upper()}"
                        wp_entity = wp_service.create_working_paper(
                            CreateWorkingPaperDTO(
                                engagement_id=dto.engagement_id,
                                index_reference=wp_idx,
                                title=f"[{std.standard_code}] {proc_tmpl.working_paper_title}",
                                area=rsk_tmpl.audit_area,
                                preparer_id=dto.actor,
                                procedure_ids=[proc_entity.id],
                            )
                        )
                        created_wp_ids.append(wp_entity.id)
                        wp_service.add_link(wp_entity.id, "PROCEDURE", proc_entity.id)
                        wp_service.add_link(wp_entity.id, "RISK", risk_entity.id)

        with self.db_manager.session_scope() as session:
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=dto.engagement_id,
                    actor=dto.actor,
                    action="Audit Methodology Instantiated",
                    details=f"Instantiated methodology version '{pkg.version}' ({len(selected_standards)} standards). Generated {len(created_risk_ids)} risks, {len(created_proc_ids)} procedures, and {len(created_wp_ids)} working papers.",
                )
            )

        return MethodologyInstantiationResultDTO(
            engagement_id=dto.engagement_id,
            methodology_version=pkg.version,
            risks_created_count=len(created_risk_ids),
            procedures_created_count=len(created_proc_ids),
            working_papers_created_count=len(created_wp_ids),
            created_risk_ids=created_risk_ids,
            created_procedure_ids=created_proc_ids,
            created_wp_ids=created_wp_ids,
        )
