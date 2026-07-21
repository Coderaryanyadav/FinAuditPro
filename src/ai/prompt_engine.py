class PromptEngine:
    """
    Centralized factory for generating highly engineered, versioned prompts.
    """
    VERSION = "1.0"
    
    SYSTEM_PROMPT = """You are a highly skilled Chartered Accountant and Audit Copilot.
You are tasked with analyzing financial documents and finding anomalies, frauds, and errors.
You must be strictly deterministic, objective, and reference specific accounting standards.
You must NEVER output free conversational text. You must ONLY output a valid JSON object matching the requested schema.
"""

    @classmethod
    def get_system_prompt(cls) -> str:
        return cls.SYSTEM_PROMPT

    @classmethod
    def build_audit_analysis_prompt(cls, document_text: str, schema_template: str) -> str:
        """General audit analysis prompt."""
        return f"""
Analyze the following financial document extract and identify any audit risks, anomalies, or compliance issues.

DOCUMENT:
{document_text}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_risk_assessment_prompt(cls, industry: str, background: str, schema_template: str) -> str:
        """Prompt specifically for planning phase risk assessment."""
        return f"""
Perform a risk assessment for a client in the {industry} industry. 
Background details: {background}

Identify inherent risks, control risks, and suggest audit procedures.
Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""

    @classmethod
    def build_gst_review_prompt(cls, invoice_text: str, schema_template: str) -> str:
        """Prompt specifically for GST invoice validation."""
        return f"""
Review the following invoice for GST compliance. Check for missing GSTINs, incorrect tax rates, or missing mandatory fields.

INVOICE:
{invoice_text}

Strictly return your response as a valid JSON object matching this schema:
{schema_template}
"""
