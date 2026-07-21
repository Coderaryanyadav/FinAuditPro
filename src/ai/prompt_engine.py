class PromptEngine:
    """
    Centralized factory for generating highly engineered, versioned prompts.
    """
    VERSION = "2.0"
    
    SYSTEM_PROMPT = """You are a highly skilled Chartered Accountant and Audit Copilot.
You are tasked with analyzing financial documents and finding anomalies, frauds, and errors.
You must be strictly deterministic, objective, and reference specific accounting standards (e.g. SA 240, SA 500, Ind AS).
You must NEVER output free conversational text. You must ONLY output a valid JSON object matching the requested schema.
"""

    @classmethod
    def get_system_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT

    @classmethod
    def build_audit_analysis_prompt(cls, document_text: str, schema_template: str) -> str:
        return f"""
Analyze the following financial document extract and identify any audit risks, anomalies, or compliance issues.

DOCUMENT:
{document_text}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_risk_assessment_prompt(cls, industry: str, background: str, schema_template: str) -> str:
        return f"""
Perform a risk assessment for a client in the {industry} industry. 
Background details: {background}

Identify inherent risks, control risks, and suggest audit procedures.
Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_gst_review_prompt(cls, invoice_text: str, schema_template: str) -> str:
        return f"""
Review the following invoice / GST document for tax compliance. Check for missing GSTINs, incorrect tax rates, or missing mandatory fields.

INVOICE:
{invoice_text}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_compliance_review_prompt(cls, compliance_data: str, schema_template: str) -> str:
        return f"""
Review statutory compliance records against statutory due dates (TDS, GST, Income Tax, ROC).

COMPLIANCE DATA:
{compliance_data}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_working_paper_prompt(cls, audit_area: str, procedure: str, observations: str, schema_template: str) -> str:
        return f"""
Generate an audit working paper summary for Audit Area: {audit_area}.
Procedure Performed: {procedure}
Observations: {observations}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_management_letter_prompt(cls, findings_summary: str, schema_template: str) -> str:
        return f"""
Draft Management Letter recommendations based on the following audit findings.

FINDINGS:
{findings_summary}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_register_review_prompt(cls, register_type: str, register_data: str, schema_template: str) -> str:
        return f"""
Review the {register_type} for unusual transactions, round-sum amounts, or duplicate entries.

REGISTER DATA:
{register_data}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_document_comparison_prompt(cls, doc1_text: str, doc2_text: str, schema_template: str) -> str:
        return f"""
Compare the following two documents and identify variances, mismatches, or discrepancies.

DOCUMENT 1:
{doc1_text}

DOCUMENT 2:
{doc2_text}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

