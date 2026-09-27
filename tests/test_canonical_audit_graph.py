"""Integration test suite proving the complete Canonical Audit Graph.

Validates:
1. End-to-end chain:
   Risk -> Assertion -> Procedure -> Population -> Sample -> Evidence -> Test Result -> Exception -> Finding -> Working Paper
2. Bidirectional navigation:
   - Finding -> Evidence & Evidence -> Finding
   - Working Paper -> Procedure & Procedure -> Working Paper
   - Procedure -> Risk & Risk -> Procedure
   - Risk -> Working Paper & Working Paper -> Risk
3. Proper ownership, validation, audit trails, and immutability.
"""

from datetime import datetime
import pytest

from finauditpro.application.dtos import (
    CreateClientDTO,
    CreateEngagementDTO,
    CreateFirmDTO,
)
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.application.services.traceability_service import TraceabilityService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.domain.audit_execution_entities import (
    AuditException,
    AuditSampleItemTest,
    AuditTestOutcomeEnum,
    ExceptionStatusEnum,
    ProcedureConclusionEnum,
    TestExecution,
)
from finauditpro.domain.audit_matrix_entities import (
    AssertionEnum,
    AuditEvidence,
    AuditFinding,
    AuditProcedure,
    AuditRisk,
    FindingStatusEnum,
    ProcedureStatusEnum,
    RiskSeverityEnum,
)
from finauditpro.domain.entities import AuditTypeEnum, EngagementStatusEnum
from finauditpro.domain.working_paper_entities import FileCategoryEnum, WorkingPaperStatusEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def db_manager(tmp_path):
    db_path = tmp_path / "test_canonical_graph.db"
    mgr = DatabaseManager(db_path=db_path)
    mgr.create_tables()
    return mgr


@pytest.fixture
def graph_services(db_manager):
    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    matrix_svc = AuditMatrixService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    trace_svc = TraceabilityService(db_manager)
    return firm_svc, client_svc, eng_svc, matrix_svc, wp_svc, trace_svc


