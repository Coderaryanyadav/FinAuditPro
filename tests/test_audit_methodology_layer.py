"""Comprehensive tests for the versioned, configurable Indian audit methodology layer and version isolation."""

import pytest

from finauditpro.application.methodology_dtos import ApplyMethodologyDTO
from finauditpro.application.services.methodology_service import MethodologyService
from finauditpro.domain.audit_matrix_entities import AssertionEnum
from finauditpro.domain.entities import Client, Engagement, Firm
from finauditpro.domain.exceptions import EntityNotFoundError
from finauditpro.domain.methodology_entities import (
    AuditMethodologyPackage,
    MethodologyProcedureTemplate,
    MethodologyRiskTemplate,
    StandardCategoryEnum,
    StandardDefinition,
    StandardRequirement,
)
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
)


@pytest.fixture
def db_manager(tmp_path):
    db_file = tmp_path / "test_methodology_audit.db"
    mgr = DatabaseManager(f"sqlite:///{db_file}")
    mgr.create_tables()
    return mgr


@pytest.fixture
def seeded_engagement(db_manager):
    with db_manager.session_scope() as session:
        firm = FirmRepository(session).add(Firm(name="Apex Audit LLP"))
        client = ClientRepository(session).add(
            Client(firm_id=firm.id, name="Bharati Global Ltd", pan="AABCB9999F")
        )
        eng = EngagementRepository(session).add(
            Engagement(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-2026",
                title="Statutory Audit FY 2025-26",
            )
        )
        return eng


