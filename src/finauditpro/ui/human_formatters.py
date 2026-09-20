"""Human-friendly display formatters for FinAuditPro entities and audit concepts."""




def format_engagement_display(
    financial_year: str | None,
    audit_type: str | None,
    client_name: str | None = None,
) -> str:
    """Format engagement identifiers into human-friendly auditor terminology."""
    fy_str = financial_year or "FY 2025-26"
    type_str = audit_type or "Statutory Audit"
    if client_name:
        return f"{client_name} — {fy_str} ({type_str})"
    return f"{fy_str} / {type_str}"


def format_client_display(name: str, pan: str | None = None, entity_type: str | None = None) -> str:
    """Format client entity into human-friendly label."""
    bits = [name]
    if entity_type:
        bits.append(f"({entity_type})")
    if pan:
        bits.append(f"PAN: {pan}")
    return " ".join(bits)


def format_document_display(filename: str, category: str | None = None) -> str:
    """Format document file record for clean presentation."""
    if category and category != "Unclassified":
        return f"[{category}] {filename}"
    return filename


def format_task_display(title: str, priority: str = "MEDIUM", due_at: str | None = None) -> str:
    """Format work task label with priority indicator."""
    p_tag = f"[{priority.upper()}]" if priority else ""
    due_tag = f" (Due: {due_at})" if due_at else ""
    return f"{p_tag} {title}{due_tag}".strip()


def format_finding_display(title: str, severity: str = "Medium", category: str | None = None) -> str:
    """Format audit finding label for human consumption."""
    s_tag = f"[{severity.upper()}]"
    c_tag = f" ({category})" if category else ""
    return f"{s_tag} {title}{c_tag}"
