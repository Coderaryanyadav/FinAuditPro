"""Repository for Financial Statement Packages, Notes to Accounts, and Accounting Policies."""

import json
from uuid import uuid4

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from finauditpro.domain.financial_statement_entities import (
    AccountingPolicy,
    BalanceSheet,
    CashFlowStatement,
    DisclosureClassificationEnum,
    FinancialStatementNote,
    FinancialStatementPackage,
    FinancialStatementVersionEnum,
    PackageStatusEnum,
    ProfitAndLossStatement,
    StatementOfChangesInEquity,
)
from finauditpro.infrastructure.persistence.financial_statement_models import (
    AccountingPolicyModel,
    FinancialStatementNoteModel,
    FinancialStatementPackageModel,
)


class FinancialStatementRepository:
    """Persistence repository for financial statements, notes, and accounting policies."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_package(self, pkg: FinancialStatementPackage) -> FinancialStatementPackage:
        model = FinancialStatementPackageModel(
            id=pkg.id or str(uuid4()),
            engagement_id=pkg.engagement_id,
            version=pkg.version.value if hasattr(pkg.version, "value") else str(pkg.version),
            status=pkg.status.value if hasattr(pkg.status, "value") else str(pkg.status),
            balance_sheet_json=json.dumps(pkg.balance_sheet.model_dump(mode="json")),
            profit_loss_json=json.dumps(pkg.profit_and_loss.model_dump(mode="json")),
            cash_flow_json=json.dumps(pkg.cash_flow.model_dump(mode="json")),
            changes_in_equity_json=json.dumps(pkg.changes_in_equity.model_dump(mode="json")),
            is_locked=pkg.is_locked,
            data_hash=pkg.data_hash,
            is_stale=pkg.is_stale,
            created_by=pkg.created_by,
            approved_by=pkg.approved_by,
            created_at=pkg.created_at,
            updated_at=pkg.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_package_entity(model)

    def get_package_by_id(self, package_id: str) -> FinancialStatementPackage | None:
        model = self.session.get(FinancialStatementPackageModel, package_id)
        return self._to_package_entity(model) if model else None

    def get_latest_package(self, engagement_id: str) -> FinancialStatementPackage | None:
        stmt = (
            select(FinancialStatementPackageModel)
            .where(FinancialStatementPackageModel.engagement_id == engagement_id)
            .order_by(desc(FinancialStatementPackageModel.created_at))
        )
        model = self.session.scalars(stmt).first()
        return self._to_package_entity(model) if model else None

    def list_packages_for_engagement(self, engagement_id: str) -> list[FinancialStatementPackage]:
        stmt = (
            select(FinancialStatementPackageModel)
            .where(FinancialStatementPackageModel.engagement_id == engagement_id)
            .order_by(desc(FinancialStatementPackageModel.created_at))
        )
        return [self._to_package_entity(m) for m in self.session.scalars(stmt).all()]

    def update_package(self, pkg: FinancialStatementPackage) -> FinancialStatementPackage:
        model = self.session.get(FinancialStatementPackageModel, pkg.id)
        if not model:
            return self.add_package(pkg)
        model.version = pkg.version.value if hasattr(pkg.version, "value") else str(pkg.version)
        model.status = pkg.status.value if hasattr(pkg.status, "value") else str(pkg.status)
        model.balance_sheet_json = json.dumps(pkg.balance_sheet.model_dump(mode="json"))
        model.profit_loss_json = json.dumps(pkg.profit_and_loss.model_dump(mode="json"))
        model.cash_flow_json = json.dumps(pkg.cash_flow.model_dump(mode="json"))
        model.changes_in_equity_json = json.dumps(pkg.changes_in_equity.model_dump(mode="json"))
        model.is_locked = pkg.is_locked
        model.data_hash = pkg.data_hash
        model.is_stale = pkg.is_stale
        model.approved_by = pkg.approved_by
        model.updated_at = pkg.updated_at
        self.session.flush()
        return self._to_package_entity(model)

    def add_note(self, note: FinancialStatementNote) -> FinancialStatementNote:
        model = FinancialStatementNoteModel(
            id=note.id or str(uuid4()),
            engagement_id=note.engagement_id,
            package_id=note.package_id,
            note_number=note.note_number,
            title=note.title,
            fs_reference=note.fs_reference,
            source_type=note.source_type,
            disclosure_classification=note.disclosure_classification.value
            if hasattr(note.disclosure_classification, "value")
            else str(note.disclosure_classification),
            amount_paise=note.amount_paise,
            details_json=json.dumps(note.details),
            narrative=note.narrative,
            prepared_by=note.prepared_by,
            reviewed_by=note.reviewed_by,
            status=note.status,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_note_entity(model)

    def list_notes_for_engagement(self, engagement_id: str) -> list[FinancialStatementNote]:
        stmt = (
            select(FinancialStatementNoteModel)
            .where(FinancialStatementNoteModel.engagement_id == engagement_id)
            .order_by(FinancialStatementNoteModel.note_number)
        )
        return [self._to_note_entity(m) for m in self.session.scalars(stmt).all()]

    def update_note(self, note: FinancialStatementNote) -> FinancialStatementNote:
        model = self.session.get(FinancialStatementNoteModel, note.id)
        if not model:
            return self.add_note(note)
        model.title = note.title
        model.fs_reference = note.fs_reference
        model.amount_paise = note.amount_paise
        model.details_json = json.dumps(note.details)
        model.narrative = note.narrative
        model.reviewed_by = note.reviewed_by
        model.status = note.status
        model.updated_at = note.updated_at
        self.session.flush()
        return self._to_note_entity(model)

    def add_policy(self, pol: AccountingPolicy) -> AccountingPolicy:
        model = AccountingPolicyModel(
            id=pol.id or str(uuid4()),
            engagement_id=pol.engagement_id,
            policy_code=pol.policy_code,
            title=pol.title,
            category=pol.category,
            applicable_standard=pol.applicable_standard,
            policy_text=pol.policy_text,
            changes_text=pol.changes_text,
            reviewed_by=pol.reviewed_by,
            status=pol.status,
            created_at=pol.created_at,
            updated_at=pol.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return self._to_policy_entity(model)

    def list_policies_for_engagement(self, engagement_id: str) -> list[AccountingPolicy]:
        stmt = (
            select(AccountingPolicyModel)
            .where(AccountingPolicyModel.engagement_id == engagement_id)
            .order_by(AccountingPolicyModel.policy_code)
        )
        return [self._to_policy_entity(m) for m in self.session.scalars(stmt).all()]

    def _to_package_entity(self, m: FinancialStatementPackageModel) -> FinancialStatementPackage:
        bs_data = json.loads(m.balance_sheet_json) if m.balance_sheet_json else {}
        pnl_data = json.loads(m.profit_loss_json) if m.profit_loss_json else {}
        cf_data = json.loads(m.cash_flow_json) if m.cash_flow_json else {}
        eq_data = json.loads(m.changes_in_equity_json) if m.changes_in_equity_json else {}

        return FinancialStatementPackage(
            id=m.id,
            engagement_id=m.engagement_id,
            version=FinancialStatementVersionEnum(m.version)
            if m.version in FinancialStatementVersionEnum._value2member_map_
            else FinancialStatementVersionEnum.DRAFT_V1,
            status=PackageStatusEnum(m.status)
            if m.status in PackageStatusEnum._value2member_map_
            else PackageStatusEnum.DRAFT,
            balance_sheet=BalanceSheet(**bs_data)
            if bs_data
            else BalanceSheet(engagement_id=m.engagement_id, as_at_date=""),
            profit_and_loss=ProfitAndLossStatement(**pnl_data)
            if pnl_data
            else ProfitAndLossStatement(engagement_id=m.engagement_id, for_period_ended=""),
            cash_flow=CashFlowStatement(**cf_data)
            if cf_data
            else CashFlowStatement(engagement_id=m.engagement_id, for_period_ended=""),
            changes_in_equity=StatementOfChangesInEquity(**eq_data)
            if eq_data
            else StatementOfChangesInEquity(engagement_id=m.engagement_id),
            data_hash=m.data_hash,
            is_locked=m.is_locked,
            is_stale=m.is_stale,
            created_by=m.created_by,
            approved_by=m.approved_by,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _to_note_entity(self, m: FinancialStatementNoteModel) -> FinancialStatementNote:
        return FinancialStatementNote(
            id=m.id,
            engagement_id=m.engagement_id,
            package_id=m.package_id,
            note_number=m.note_number,
            title=m.title,
            fs_reference=m.fs_reference,
            source_type=m.source_type,
            disclosure_classification=DisclosureClassificationEnum(m.disclosure_classification)
            if m.disclosure_classification in DisclosureClassificationEnum._value2member_map_
            else DisclosureClassificationEnum.AUTOMATIC,
            amount_paise=m.amount_paise,
            details=json.loads(m.details_json) if m.details_json else [],
            narrative=m.narrative,
            prepared_by=m.prepared_by,
            reviewed_by=m.reviewed_by,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )

    def _to_policy_entity(self, m: AccountingPolicyModel) -> AccountingPolicy:
        return AccountingPolicy(
            id=m.id,
            engagement_id=m.engagement_id,
            policy_code=m.policy_code,
            title=m.title,
            category=m.category,
            applicable_standard=m.applicable_standard,
            policy_text=m.policy_text,
            changes_text=m.changes_text,
            reviewed_by=m.reviewed_by,
            status=m.status,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
