"""Regression test suite verifying Prompt 9 security and data-integrity remediations:
SEC-01 (RBAC & SecurityContext), SEC-02 (Cross-tenant isolation), DAT-01 (Evidence integrity), AUD-01 (Completeness).
"""

from pathlib import Path
from uuid import uuid4

import pytest

from finauditpro.application.dtos import CreateEngagementDTO
from finauditpro.application.report_dtos import ApproveReportDTO, GenerateReportDTO
from finauditpro.application.security.rbac import UserSession
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.application.services.client_service import ClientService, CreateClientDTO
from finauditpro.application.services.document_service import (
    CreateEvidenceLinkDTO,
    DocumentService,
    UploadDocumentDTO,
)
from finauditpro.application.services.engagement_service import EngagementService
from finauditpro.application.services.firm_service import CreateFirmDTO, FirmService
from finauditpro.application.services.report_service import ReportService
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import CreateWorkingPaperDTO, SignOffDTO
from finauditpro.domain.entities import RoleEnum
from finauditpro.domain.exceptions import PermissionDeniedError, ValidationError
from finauditpro.domain.working_paper_entities import SignOffLevelEnum
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.migration_list import get_all_migrations
from finauditpro.infrastructure.persistence.migrations import MigrationRunner
from finauditpro.infrastructure.persistence.repositories import (
    UserRepository,
)
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


@pytest.fixture
def remediation_env(tmp_path):
    db_file = tmp_path / "test_remediation.db"
    db_manager = DatabaseManager(str(db_file))
    db_manager.create_tables()
    runner = MigrationRunner(str(db_file))
    runner.run_all(get_all_migrations())

    firm_svc = FirmService(db_manager)
    client_svc = ClientService(db_manager)
    eng_svc = EngagementService(db_manager)
    wp_svc = WorkingPaperService(db_manager)
    doc_svc = DocumentService(db_manager)
    rep_svc = ReportService(db_manager)

    firm = firm_svc.create_firm(CreateFirmDTO(name="National CA Practice"))
    client_a = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Alpha Ltd"))
    client_b = client_svc.create_client(CreateClientDTO(firm_id=firm.id, name="Client Beta Ltd"))

    with db_manager.session_scope() as session:
        user_repo = UserRepository(session)
        user_repo.create_user_with_password("assoc@firm.com", "Password@123", role="Associate")
        user_repo.create_user_with_password("senior@firm.com", "Password@123", role="Senior")
        user_repo.create_user_with_password("partner@firm.com", "Password@123", role="Partner")

    eng_a = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_a.id, financial_year="2025-26")
    )
    eng_b = eng_svc.create_engagement(
        CreateEngagementDTO(firm_id=firm.id, client_id=client_b.id, financial_year="2025-26")
    )

    wp_svc.assign_user_to_engagement(eng_a.id, "assoc@firm.com", "Associate")
    wp_svc.assign_user_to_engagement(eng_a.id, "senior@firm.com", "Senior")
    wp_svc.assign_user_to_engagement(eng_a.id, "partner@firm.com", "Partner")

    wp_svc.assign_user_to_engagement(eng_b.id, "assoc@firm.com", "Associate")
    wp_svc.assign_user_to_engagement(eng_b.id, "senior@firm.com", "Senior")
    wp_svc.assign_user_to_engagement(eng_b.id, "partner@firm.com", "Partner")

    return {
        "db": db_manager,
        "eng_a": eng_a,
        "eng_b": eng_b,
        "wp_svc": wp_svc,
        "doc_svc": doc_svc,
        "rep_svc": rep_svc,
        "tmp_path": tmp_path,
    }


def test_sec01_associate_cannot_approve_partner_only_final_signoff(remediation_env) -> None:
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-CASH-01",
            title="Cash Balance",
            area="Cash",
            preparer_id="preparer@firm.com",
        )
    )

    with (
        SecurityContext.with_session(
            UserSession(
                user_id="assoc@firm.com", username="assoc@firm.com", role=RoleEnum.ASSOCIATE
            )
        ),
        pytest.raises(
            ValidationError, match="Unauthorized: Only Partners can perform final sign-off"
        ),
    ):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="assoc@firm.com",
                user_role="Associate",
            )
        )


def test_sec01_associate_cannot_forge_partner_role_in_dto(remediation_env) -> None:
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-CASH-02",
            title="Cash Balance",
            area="Cash",
            preparer_id="preparer@firm.com",
        )
    )

    with (
        SecurityContext.with_session(
            UserSession(
                user_id="assoc@firm.com", username="assoc@firm.com", role=RoleEnum.ASSOCIATE
            )
        ),
        pytest.raises(
            ValidationError, match="Unauthorized: Only Partners can perform final sign-off"
        ),
    ):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="assoc@firm.com",
                user_role="Partner",
            )
        )


def test_sec01_associate_cannot_forge_partner_user_id_in_dto(remediation_env) -> None:
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-CASH-03",
            title="Cash Balance",
            area="Cash",
            preparer_id="preparer@firm.com",
        )
    )

    # Logged-in session is Associate; DTO attempts to claim user_id is partner@firm.com
    with (
        SecurityContext.with_session(
            UserSession(
                user_id="assoc@firm.com", username="assoc@firm.com", role=RoleEnum.ASSOCIATE
            )
        ),
        pytest.raises(
            ValidationError, match="Unauthorized: Only Partners can perform final sign-off"
        ),
    ):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="partner@firm.com",
                user_role="Partner",
            )
        )


