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

    def detect_risks(self, industry: str, background: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_risk_assessment_prompt(industry, background, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)

    def explain_gst_difference(self, invoice_text: str, engagement_id: int) -> Dict[str, Any]:
        prompt = self.prompt_engine.build_gst_review_prompt(invoice_text, self.schema_template)
        return self._execute_analysis(prompt, engagement_id)
