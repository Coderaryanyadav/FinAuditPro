from PySide6.QtCore import QRunnable, QObject, QThread, Signal, Slot
from typing import Dict, Any, Callable
import traceback
from .ollama_client import OllamaClient


class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals:
    - finished: No data
    - error: tuple (Exception, traceback_str)
    - result: object data returned from processing
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
    """QThread worker for streaming Ollama responses."""
    chunk_received = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, raw_query: str, system_prompt: str = ""):
        super().__init__()
        self.raw_query = raw_query
        self.system_prompt = system_prompt
        self.client = OllamaClient()

    def run(self):
        try:
            response = self.client.generate_response(
                prompt=self.raw_query,
                system_prompt=self.system_prompt
            )
            self.chunk_received.emit(response)
            self.finished.emit()
        except Exception as e:
            traceback.print_exc()
            self.error.emit(f"{str(e)}\n{traceback.format_exc()}")
