"""Repository for persisting AuditReportWorkpaper, Lineage, and Version models (Phase E)."""

import json
from uuid import uuid4
from sqlalchemy.orm import Session

from finauditpro.domain.audit_report_entities import (
    AuditOpinionTypeEnum,
    AuditReportWorkpaper,
    BasisOfOpinionItem,
    EmphasisOrOtherMatter,
    KeyAuditMatter,
    ReportDataLineage,
    ReportWorkpaperStatusEnum,
    SourceLineageTypeEnum,
)
from finauditpro.infrastructure.persistence.audit_report_models import (
    AuditReportLineageModel,
    AuditReportVersionModel,
    AuditReportWorkpaperModel,
)


class AuditReportRepository:
    """Persistence operations for statutory audit report workpapers and data lineage."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def add_report_workpaper(self, wp: AuditReportWorkpaper) -> AuditReportWorkpaper:
        model = self._to_model(wp)
        self.session.add(model)
        self.session.flush()
        return wp

    def get_report_workpaper(self, wp_id: str) -> AuditReportWorkpaper | None:
        model = (
            self.session.query(AuditReportWorkpaperModel)
            .filter(AuditReportWorkpaperModel.id == wp_id)
            .first()
        )
        return self._to_domain(model) if model else None

    def get_report_workpaper_for_engagement(
        self, engagement_id: str
    ) -> AuditReportWorkpaper | None:
        model = (
            self.session.query(AuditReportWorkpaperModel)
            .filter(AuditReportWorkpaperModel.engagement_id == engagement_id)
            .order_by(AuditReportWorkpaperModel.created_at.desc())
            .first()
        )
        return self._to_domain(model) if model else None

    def update_report_workpaper(self, wp: AuditReportWorkpaper) -> AuditReportWorkpaper:
        model = (
            self.session.query(AuditReportWorkpaperModel)
            .filter(AuditReportWorkpaperModel.id == wp.id)
            .first()
        )
        if not model:
            return self.add_report_workpaper(wp)

        model.reporting_framework = wp.reporting_framework
        model.financial_year = wp.financial_year
        model.entity_name = wp.entity_name
        model.applicable_companies_act_framework = wp.applicable_companies_act_framework
        model.applicable_auditing_framework = wp.applicable_auditing_framework
        model.materiality_paise = wp.materiality_paise
        model.proposed_opinion = wp.proposed_opinion.value
        model.final_opinion = wp.final_opinion.value
        model.opinion_rationale = wp.opinion_rationale
        model.basis_of_opinion_json = json.dumps([b.model_dump() for b in wp.basis_of_opinion_items])
        model.kam_applicable = wp.kam_applicable
        model.key_audit_matters_json = json.dumps([k.model_dump() for k in wp.key_audit_matters])
        model.emphasis_other_matters_json = json.dumps([e.model_dump() for e in wp.emphasis_other_matters])
        model.caro_applicable = wp.caro_applicable
        model.caro_report_summary = wp.caro_report_summary
        model.tax_audit_applicable = wp.tax_audit_applicable
        model.tax_audit_summary = wp.tax_audit_summary
        model.going_concern_conclusion = wp.going_concern_conclusion
        model.subsequent_events_conclusion = wp.subsequent_events_conclusion
        model.misstatements_summary = wp.misstatements_summary
        model.management_rep_status = wp.management_rep_status
        model.status = wp.status.value
        model.version = wp.version
        model.is_locked = wp.is_locked
        model.preparer_id = wp.preparer_id
        model.reviewer_id = wp.reviewer_id
        model.approved_by_partner_id = wp.approved_by_partner_id
        model.approved_at = wp.approved_at
        model.dependency_hash = wp.dependency_hash
        model.udin = wp.udin
        model.updated_at = wp.updated_at
        self.session.flush()
        return wp

    def add_lineage_items(self, wp_id: str, items: list[ReportDataLineage]) -> None:
        self.session.query(AuditReportLineageModel).filter(
            AuditReportLineageModel.report_workpaper_id == wp_id
        ).delete()
        for item in items:
            m = AuditReportLineageModel(
                id=item.id,
                report_workpaper_id=wp_id,
                field_name=item.field_name,
                reported_value=item.reported_value,
                source_type=item.source_type.value,
                source_reference=item.source_reference,
                underlying_value=item.underlying_value,
                is_reconciled=item.is_reconciled,
            )
            self.session.add(m)
        self.session.flush()

    def list_lineage_for_workpaper(self, wp_id: str) -> list[ReportDataLineage]:
        models = (
            self.session.query(AuditReportLineageModel)
            .filter(AuditReportLineageModel.report_workpaper_id == wp_id)
            .all()
        )
        return [
            ReportDataLineage(
                id=m.id,
                field_name=m.field_name,
                reported_value=m.reported_value,
                source_type=SourceLineageTypeEnum(m.source_type),
                source_reference=m.source_reference,
                underlying_value=m.underlying_value,
                is_reconciled=m.is_reconciled,
            )
            for m in models
        ]

    def add_version_snapshot(
        self, wp_id: str, version: int, status: str, snapshot_json: str, dep_hash: str, user: str
    ) -> None:
        model = AuditReportVersionModel(
            id=f"{wp_id}-v{version}-{str(uuid4())[:8]}",
            report_workpaper_id=wp_id,
            version=version,
            status=status,
            snapshot_json=snapshot_json,
            dependency_hash=dep_hash,
            created_by=user,
        )
        self.session.add(model)
        self.session.flush()

    def _to_model(self, wp: AuditReportWorkpaper) -> AuditReportWorkpaperModel:
        return AuditReportWorkpaperModel(
            id=wp.id,
            engagement_id=wp.engagement_id,
            reporting_framework=wp.reporting_framework,
            financial_year=wp.financial_year,
            entity_name=wp.entity_name,
            applicable_companies_act_framework=wp.applicable_companies_act_framework,
            applicable_auditing_framework=wp.applicable_auditing_framework,
            materiality_paise=wp.materiality_paise,
            proposed_opinion=wp.proposed_opinion.value,
            final_opinion=wp.final_opinion.value,
            opinion_rationale=wp.opinion_rationale,
            basis_of_opinion_json=json.dumps([b.model_dump() for b in wp.basis_of_opinion_items]),
            kam_applicable=wp.kam_applicable,
            key_audit_matters_json=json.dumps([k.model_dump() for k in wp.key_audit_matters]),
            emphasis_other_matters_json=json.dumps([e.model_dump() for e in wp.emphasis_other_matters]),
            caro_applicable=wp.caro_applicable,
            caro_report_summary=wp.caro_report_summary,
            tax_audit_applicable=wp.tax_audit_applicable,
            tax_audit_summary=wp.tax_audit_summary,
            going_concern_conclusion=wp.going_concern_conclusion,
            subsequent_events_conclusion=wp.subsequent_events_conclusion,
            misstatements_summary=wp.misstatements_summary,
            management_rep_status=wp.management_rep_status,
            status=wp.status.value,
            version=wp.version,
            is_locked=wp.is_locked,
            preparer_id=wp.preparer_id,
            reviewer_id=wp.reviewer_id,
            approved_by_partner_id=wp.approved_by_partner_id,
            approved_at=wp.approved_at,
            dependency_hash=wp.dependency_hash,
            udin=wp.udin,
            created_at=wp.created_at,
            updated_at=wp.updated_at,
        )

    def _to_domain(self, m: AuditReportWorkpaperModel) -> AuditReportWorkpaper:
        basis_items = [BasisOfOpinionItem(**item) for item in json.loads(m.basis_of_opinion_json)]
        kam_items = [KeyAuditMatter(**item) for item in json.loads(m.key_audit_matters_json)]
        eom_items = [EmphasisOrOtherMatter(**item) for item in json.loads(m.emphasis_other_matters_json)]

        return AuditReportWorkpaper(
            id=m.id,
            engagement_id=m.engagement_id,
            reporting_framework=m.reporting_framework,
            financial_year=m.financial_year,
            entity_name=m.entity_name,
            applicable_companies_act_framework=m.applicable_companies_act_framework,
            applicable_auditing_framework=m.applicable_auditing_framework,
            materiality_paise=m.materiality_paise,
            proposed_opinion=AuditOpinionTypeEnum(m.proposed_opinion),
            final_opinion=AuditOpinionTypeEnum(m.final_opinion),
            opinion_rationale=m.opinion_rationale,
            basis_of_opinion_items=basis_items,
            kam_applicable=m.kam_applicable,
            key_audit_matters=kam_items,
            emphasis_other_matters=eom_items,
            caro_applicable=m.caro_applicable,
            caro_report_summary=m.caro_report_summary,
            tax_audit_applicable=m.tax_audit_applicable,
            tax_audit_summary=m.tax_audit_summary,
            going_concern_conclusion=m.going_concern_conclusion,
            subsequent_events_conclusion=m.subsequent_events_conclusion,
            misstatements_summary=m.misstatements_summary,
            management_rep_status=m.management_rep_status,
            status=ReportWorkpaperStatusEnum(m.status),
            version=m.version,
            is_locked=m.is_locked,
            preparer_id=m.preparer_id,
            reviewer_id=m.reviewer_id,
            approved_by_partner_id=m.approved_by_partner_id,
            approved_at=m.approved_at,
            dependency_hash=m.dependency_hash,
            udin=m.udin,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
