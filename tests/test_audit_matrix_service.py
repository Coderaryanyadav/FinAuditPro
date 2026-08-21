"""Integration tests for Audit Matrix Service (Risks, Procedures, Findings, Evidence)."""

import pytest

from finauditpro.application.audit_matrix_dtos import (
    AttachEvidenceDTO,
    CreateFindingDTO,
    CreateProcedureDTO,
    CreateRiskDTO,
)
from finauditpro.application.dtos import CreateClientDTO, CreateEngagementDTO, CreateFirmDTO
from finauditpro.application.services.audit_matrix_service import AuditMatrixService
from finauditpro.application.services.client_service import ClientService
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import FirmService
from finauditpro.domain.audit_matrix_entities import AssertionEnum, RiskSeverityEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager


@pytest.fixture
def setup_services(tmp_path):
    db_path = tmp_path / "test_matrix_svc.db"
    manager = DatabaseManager(db_path=db_path)
    manager.create_tables()

    firm_svc = FirmService(manager)
    client_svc = ClientService(manager)
    eng_svc = EngagementService(manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="Matrix Audit Firm"))
    client = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Matrix Client Ltd"))
    eng = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client.id, financial_year="2025-26")
    )

    matrix_svc = AuditMatrixService(manager)
    return manager, eng, matrix_svc


def test_full_audit_traceability_chain(setup_services) -> None:
    _manager, eng, matrix_svc = setup_services

    # 1. Identify Audit Risk
    risk_dto = CreateRiskDTO(
        engagement_id=eng.id,
        risk_code="RSK-CUT-01",
        category="Revenue Cut-Off",
        description="Risk of premature revenue recognition prior to year-end cut-off date.",
        assertion=AssertionEnum.CUT_OFF,
        inherent_risk=RiskSeverityEnum.HIGH,
        control_risk=RiskSeverityEnum.MEDIUM,
        severity=RiskSeverityEnum.HIGH,
        risk_response="Perform detailed year-end invoice cut-off testing 5 days pre and post March 31.",
    )
    risk = matrix_svc.create_risk(risk_dto)
    assert risk.id is not None
    assert risk.risk_code == "RSK-CUT-01"

    # 2. Create Audit Procedure linked to Risk
    proc_dto = CreateProcedureDTO(
        engagement_id=eng.id,
        risk_id=risk.id,
        procedure_code="PROC-CUT-01",
        objective="Inspect sales invoices posted between March 25 and April 5.",
        assertion=AssertionEnum.CUT_OFF,
        instructions="Match invoice dates against dispatch documentation and shipping bills.",
    )
    proc = matrix_svc.create_procedure(proc_dto)
    assert proc.id is not None
    assert proc.risk_id == risk.id

    # 3. Log Audit Finding linked to Procedure & Risk
    finding_dto = CreateFindingDTO(
        engagement_id=eng.id,
        procedure_id=proc.id,
        risk_id=risk.id,
        title="Revenue Cut-Off Exception: Invoice #1092 Prematurely Recorded",
        description="Invoice #1092 dated April 2 was recorded in March sales register.",
        monetary_amount=850000.0,
        affected_account="Sales Revenue",
        assertion=AssertionEnum.CUT_OFF,
    )
    finding = matrix_svc.create_finding(finding_dto)
    assert finding.id is not None
    assert finding.procedure_id == proc.id
    assert finding.risk_id == risk.id

    # 4. Attach Evidence to Finding & Procedure
    ev_dto = AttachEvidenceDTO(
        engagement_id=eng.id,
        finding_id=finding.id,
        procedure_id=proc.id,
        row_index=142,
        title="Sales Register Row #142 & Shipping Bill Copy",
        excerpt_or_reference="Shipping bill dated April 2, 2026 confirms goods dispatched post year-end.",
    )
    ev = matrix_svc.attach_evidence(ev_dto)
    assert ev.id is not None
    assert ev.finding_id == finding.id

    # 5. Verify Retrieval & Traceability
    risks = matrix_svc.list_risks_for_engagement(eng.id)
    procs = matrix_svc.list_procedures_for_engagement(eng.id)
    findings = matrix_svc.list_findings_for_engagement(eng.id)
    evidences = matrix_svc.list_evidence_for_engagement(eng.id)

    assert len(risks) == 1
    assert len(procs) == 1
    assert len(findings) == 1
    assert len(evidences) == 1
