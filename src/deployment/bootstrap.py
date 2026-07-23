"""
Background AI & System Services Bootstrap Engine for FinAuditPro.
Pre-warms local Ollama LLM services, FAISS vector indexes, OCR engines, and DB connections
in the background on application launch.
"""

import threading
import subprocess
import logging
import os
import time

logger = logging.getLogger(__name__)

class EngineBootstrap:
    """Manages asynchronous background initialization of AI models and tools."""

    _initialized = False

    @classmethod
    def start_background_bootstrap(cls):
        """Spawns background daemon thread to initialize local AI services."""
        if cls._initialized:
            return
        cls._initialized = True
        thread = threading.Thread(target=cls._bootstrap_services, daemon=True, name="AIEngineBootstrap")
        thread.start()
        logger.info("Launched AI Engine Background Bootstrap Thread.")

    @classmethod
    def _bootstrap_services(cls):
        """Background initialization routine."""
        # 1. Pre-warm OCR engine status cache
        try:
            from document_intelligence.ocr_engine import OCREngine
            is_avail, msg = OCREngine.is_ocr_available()
            logger.info(f"Background OCR Engine Bootstrap: {msg}")
        except Exception as e:
            logger.warning(f"Background OCR Pre-warm warning: {e}")

        # 2. Check/Start Ollama LLM Service Daemon
        try:
            import urllib.request
            req = urllib.request.Request("http://localhost:11434/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    logger.info("Background AI Bootstrap: Ollama LLM Daemon is active and responding.")
        except Exception:
            logger.info("Ollama LLM service not responding on localhost:11434. Attempting background spawn...")
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info("Spawned background 'ollama serve' daemon process.")
            except (OSError, FileNotFoundError) as err:
                logger.warning(f"Ollama CLI binary not found in PATH: {err}. AI Assistant will run in rule-fallback mode.")

        # 3. Pre-warm FAISS Vector Store
        try:
            from ai.vector_store import VectorStore
            vs = VectorStore()
            logger.info("Background Vector Store Bootstrap: FAISS RAG index initialized.")
        except Exception as e:
            logger.warning(f"Background Vector Store Pre-warm warning: {e}")

        # 4. Pre-warm Rule Registry
        try:
            from rule_engine.rule_registry import RuleRegistry
            rr = RuleRegistry()
            logger.info(f"Background Rule Engine Bootstrap: Loaded {len(rr.list_rules())} audit rules.")
        except Exception as e:
            logger.warning(f"Background Rule Engine Pre-warm warning: {e}")
