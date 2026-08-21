"""Repository managing persistence for Report Templates, Reports, and Artifacts."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from finauditpro.domain.report_entities import (
    DEFAULT_REPORT_TEMPLATES,
    ExportFormatEnum,
    Report,
    ReportArtifact,
    ReportStatusEnum,
    ReportTemplate,
    ReportTypeEnum,
)
from finauditpro.infrastructure.persistence.report_models import (
    ReportArtifactModel,
    ReportModel,
    ReportTemplateModel,
)


class ReportRepository:
    """Repository for Report Templates, Assembled Reports, and Export Artifacts."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def seed_default_templates(self) -> None:
        """Seed non-statutory default templates if missing."""
        for tpl in DEFAULT_REPORT_TEMPLATES:
            if not self.session.get(ReportTemplateModel, tpl.id):
                model = ReportTemplateModel(
                    id=tpl.id,
                    name=tpl.name,
                    report_type=tpl.report_type.value,
                    version=tpl.version,
                    section_structure_json=tpl.section_structure_json,
                    source=tpl.source,
                    jurisdiction=tpl.jurisdiction,
                    effective_from=tpl.effective_from,
                    verified_statutory=tpl.verified_statutory,
                    created_at=tpl.created_at,
                    updated_at=tpl.updated_at,
                )
                self.session.add(model)
        self.session.flush()

    def get_template(self, template_id: str) -> ReportTemplate | None:
        model = self.session.get(ReportTemplateModel, template_id)
        if not model:
            self.seed_default_templates()
            model = self.session.get(ReportTemplateModel, template_id)
        if not model:
            return None
        return ReportTemplate(
            id=model.id,
            name=model.name,
            report_type=ReportTypeEnum(model.report_type),
            version=model.version,
            section_structure_json=model.section_structure_json,
            source=model.source,
            jurisdiction=model.jurisdiction,
            effective_from=model.effective_from,
            verified_statutory=model.verified_statutory,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list_templates(self) -> list[ReportTemplate]:
        self.seed_default_templates()
        stmt = select(ReportTemplateModel).order_by(ReportTemplateModel.name)
        models = self.session.scalars(stmt).all()
        return [
            ReportTemplate(
                id=m.id,
                name=m.name,
                report_type=ReportTypeEnum(m.report_type),
                version=m.version,
                section_structure_json=m.section_structure_json,
                source=m.source,
                jurisdiction=m.jurisdiction,
                effective_from=m.effective_from,
                verified_statutory=m.verified_statutory,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def add_report(self, report: Report) -> Report:
        model = ReportModel(
            id=report.id,
            engagement_id=report.engagement_id,
            template_id=report.template_id,
            template_version=report.template_version,
            title=report.title,
            report_type=report.report_type.value,
            status=report.status.value,
            data_as_of=report.data_as_of,
            content_model_json=report.content_model_json,
            content_hash=report.content_hash,
            generated_by=report.generated_by,
            reviewed_by=report.reviewed_by,
            approved_by=report.approved_by,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )
        self.session.add(model)
        self.session.flush()
        return report

    def get_report(self, report_id: str) -> Report | None:
        model = self.session.get(ReportModel, report_id)
        if not model:
            return None
        return Report(
            id=model.id,
            engagement_id=model.engagement_id,
            template_id=model.template_id,
            template_version=model.template_version,
            title=model.title,
            report_type=ReportTypeEnum(model.report_type),
            status=ReportStatusEnum(model.status),
            data_as_of=model.data_as_of,
            content_model_json=model.content_model_json,
            content_hash=model.content_hash,
            generated_by=model.generated_by,
            reviewed_by=model.reviewed_by,
            approved_by=model.approved_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list_for_engagement(self, engagement_id: str) -> list[Report]:
        stmt = (
            select(ReportModel)
            .where(ReportModel.engagement_id == engagement_id)
            .order_by(ReportModel.created_at.desc())
        )
        models = self.session.scalars(stmt).all()
        return [
            Report(
                id=m.id,
                engagement_id=m.engagement_id,
                template_id=m.template_id,
                template_version=m.template_version,
                title=m.title,
                report_type=ReportTypeEnum(m.report_type),
                status=ReportStatusEnum(m.status),
                data_as_of=m.data_as_of,
                content_model_json=m.content_model_json,
                content_hash=m.content_hash,
                generated_by=m.generated_by,
                reviewed_by=m.reviewed_by,
                approved_by=m.approved_by,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def update_report(self, report: Report) -> Report:
        model = self.session.get(ReportModel, report.id)
        if model:
            model.status = report.status.value
            model.reviewed_by = report.reviewed_by
            model.approved_by = report.approved_by
            model.updated_at = report.updated_at
            self.session.flush()
        return report

    def add_artifact(self, artifact: ReportArtifact) -> ReportArtifact:
        model = ReportArtifactModel(
            id=artifact.id,
            report_id=artifact.report_id,
            format=artifact.format.value,
            stored_document_id=artifact.stored_document_id,
            file_path=artifact.file_path,
            content_hash=artifact.content_hash,
            created_at=artifact.created_at,
        )
        self.session.add(model)
        self.session.flush()
        return artifact

    def list_artifacts(self, report_id: str) -> list[ReportArtifact]:
        stmt = select(ReportArtifactModel).where(ReportArtifactModel.report_id == report_id)
        models = self.session.scalars(stmt).all()
        return [
            ReportArtifact(
                id=m.id,
                report_id=m.report_id,
                format=ExportFormatEnum(m.format),
                stored_document_id=m.stored_document_id,
                file_path=m.file_path,
                content_hash=m.content_hash,
                created_at=m.created_at,
            )
            for m in models
        ]