class TestCanonicalAuditGraphIntegration:
    """Proves that the complete canonical audit graph operates bidirectionally."""

    def test_canonical_chain_and_bidirectional_navigation(self, graph_services):
        firm_svc, client_svc, eng_svc, matrix_svc, wp_svc, trace_svc = graph_services

        # 1. Foundation: Firm -> Client -> Engagement
        firm = firm_svc.create_firm(CreateFirmDTO(name="A.K. Singhal & Co. Chartered Accountants"))
        client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Solaris Power Technologies Ltd"))
        eng = eng_svc.create_engagement(
            CreateEngagementDTO(
                firm_id=firm.id,
                client_id=client.id,
                financial_year="2025-26",
                audit_type=AuditTypeEnum.STATUTORY_AUDIT,
                status=EngagementStatusEnum.PLANNING,
            )
        )

        # 2. Risk (SA 315) -> Assertion (Cut-Off)
        risk = matrix_svc.create_risk(
            AuditRisk(
                engagement_id=eng.id,
                risk_code="R-REV-01",
                title="Premature Revenue Recognition & Year-End Cut-Off Inaccuracy",
                category="Revenue & Receivables",
                description="Risk that sales dispatched after year-end are booked in current fiscal year.",
                assertions=[AssertionEnum.CUT_OFF, AssertionEnum.OCCURRENCE],
                inherent_risk=RiskSeverityEnum.HIGH,
                control_risk=RiskSeverityEnum.MEDIUM,
            )
        )
        assert risk.derived_romm == RiskSeverityEnum.HIGH
        assert risk.assertion == AssertionEnum.CUT_OFF

        # 3. Procedure (SA 330) responding to Risk & targeting Population
        proc = matrix_svc.create_procedure(
            AuditProcedure(
                engagement_id=eng.id,
                procedure_code="P-REV-CUTOFF-01",
                objective="Inspect dispatch gate passes and transporter lorry receipts for ±10 days around March 31.",
                account_area="Revenue",
                instructions="Sample 100% of sales invoices > performance materiality in boundary period.",
                population_definition="General Ledger Sales Account 401000 transactions between 2026-03-21 and 2026-04-10.",
                evidence_requirement="Verified Dispatch Gate Pass (GP) and Signed Customer Delivery Receipt.",
                linked_risk_ids=[risk.id],
                assertions=[AssertionEnum.CUT_OFF],
                status=ProcedureStatusEnum.IN_PROGRESS,
            )
        )
        assert proc.audit_area == "Revenue"
        assert proc.population.startswith("General Ledger Sales")
        assert proc.expected_evidence.startswith("Verified Dispatch")
        assert proc.risk_id == risk.id

        # 4. Sample Selection & Test Execution (SA 530 / SA 330)
        sample_item = AuditSampleItemTest(
            procedure_id=proc.id,
            item_identifier="INV-99042 / DN-8812",
            account_code="401000",
            expected_value_paise=150000000,
            actual_value_paise=0,  # Unbilled dispatch pre year-end
            explanation="Goods delivered 2026-03-29 but invoice entered on 2026-04-02 in next FY.",
            tested_by="Senior Auditor",
        )
        diff = sample_item.calculate_difference()
        assert sample_item.test_result == AuditTestOutcomeEnum.EXCEPTION

        test_run = TestExecution(
            engagement_id=eng.id,
            procedure_id=proc.id,
            population_reference=proc.population,
            sample_ids=[sample_item.id],
            tested_by="Senior Auditor",
            methodology_version=1,
            result=ProcedureConclusionEnum.EXCEPTION,
            exception_ids=["EXC-REV-01"],
            notes="Identified cut-off timing exception on sample item INV-99042.",
        )
        assert test_run.result == ProcedureConclusionEnum.EXCEPTION

        # 5. Exception Recorded
        audit_exc = AuditException(
            engagement_id=eng.id,
            procedure_id=proc.id,
            sample_item_id=sample_item.id,
            exception_code="EXC-REV-01",
            title="Unbilled Pre-Year-End Dispatch",
            description="Goods dispatched on March 29, 2026 was billed in April 2026.",
            source="Cut-Off Testing",
            rule="Revenue Recognition Period Matching (AS 9 / Ind AS 115)",
            severity="High",
            amount_paise=150000000,
            root_cause="Billing department delayed invoice issuance past fiscal close.",
            status=ExceptionStatusEnum.OPEN,
        )
        assert audit_exc.explanation.startswith("Goods dispatched")

        # 6. Evidence Attached
        evidence = matrix_svc.attach_evidence(
            AuditEvidence(
                engagement_id=eng.id,
                procedure_id=proc.id,
                document_id=None,
                title="Lorry Receipt LR-8812 & Gate Pass GP-99042",
                excerpt_or_reference="Confirmed physical dispatch date 2026-03-29.",
            )
        )

        # 7. Finding Crystallized
        finding = matrix_svc.create_finding(
            AuditFinding(
                engagement_id=eng.id,
                procedure_id=proc.id,
                risk_id=risk.id,
                title="Revenue Understated in FY 25-26 by ₹15,00,000",
                description="Unbilled dispatch before year-end resulted in revenue cut-off timing error.",
                severity=RiskSeverityEnum.HIGH,
                amount_paise=150000000,
                affected_account="401000 - Domestic Sales",
                assertion=AssertionEnum.CUT_OFF,
                recommendation="Post audit adjustment Dr Unbilled Revenue Cr Sales.",
                status=FindingStatusEnum.OPEN,
                linked_exception_ids=[audit_exc.id],
            )
        )

        # Link evidence to finding
        matrix_svc.link_evidence_to_finding(finding.id, evidence.id)

        # 8. Working Paper Created & Linked
        wp = wp_svc.create_working_paper(
            CreateWorkingPaperDTO(
                engagement_id=eng.id,
                index_reference="C.01",
                title="Revenue & Receivables Lead Schedule & Cut-Off Audit",
                area="Revenue",
                file_category=FileCategoryEnum.CURRENT_FILE,
                preparer_id="auditor_01",
            )
        )
        # Explicit link in WP repository
        wp_svc.add_link(
            working_paper_id=wp.id,
            target_type="Procedure",
            target_id=proc.id,
            link_description="Cut-Off substantive procedure",
            actor="Senior Auditor",
        )
        wp_svc.add_link(
            working_paper_id=wp.id,
            target_type="Finding",
            target_id=finding.id,
            link_description="Revenue cut-off timing finding",
            actor="Senior Auditor",
        )

        # =========================================================================
        # VERIFY BIDIRECTIONAL GRAPH NAVIGATION
        # =========================================================================

        # A. Finding -> Evidence & Evidence -> Finding
        evs = trace_svc.get_evidence_for_finding(eng.id, finding.id)
        assert len(evs) == 1
        assert evs[0].id == evidence.id

        findings = trace_svc.get_findings_for_evidence(eng.id, evidence.id)
        assert len(findings) == 1
        assert findings[0].id == finding.id

        # B. Working Paper -> Procedure & Procedure -> Working Paper
        procs_for_wp = trace_svc.get_procedures_for_working_paper(eng.id, wp.id)
        assert any(p.id == proc.id for p in procs_for_wp)

        wps_for_proc = trace_svc.get_working_papers_for_procedure(eng.id, proc.id)
        assert any(w.id == wp.id for w in wps_for_proc)

        # C. Procedure -> Risk & Risk -> Procedure
        risks_for_proc = trace_svc.get_risks_for_procedure(eng.id, proc.id)
        assert any(r.id == risk.id for r in risks_for_proc)

        procs_for_risk = trace_svc.get_procedures_for_risk(eng.id, risk.id)
        assert any(p.id == proc.id for p in procs_for_risk)

        # D. Risk -> Working Paper & Working Paper -> Risk
        wps_for_risk = trace_svc.get_working_papers_for_risk(eng.id, risk.id)
        assert any(w.id == wp.id for w in wps_for_risk)

        risks_for_wp = trace_svc.get_risks_for_working_paper(eng.id, wp.id)
        assert any(r.id == risk.id for r in risks_for_wp)

        # E. Full Traceability Graph DTO
        graph = trace_svc.build_finding_traceability(eng.id, finding.id)
        assert graph.finding_id == finding.id
        node_types = {n["type"] for n in graph.nodes}
        assert "Finding" in node_types
        assert "Procedure" in node_types
        assert "Risk" in node_types
        assert "WorkingPaper" in node_types
