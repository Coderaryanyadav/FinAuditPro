import time
from typing import Dict, Any, List
from .ollama_client import OllamaClient
from .prompt_engine import PromptEngine
from .context_retriever import ContextRetriever
from .response_parser import ResponseParser
from .json_schema import AuditFindingSchema

class AuditCopilot:
    """
    The main Facade for the AI Engine.
    Orchestrates Context Retrieval -> Prompt Engine -> Ollama -> Response Parser.
    Never talks directly to the UI.
    """

    def __init__(self, context_retriever: ContextRetriever, ollama_client: OllamaClient = None):
        self.context_retriever = context_retriever
        self.ollama = ollama_client or OllamaClient()
        self.prompt_engine = PromptEngine()
        self.schema_template = AuditFindingSchema.schema_json()

    def _execute_analysis(self, prompt: str, engagement_id: int, client_id: int = None, k: int = 5) -> Dict[str, Any]:
        """Core execution pipeline."""
        start_time = time.time()

        # 1. Retrieve Context safely
        context = self.context_retriever.retrieve_context(prompt, engagement_id, client_id, k)

        # 2. Build full prompt
        system_prompt = self.prompt_engine.get_system_prompt()
        full_prompt = f"CONTEXT:\n{context}\n\nTASK:\n{prompt}"

        # 3. Generate raw response
        raw_response = self.ollama.generate(full_prompt, system_prompt=system_prompt)

        # 4. Parse, repair, and validate JSON
        result = ResponseParser.parse_audit_finding(raw_response)

        result["processing_time"] = round(time.time() - start_time, 2)
        return result

    def analyze_document(self, document_text: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_audit_analysis_prompt(document_text, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def compare_documents(self, doc1_text: str, doc2_text: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_document_comparison_prompt(doc1_text, doc2_text, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def detect_risks(self, industry: str, background: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_risk_assessment_prompt(industry, background, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def generate_findings(self, data_summary: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_audit_analysis_prompt(data_summary, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def review_working_papers(self, audit_area: str, procedure: str, observations: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_working_paper_prompt(audit_area, procedure, observations, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def generate_management_letter(self, findings_summary: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_management_letter_prompt(findings_summary, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def explain_gst_difference(self, invoice_text: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_gst_review_prompt(invoice_text, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def review_trial_balance(self, tb_data: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_register_review_prompt("Trial Balance", tb_data, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def review_bank_statement(self, bank_data: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_register_review_prompt("Bank Statement", bank_data, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def review_purchase_register(self, purchase_data: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_register_review_prompt("Purchase Register", purchase_data, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def review_sales_register(self, sales_data: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_register_review_prompt("Sales Register", sales_data, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

