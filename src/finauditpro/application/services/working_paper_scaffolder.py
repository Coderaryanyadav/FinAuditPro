"""Helper to scaffold Permanent Audit Files and Schedule III working papers."""

from finauditpro.domain.working_paper_entities import (
    WorkingPaper,
    WorkingPaperSection,
    WorkingPaperStatusEnum,
)
from finauditpro.domain.entities import AuditEvent
from finauditpro.infrastructure.persistence.repositories import AuditEventRepository
from finauditpro.infrastructure.persistence.repositories.working_paper_repository import (
    WorkingPaperRepository,
)


def scaffold_permanent_audit_file(db_manager, engagement_id: str, preparer_id: str = "auditor") -> list[WorkingPaper]:
    """Automatically scaffold standard ICAI Permanent Audit File (PAF) legal and statutory structures."""
    from finauditpro.domain.working_paper_entities import (
        DEFAULT_PERMANENT_FILE_HEADS,
        FileCategoryEnum,
    )

    created = []
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        existing = wp_repo.list_for_engagement(engagement_id)
        existing_refs = {w.index_reference for w in existing}

        for ref, title, area, scope_desc in DEFAULT_PERMANENT_FILE_HEADS:
            if ref in existing_refs:
                continue
            wp = WorkingPaper(
                engagement_id=engagement_id,
                index_reference=ref,
                title=title,
                area=area,
                file_category=FileCategoryEnum.PERMANENT_FILE,
                status=WorkingPaperStatusEnum.DRAFT,
                preparer_id=preparer_id,
            )
            saved_wp = wp_repo.add_working_paper(wp)
            for order, s_title, content in [
                (1, "1. Permanent Record Summary", scope_desc),
                (2, "2. Key Terms & Verification Details", "Record incorporation dates, authorized signatories, tax identification numbers, and terms."),
                (3, "3. Continuity & Update Log", "Verify if any amendments or alterations occurred during the current audit period."),
            ]:
                wp_repo.add_section(WorkingPaperSection(working_paper_id=saved_wp.id, section_order=order, title=s_title, content_markdown=content))
            created.append(saved_wp)

        if created:
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=preparer_id,
                    action="Permanent Audit File (PAF) Scaffolded",
                    details=f"Auto-generated {len(created)} standard ICAI Permanent Audit File (PAF) working paper templates.",
                )
            )
    return created


def scaffold_schedule_iii_working_papers(db_manager, engagement_id: str, preparer_id: str = "auditor") -> list[WorkingPaper]:
    """Automatically scaffold standard ICAI Schedule III statutory audit working papers (CAF)."""
    from finauditpro.domain.working_paper_entities import FileCategoryEnum

    standard_heads = [
        ("WP-A", "Cash & Cash Equivalents (Bank Confirmations & Reconciliation)", "Cash & Bank", "Verify 100% bank statement reconciliations, confirmation letters, and cash in hand verification."),
        ("WP-B", "Trade Receivables (Ageing & Balance Confirmations)", "Receivables", "Inspect trade receivable ageing schedules (>6 months), SA 505 third-party balance confirmations, and expected credit loss (ECL) provisions."),
        ("WP-C", "Property, Plant & Equipment (Fixed Assets & Depreciation)", "Fixed Assets", "Verify physical asset register, title deeds, capital additions vouching, and Schedule II depreciation rates."),
        ("WP-D", "Borrowings & Financial Liabilities (Sanction Letters & Terms)", "Liabilities", "Verify loan agreements, hypothecation charges registered on MCA portal, and bank interest calculation."),
        ("WP-E", "Revenue from Operations & Cut-Off Testing", "Revenue", "Perform year-end cut-off vouching across 15 days before/after balance sheet date, credit notes, and GST turnover tie-out."),
        ("WP-F", "Statutory Dues (GST 2B/3B, TDS, PF, ESI Reconciliation)", "Statutory Dues", "Reconcile GSTR-2B eligible ITC against Purchase Register, and verify timely deposit of statutory dues per CARO 2020."),
    ]

    created = []
    with db_manager.session_scope() as session:
        wp_repo = WorkingPaperRepository(session)
        existing = wp_repo.list_for_engagement(engagement_id)
        existing_refs = {w.index_reference for w in existing}

        for ref, title, area, scope_desc in standard_heads:
            if ref in existing_refs:
                continue
            wp = WorkingPaper(
                engagement_id=engagement_id,
                index_reference=ref,
                title=title,
                area=area,
                file_category=FileCategoryEnum.CURRENT_FILE,
                status=WorkingPaperStatusEnum.DRAFT,
                preparer_id=preparer_id,
            )
            saved_wp = wp_repo.add_working_paper(wp)
            for order, s_title, content in [
                (1, "1. Objective & Scope", scope_desc),
                (2, "2. Work Done & Substantive Testing Summary", "Document vouching sample details, ledger extracts, and verification findings."),
                (3, "3. Conclusion & SA 700 Impact", "Auditor conclusion regarding material misstatement."),
            ]:
                wp_repo.add_section(WorkingPaperSection(working_paper_id=saved_wp.id, section_order=order, title=s_title, content_markdown=content))
            created.append(saved_wp)

        if created:
            AuditEventRepository(session).add(
                AuditEvent(
                    engagement_id=engagement_id,
                    actor=preparer_id,
                    action="Schedule III Working Papers Scaffolded",
                    details=f"Auto-generated {len(created)} standard ICAI Schedule III working paper templates.",
                )
            )
    return created