def test_sec01_unregistered_user_substring_partner_rejected(remediation_env) -> None:
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-CASH-04",
            title="Cash Balance",
            area="Cash",
            preparer_id="preparer@firm.com",
        )
    )

    with (
        SecurityContext.with_session(
            UserSession(
                user_id="assoc@firm.com", username="assoc@firm.com", role=RoleEnum.ASSOCIATE
            )
        ),
        pytest.raises(
            ValidationError, match="Unauthorized: Only Partners can perform final sign-off"
        ),
    ):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="fake_partner_impostor",
                user_role="Partner",
            )
        )


def test_sec01_report_approval_rejects_associate_with_forged_role(remediation_env) -> None:
    rep_svc = remediation_env["rep_svc"]
    eng_a = remediation_env["eng_a"]

    templates = rep_svc.list_templates()
    tmpl_id = templates[0].id if templates else "default"

    rep = rep_svc.generate_report(
        GenerateReportDTO(
            engagement_id=eng_a.id,
            template_id=tmpl_id,
            title="Statutory Audit Report",
            generated_by="assoc@firm.com",
        )
    )

    with (
        SecurityContext.with_session(
            UserSession(
                user_id="assoc@firm.com", username="assoc@firm.com", role=RoleEnum.ASSOCIATE
            )
        ),
        pytest.raises(
            PermissionDeniedError, match="Permission denied for action 'engagement:signoff'"
        ),
    ):
        rep_svc.approve_report(
            ApproveReportDTO(
                report_id=rep.id, approved_by="assoc@firm.com", approver_role="Partner"
            )
        )


def test_sec02_cross_engagement_evidence_linking_strictly_blocked(remediation_env) -> None:
    doc_svc = remediation_env["doc_svc"]
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]
    eng_b = remediation_env["eng_b"]
    tmp_path = remediation_env["tmp_path"]

    doc_file = tmp_path / "confidential_alpha.txt"
    doc_file.write_text("Alpha Secret Contract")
    doc_a = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng_a.id, file_path=str(doc_file))
    )

    wp_b = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_b.id,
            index_reference="WP-BETA-01",
            title="Beta Testing",
            area="Revenue",
            preparer_id="preparer@firm.com",
        )
    )

    # Cross-tenant link attempt: Document from Eng A into Eng B working paper
    with pytest.raises(ValidationError, match="Cross-Engagement Violation"):
        doc_svc.create_evidence_link(
            CreateEvidenceLinkDTO(
                engagement_id=eng_b.id,
                document_id=doc_a.id,
                page_number=1,
                target_type="Working Paper",
                target_id=wp_b.id,
                title="Cross Link",
            )
        )


def test_dat01_working_paper_integrity_detects_tampered_and_deleted_evidence(
    remediation_env,
) -> None:
    doc_svc = remediation_env["doc_svc"]
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]
    db = remediation_env["db"]
    tmp_path = remediation_env["tmp_path"]

    doc_file = tmp_path / "bank_evidence.txt"
    doc_file.write_text("SBI Confirmed Bank Balance: ₹50,00,000.00", encoding="utf-8")
    doc = doc_svc.upload_and_process_document(
        UploadDocumentDTO(engagement_id=eng_a.id, file_path=str(doc_file))
    )

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-BRS-01",
            title="Bank Reconciliation",
            area="Bank",
            preparer_id="senior@firm.com",
        )
    )

    with db.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        wp_repo.add_link(str(uuid4()), wp.id, "Document", doc.id)

    with SecurityContext.with_session(
        UserSession(user_id="partner@firm.com", username="partner@firm.com", role=RoleEnum.PARTNER)
    ):
        wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="partner@firm.com",
                user_role="Partner",
            )
        )

    # 1. Verification with intact evidence passes
    is_valid, msg = wp_svc.verify_integrity(wp.id)
    assert is_valid is True
    assert "Integrity Verified" in msg

    # 2. Tampering evidence on disk fails integrity check
    stored_path = Path(doc.stored_path)
    stored_path.write_text("TAMPERED BANK BALANCE: ₹100.00", encoding="utf-8")
    is_valid_tampered, msg_tampered = wp_svc.verify_integrity(wp.id)
    assert is_valid_tampered is False
    assert "modified or tampered" in msg_tampered

    # 3. Deleting evidence on disk fails integrity check
    stored_path.unlink()
    is_valid_del, msg_del = wp_svc.verify_integrity(wp.id)
    assert is_valid_del is False
    assert "missing from storage disk" in msg_del


def test_authorized_partner_signoff_succeeds(remediation_env) -> None:
    wp_svc = remediation_env["wp_svc"]
    eng_a = remediation_env["eng_a"]

    wp = wp_svc.create_working_paper(
        CreateWorkingPaperDTO(
            engagement_id=eng_a.id,
            index_reference="WP-PPE-01",
            title="PPE Substantive",
            area="Fixed Assets",
            preparer_id="senior@firm.com",
        )
    )

    with SecurityContext.with_session(
        UserSession(user_id="partner@firm.com", username="partner@firm.com", role=RoleEnum.PARTNER)
    ):
        signoff = wp_svc.sign_off_working_paper(
            SignOffDTO(
                working_paper_id=wp.id,
                level=SignOffLevelEnum.FINAL_SIGN_OFF,
                user_id="partner@firm.com",
                user_role="Partner",
            )
        )
        assert signoff.level == SignOffLevelEnum.FINAL_SIGN_OFF
        assert signoff.user_role == "Partner"
