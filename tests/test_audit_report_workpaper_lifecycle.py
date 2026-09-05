"""Integration tests for AuditReportWorkpaper lifecycle, KAMs, Basis of Opinion, and Partner Approval."""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.audit_report_dtos import (
    AddBasisOfOpinionItemDTO,
    AddEmphasisOrOtherMatterDTO,
    AddKeyAuditMatterDTO,
    CreateAuditReportWorkpaperDTO,
    PartnerApproveReportDTO,
    UpdateAuditReportWorkpaperDTO,
)
from finauditpro.application.security.rbac import RoleEnum, UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.audit_report_service import AuditReportService
from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    ReportWorkpaperStatusEnum,
)
from finauditpro.domain.entities import (
    AuditTypeEnum,
    Client,
    Engagement,
    EngagementStatusEnum,
    Firm,
    User,
)
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.infrastructure.first_run import initialize_database
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories import (
    ClientRepository,
    EngagementRepository,
    FirmRepository,
    UserRepository,
)


@pytest.fixture
def db_manager(tmp_path: Path) -> DatabaseManager:
    db_file = tmp_path / "test_report_lifecycle.db"
    return initialize_database(db_file)


def test_audit_report_lifecycle(db_manager: DatabaseManager) -> None:
    eng_id = f"eng-{uuid4()}"
    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        partner = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_partner_vikram",
                password_hash="h",
                salt="s",
                display_name="CA Vikram (Partner)",
                role=RoleEnum.PARTNER,
            )
        )
        senior = user_repo.add_user(
            User(
                id=str(uuid4()),
                username="ca_senior_neha",
                password_hash="h",
                salt="s",
                display_name="CA Neha (Senior)",
                role=RoleEnum.SENIOR,
            )
        )
        firm = Firm(id="firm-01", name="Vikram & Co LLP")
        FirmRepository(session).add(firm)
        client = Client(id="cli-01", firm_id=firm.id, name="Solaris Energy Ltd")
        ClientRepository(session).add(client)
        eng = Engagement(
            id=eng_id,
            firm_id=firm.id,
            client_id=client.id,
            title="Statutory Audit 2025-26",
            financial_year="2025-26",
            audit_type=AuditTypeEnum.STATUTORY_AUDIT,
            status=EngagementStatusEnum.AUDIT_PROCEDURES,
        )
        EngagementRepository(session).add(eng)

    # 1. Senior prepares draft report workpaper
    SecurityContext.set_current_user(
        UserSession(user_id=senior.id, username=senior.username, role=senior.role)
    )
    svc = AuditReportService(db_manager)
    create_dto = CreateAuditReportWorkpaperDTO(
        engagement_id=eng_id,
        reporting_framework="Companies Act 2013 / Ind AS",
        proposed_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        final_opinion=AuditOpinionTypeEnum.UNMODIFIED,
        opinion_rationale="Unmodified opinion on true and fair view.",
    )
    wp = svc.get_or_create_report_workpaper(create_dto)
    assert wp.id is not None
    assert wp.status == ReportWorkpaperStatusEnum.DRAFT
    assert wp.entity_name == "Solaris Energy Ltd"

    # 2. Add Basis of Opinion Item
    svc.add_basis_of_opinion_item(
        wp.id,
        AddBasisOfOpinionItemDTO(
            issue_title="Revenue Cut-off Verification",
            financial_area="Revenue",
            assertion="Cut-off",
            procedure_ref="WP-REV-001",
            evidence_ref="EVID-DISPATCH-01",
            finding_description="Cut-off testing satisfactory across 50 dispatch notes.",
            misstatement_paise=0,
            is_material=False,
            is_pervasive=False,
            auditor_conclusion="Cut-off properly established.",
        ),
    )

    # 3. Add Key Audit Matter (SA 701)
    svc.add_key_audit_matter(
        wp.id,
        AddKeyAuditMatterDTO(
            matter_title="Valuation of Solar Plant Work-in-Progress",
            why_significant="High estimation uncertainty in percentage-of-completion method.",
            how_addressed="Independent technical expert recomputation and inspection of physical project milestones.",
            fs_reference="Note 14 to Financial Statements",
            wp_references=["WP-PPE-CWIP-01"],
            partner_conclusion="Valuation methodology is compliant with Ind AS 115 / Ind AS 16.",
        ),
    )

    # 4. Add Emphasis of Matter (SA 706)
    svc.add_emphasis_or_other_matter(
        wp.id,
        AddEmphasisOrOtherMatterDTO(
            matter_type="Emphasis of Matter",
            title="Material Sub-contracting Dispute",
            reason="Ongoing arbitration with turnkey EPC contractor without admitting liability.",
            fs_reference="Note 29 (Contingent Liabilities)",
            audit_evidence_ref="WP-LEGAL-CONFIRM-02",
            partner_decision="Include Emphasis of Matter paragraph drawing attention to Note 29.",
            final_wording="We draw attention to Note 29 of the financial statements describing the arbitration.",
        ),
    )

    # 5. Unauthorized Senior attempts Partner Approval -> MUST FAIL
    with pytest.raises(PermissionDeniedError):
        svc.partner_approve_report(
            PartnerApproveReportDTO(
                engagement_id=eng_id,
                report_workpaper_id=wp.id,
                approval_notes="Senior approval attempt",
            )
        )

    # 6. Authorized Partner approves report
    SecurityContext.set_current_user(
        UserSession(user_id=partner.id, username=partner.username, role=partner.role)
    )
    approved_wp = svc.partner_approve_report(
        PartnerApproveReportDTO(
            engagement_id=eng_id,
            report_workpaper_id=wp.id,
            approval_notes="Approved unmodified report with 1 KAM and 1 EOM.",
            udin="26987654AAAAAB9999",
        )
    )
    assert approved_wp.status == ReportWorkpaperStatusEnum.PARTNER_APPROVED
    assert approved_wp.approved_by_partner_id == partner.username
    assert approved_wp.udin == "26987654AAAAAB9999"
    assert len(approved_wp.dependency_hash) == 64

    # 7. Lock report
    locked_wp = svc.lock_final_report(wp.id)
    assert locked_wp.status == ReportWorkpaperStatusEnum.LOCKED
    assert locked_wp.is_locked is True

    # 8. Modifying locked report -> MUST FAIL
    with pytest.raises(ValidationError):
        svc.update_report_workpaper(
            wp.id,
            UpdateAuditReportWorkpaperDTO(opinion_rationale="Tampered rationale"),
        )
