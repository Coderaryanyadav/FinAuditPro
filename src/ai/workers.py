"""
Async Worker Threads & Runnable Tasks for FinAuditPro AI & RAG Copilot.
Prevents UI event loop blocking during LLM inference, embedding calculation, and document ingestion.
"""

from PySide6.QtCore import QRunnable, QObject, QThread, Signal, Slot
from typing import Dict, Any, Callable
import traceback
import logging
from .ollama_client import OllamaClient, OllamaClientError

logger = logging.getLogger(__name__)

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    """
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)

class AICopilotWorker(QRunnable):
    """
    Worker thread to execute long-running AI Copilot methods 
    without blocking the PySide6 UI.
    """
    def __init__(self, fn: Callable, *args, **kwargs):
        super(AICopilotWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self):
        """Execute the function and emit the appropriate signals."""
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            traceback.print_exc()
            self.signals.error.emit((e, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()

class OllamaWorker(QThread):
    """QThread worker for streaming & synchronous Ollama AI responses."""
    chunk_received = Signal(str)
    finished = Signal()
    error = Signal(str)
    ollama_offline = Signal(str)  # Emitted with the original query when Ollama is unreachable

    def __init__(self, raw_query: str, system_prompt: str = ""):
        super().__init__()
        self.raw_query = raw_query
        self.system_prompt = system_prompt
        self.client = OllamaClient()

    def run(self):
        try:
            # Attempt streaming generation for real-time token rendering
            streamed_any = False
            for chunk in self.client.generate_stream(prompt=self.raw_query, system_prompt=self.system_prompt):
                if chunk:
                    streamed_any = True
                    self.chunk_received.emit(chunk)

            if not streamed_any:
                # Sync fallback
                res = self.client.generate(prompt=self.raw_query, system_prompt=self.system_prompt)
                self.chunk_received.emit(res or "AI Copilot completed analysis with 0 output tokens.")

            self.finished.emit()
        except Exception as e:
            logger.info(f"Ollama offline or unavailable ({e}); switching to Local RAG Analysis Engine.")
            self.ollama_offline.emit(self.raw_query)
            self.finished.emit()