class TestAuditMethodologyLayer:
    """Test suite verifying authoritative content, chain completeness, and version isolation."""

    def test_all_mandated_standards_on_auditing_present(self):
        """Verify all 19 required SAs are cataloged with authoritative metadata."""
        pkg = MethodologyService.get_methodology_package("2026.1.0")
        required_sas = [
            "SA 200", "SA 230", "SA 240", "SA 250", "SA 315", "SA 320", "SA 330",
            "SA 450", "SA 500", "SA 505", "SA 510", "SA 520", "SA 530", "SA 560",
            "SA 570", "SA 580", "SA 700", "SA 705", "SA 706",
        ]

        for sa_code in required_sas:
            std = pkg.get_standard(sa_code)
            assert std is not None, f"Standard {sa_code} missing from methodology catalog."
            assert std.category == StandardCategoryEnum.STANDARD_ON_AUDITING
            assert "ICAI" in std.authoritative_source
            assert len(std.requirements) >= 1
            for req in std.requirements:
                assert req.requirement_code.startswith("SA")
                assert len(req.risks) >= 1
                for rsk in req.risks:
                    assert len(rsk.assertions) >= 1
                    assert len(rsk.procedures) >= 1
                    for proc in rsk.procedures:
                        assert proc.procedure_code_prefix.startswith("PROC-SA")
                        assert proc.working_paper_ref.startswith("WP-SA")
                        assert len(proc.wp_sections) >= 1
                        assert len(proc.review_checklist) >= 1

    def test_all_mandated_statutory_frameworks_present(self):
        """Verify all 7 required Indian statutory frameworks are cataloged with authoritative citations."""
        pkg = MethodologyService.get_methodology_package("2026.1.0")
        required_statutory = [
            ("Schedule III", StandardCategoryEnum.COMPANIES_ACT_SCHEDULE_III),
            ("CARO 2020", StandardCategoryEnum.CARO_2020),
            ("GST Compliance", StandardCategoryEnum.TAXATION_GST),
            ("TDS Compliance", StandardCategoryEnum.TAXATION_TDS),
            ("MCA Checks", StandardCategoryEnum.MCA_SECRETARIAL),
            ("Related Parties Sec 188", StandardCategoryEnum.RELATED_PARTIES_SEC188),
            ("Statutory Compliance", StandardCategoryEnum.STATUTORY_COMPLIANCE),
        ]

        for code, category in required_statutory:
            std = pkg.get_standard(code)
            assert std is not None, f"Statutory framework {code} missing."
            assert std.category == category
            assert len(std.requirements) >= 1
            for req in std.requirements:
                assert len(req.risks) >= 1
                for rsk in req.risks:
                    assert len(rsk.procedures) >= 1
                    for proc in rsk.procedures:
                        assert len(proc.review_checklist) >= 1

    def test_complete_canonical_chain_traversal(self):
        """Verify Standard -> Requirement -> Risk -> Assertion -> Procedure -> Evidence -> Working Paper -> Review."""
        pkg = MethodologyService.get_methodology_package("2026.1.0")
        sa240 = pkg.get_standard("SA 240")
        assert sa240 is not None

        req = sa240.requirements[0]
        assert "SA240-R1" in req.requirement_code
        assert "Management Override" in req.title

        risk = req.risks[0]
        assert risk.risk_code_prefix == "RSK-SA240-OVERRIDE"
        assert AssertionEnum.OCCURRENCE in risk.assertions

        proc = risk.procedures[0]
        assert proc.procedure_code_prefix == "PROC-SA240-JRN"
        assert AssertionEnum.OCCURRENCE in proc.assertions
        assert "Benford's Law" in proc.methodology_guidance
        assert "Journal vouchers" in proc.expected_evidence
        assert proc.working_paper_ref == "WP-SA240-JOURNAL-OVERRIDE"
        assert len(proc.wp_sections) == 2
        assert len(proc.review_checklist) == 2

    def test_instantiate_methodology_in_engagement_database(self, db_manager, seeded_engagement):
        """Instantiating methodology must create interconnected risks, procedures, and working papers."""
        service = MethodologyService(db_manager)

        res = service.apply_methodology_to_engagement(
            ApplyMethodologyDTO(
                engagement_id=seeded_engagement.id,
                methodology_version="2026.1.0",
                standard_codes=["SA 240", "CARO 2020", "GST Compliance"],
                actor="Lead Partner",
            )
        )

        assert res.methodology_version == "2026.1.0"
        assert res.risks_created_count == 3
        assert res.procedures_created_count == 3
        assert res.working_papers_created_count == 3
        assert len(res.created_risk_ids) == 3
        assert len(res.created_procedure_ids) == 3
        assert len(res.created_wp_ids) == 3

    def test_methodology_version_isolation_and_immutability(self):
        """Adding new methodology versions must never alter or mutate historical methodology packages."""
        # 1. Inspect existing 2025 and 2026 versions
        pkg_2025 = MethodologyService.get_methodology_package("2025.1.0")
        pkg_2026 = MethodologyService.get_methodology_package("2026.1.0")
        assert pkg_2025.version == "2025.1.0"
        assert pkg_2026.version == "2026.1.0"

        # 2. Register a new future methodology package version (e.g. 2027.1.0)
        custom_proc = MethodologyProcedureTemplate(
            procedure_code_prefix="PROC-2027-NEW",
            title="Next Gen ESG and Climate Audit Verification",
            objective="Verify sustainability disclosures under BRSR Core framework.",
            procedure_type="Substantive ESG Audit",
            assertions=[AssertionEnum.PRESENTATION],
            population_definition="Annual Sustainability and BRSR Report.",
            methodology_guidance="100% verification of carbon footprint calculations.",
            expected_evidence="Third party carbon audit report.",
            working_paper_ref="WP-ESG-BRSR",
            working_paper_title="BRSR Core ESG Assurance Schedule",
            wp_sections=[(1, "1. Energy Metrics", "Verify Scope 1 and Scope 2 emissions.")],
            review_checklist=["Are carbon certificates validated?"],
        )
        custom_risk = MethodologyRiskTemplate(
            risk_code_prefix="RSK-ESG-GREENWASH",
            risk_title="Risk of Greenwashing & Misstated ESG Metrics",
            audit_area="Sustainability & ESG",
            inherent_risk_level="HIGH",
            assertions=[AssertionEnum.PRESENTATION],
            procedures=[custom_proc],
        )
        custom_req = StandardRequirement(
            requirement_code="ESG-REQ-01",
            title="BRSR Core Mandatory Assurance",
            description="Mandatory assurance for top 1000 listed entities under SEBI LODR.",
            statutory_reference="SEBI Circular SEBI/HO/CFD/CFD-SEC-2/P/CIR/2023/122",
            risks=[custom_risk],
        )
        custom_std = StandardDefinition(
            standard_code="BRSR Core",
            title="Business Responsibility and Sustainability Reporting (BRSR Core)",
            category=StandardCategoryEnum.STATUTORY_COMPLIANCE,
            authoritative_source="Securities and Exchange Board of India (SEBI)",
            effective_date="2026-04-01",
            requirements=[custom_req],
        )

        pkg_2027 = AuditMethodologyPackage(
            version="2027.1.0",
            name="SEBI BRSR Core & Next-Gen Statutory Framework (FY 2026-27)",
            release_date="2026-04-01",
            standards=[custom_std],
            metadata={"jurisdiction": "India", "regulatory_body": "SEBI"},
        )

        MethodologyService.register_methodology_package(pkg_2027)

        # 3. Invariant: 2027 is now available
        assert "2027.1.0" in MethodologyService.list_available_versions()
        retrieved_2027 = MethodologyService.get_methodology_package("2027.1.0")
        assert retrieved_2027.get_standard("BRSR Core") is not None

        # 4. Invariant: Historical 2025 and 2026 packages remain completely untouched
        retrieved_2025 = MethodologyService.get_methodology_package("2025.1.0")
        retrieved_2026 = MethodologyService.get_methodology_package("2026.1.0")
        assert retrieved_2025.get_standard("BRSR Core") is None
        assert retrieved_2026.get_standard("BRSR Core") is None
        assert len(retrieved_2025.standards) == 26  # 19 SAs + 7 Statutory
        assert len(retrieved_2026.standards) == 26

    def test_nonexistent_version_raises_entity_not_found(self):
        """Requesting an unregistered methodology package version must raise EntityNotFoundError."""
        with pytest.raises(EntityNotFoundError):
            MethodologyService.get_methodology_package("1999.1.0")
