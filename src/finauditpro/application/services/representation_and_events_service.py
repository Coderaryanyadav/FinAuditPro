"""Application Service for SA 580 Management Representation Letters & SA 560 Subsequent Events Register."""

import json
from typing import Any

from finauditpro.application.audit_completion_dtos import (
    CreateSubsequentEventDTO,
    ManagementRepresentationLetterDTO,
    MRLClauseDTO,
    SubsequentEventDTO,
)
from finauditpro.application.security.rbac import RoleEnum
from finauditpro.application.security.security_context import SecurityContext
from finauditpro.domain.audit_completion_engine import AuditCompletionEngine
from finauditpro.domain.audit_completion_entities import (
    ManagementRepresentationLetter,
    MRLClause,
    MRLClauseCategoryEnum,
    MRLStatusEnum,
    SubsequentEvent,
    SubsequentEventTypeEnum,
)
from finauditpro.domain.exceptions import PermissionDeniedError
from finauditpro.infrastructure.persistence.database import DatabaseManager
from finauditpro.infrastructure.persistence.repositories.audit_completion_repository import (
    AuditCompletionRepository,
)


class RepresentationAndEventsService:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    def generate_default_mrl(
        self,
        engagement_id: str,
        financial_year: str,
        requested_date: str | None = None,
    ) -> ManagementRepresentationLetterDTO:
        SecurityContext.enforce_permission(
            "mrl:create", [RoleEnum.SENIOR, RoleEnum.MANAGER, RoleEnum.PARTNER, RoleEnum.ADMIN]
        )

        default_clauses = [
            MRLClause(
                clause_number="Clause 1",
                category=MRLClauseCategoryEnum.GENERAL_RESPONSIBILITY,
                title="Management Responsibility for Financial Statements",
                text_content=(
                    "Management acknowledges its responsibility for the preparation of the financial "
                    "statements in accordance with applicable Accounting Standards / Ind AS and the Companies Act, 2013."
                ),
            ),
            MRLClause(
                clause_number="Clause 2",
                category=MRLClauseCategoryEnum.INTERNAL_CONTROL_AND_IRREGULARITIES,
                title="Internal Financial Controls & Non-Compliance Disclosures",
                text_content=(
                    "Management has designed and maintained effective internal financial controls and has "
                    "disclosed all known or suspected irregularities or non-compliances to the auditors."
                ),
            ),
            MRLClause(
                clause_number="Clause 3",
                category=MRLClauseCategoryEnum.GOING_CONCERN,
                title="Going Concern & Operational Viability",
                text_content=(
                    "Management believes that the company is a going concern and has no plans or intentions "
                    "that may materially alter the carrying value or classification of assets and liabilities."
                ),
            ),
            MRLClause(
                clause_number="Clause 4",
                category=MRLClauseCategoryEnum.SUBSEQUENT_EVENTS,
                title="Subsequent Events Disclosures (SA 560)",
                text_content=(
                    "All events subsequent to the date of the financial statements for which standard requires "
                    "adjustment or disclosure have been adjusted or disclosed."
                ),
            ),
            MRLClause(
                clause_number="Clause 5",
                category=MRLClauseCategoryEnum.RELATED_PARTIES,
                title="Related Party Transactions & Balances",
                text_content=(
                    "All related party relationships and transactions have been appropriately accounted for "
                    "and disclosed in accordance with the requirements of AS 18 / Ind AS 24."
                ),
            ),
            MRLClause(
                clause_number="Clause 6",
                category=MRLClauseCategoryEnum.STATUTORY_COMPLIANCE,
                title="CARO 2020 and Form 3CD Compliance",
                text_content=(
                    "All information required for reporting under CARO 2020 and Form 3CD has been fully "
                    "and truthfully provided to the auditors."
                ),
            ),
        ]

        mrl_entity = ManagementRepresentationLetter(
            engagement_id=engagement_id,
            mrl_number=f"MRL-{financial_year}-001",
            financial_year=financial_year,
            requested_date=requested_date,
            status=MRLStatusEnum.DRAFT,
            clauses=default_clauses,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            saved = repo.save_mrl(mrl_entity)
            return self._to_mrl_dto(saved)

    def update_mrl_status(
        self,
        engagement_id: str,
        mrl_id: str,
        status: str,
        signed_date: str | None = None,
        signatory_name: str | None = None,
        signatory_designation: str | None = None,
        audit_report_date: str | None = None,
    ) -> ManagementRepresentationLetterDTO:
        SecurityContext.enforce_permission(
            "mrl:update", [RoleEnum.SENIOR, RoleEnum.MANAGER, RoleEnum.PARTNER, RoleEnum.ADMIN]
        )

        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            mrl = repo.get_mrl_by_id(mrl_id)
            if not mrl or mrl.engagement_id != engagement_id:
                raise ValueError(f"MRL {mrl_id} not found for engagement {engagement_id}")

            status_enum = MRLStatusEnum.DRAFT
            for s in MRLStatusEnum:
                if s.value == status or s.name == status:
                    status_enum = s
                    break

            is_chron_valid = True
            chron_msg = ""
            if signed_date and audit_report_date:
                is_chron_valid, chron_msg = AuditCompletionEngine.validate_mrl_chronology(
                    mrl_signed_date=signed_date,
                    audit_report_date=audit_report_date,
                )

            mrl.status = status_enum
            mrl.signed_date = signed_date
            mrl.signatory_name = signatory_name
            mrl.signatory_designation = signatory_designation
            mrl.audit_report_date = audit_report_date
            mrl.is_chronologically_valid = is_chron_valid
            mrl.chronology_validation_msg = chron_msg

            saved = repo.save_mrl(mrl)
            return self._to_mrl_dto(saved)

    def get_mrl(self, engagement_id: str) -> ManagementRepresentationLetterDTO | None:
        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            mrl = repo.get_mrl(engagement_id)
            return self._to_mrl_dto(mrl) if mrl else None

    def list_mrls(self, engagement_id: str) -> list[ManagementRepresentationLetterDTO]:
        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            mrls = repo.list_mrls(engagement_id)
            return [self._to_mrl_dto(m) for m in mrls]

    def record_subsequent_event(
        self,
        engagement_id: str,
        dto: CreateSubsequentEventDTO,
    ) -> SubsequentEventDTO:
        SecurityContext.enforce_permission(
            "subsequent_event:record",
            [RoleEnum.SENIOR, RoleEnum.MANAGER, RoleEnum.PARTNER, RoleEnum.ADMIN],
        )

        event_type_enum = SubsequentEventTypeEnum.ADJUSTING
        for t in SubsequentEventTypeEnum:
            if t.value == dto.event_type or t.name == dto.event_type:
                event_type_enum = t
                break

        current_user = SecurityContext.get_current_user_id() or "Auditor"

        event_entity = SubsequentEvent(
            engagement_id=engagement_id,
            event_date=dto.event_date,
            event_type=event_type_enum,
            description=dto.description,
            estimated_amount_paise=dto.estimated_amount_paise,
            accounting_treatment=dto.accounting_treatment,
            is_adjusted_in_fs=dto.is_adjusted_in_fs,
            is_disclosed_in_notes=dto.is_disclosed_in_notes,
            procedure_applied=dto.procedure_applied,
            auditor_conclusion=dto.auditor_conclusion,
            identified_by=current_user,
        )

        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            saved = repo.save_subsequent_event(event_entity)
            return self._to_subseq_dto(saved)

    def list_subsequent_events(self, engagement_id: str) -> list[SubsequentEventDTO]:
        with self.db_manager.session_scope() as session:
            repo = AuditCompletionRepository(session)
            events = repo.list_subsequent_events(engagement_id)
            return [self._to_subseq_dto(e) for e in events]

    def _to_mrl_dto(self, entity: ManagementRepresentationLetter) -> ManagementRepresentationLetterDTO:
        return ManagementRepresentationLetterDTO(
            id=entity.id,
            engagement_id=entity.engagement_id,
            mrl_number=entity.mrl_number,
            financial_year=entity.financial_year,
            requested_date=entity.requested_date,
            signed_date=entity.signed_date,
            signatory_name=entity.signatory_name,
            signatory_designation=entity.signatory_designation,
            audit_report_date=entity.audit_report_date,
            status=entity.status.value,
            clauses=[
                MRLClauseDTO(
                    id=c.id,
                    clause_number=c.clause_number,
                    category=c.category.value,
                    title=c.title,
                    text_content=c.text_content,
                    is_modified=c.is_modified,
                    specific_facts=c.specific_facts,
                )
                for c in entity.clauses
            ],
            is_chronologically_valid=entity.is_chronologically_valid,
            created_at=entity.created_at,
            chronology_validation_msg=entity.chronology_validation_msg,
        )

    def _to_subseq_dto(self, entity: SubsequentEvent) -> SubsequentEventDTO:
        proc_str = (
            entity.procedure_applied.value
            if hasattr(entity.procedure_applied, "value")
            else str(entity.procedure_applied)
        )
        return SubsequentEventDTO(
            id=entity.id,
            engagement_id=entity.engagement_id,
            event_date=entity.event_date,
            event_type=entity.event_type.value if hasattr(entity.event_type, "value") else str(entity.event_type),
            description=entity.description,
            estimated_amount_paise=entity.estimated_amount_paise,
            accounting_treatment=entity.accounting_treatment,
            is_adjusted_in_fs=entity.is_adjusted_in_fs,
            is_disclosed_in_notes=entity.is_disclosed_in_notes,
            working_paper_ref=entity.working_paper_ref,
            procedure_applied=proc_str,
            auditor_conclusion=entity.auditor_conclusion,
            created_at=entity.created_at,
            identified_by=entity.identified_by,
        )
