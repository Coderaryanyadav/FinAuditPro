import requests
import json
import time
from PySide6.QtCore import QThread, Signal

class OllamaWorker(QThread):
    chunk_received = Signal(str)
    finished = Signal()
    error = Signal(str)

    def __init__(self, raw_query, model="llama3.2"):
        super().__init__()
        self.raw_query = raw_query
        self.model = model

    def run(self):
        try:
            # 1. Fetch RAG Context on background thread
            from ai.rag_pipeline import RAGPipeline
            context = ""
            try:
                rag = RAGPipeline()
                results = rag.search(self.raw_query, top_k=2)
                if results:
                    context = "\n".join([f"Source: {res['source']}\nContent: {res['text']}" for res in results])
            except Exception as e:
                print(f"Background RAG search failed: {e}")
            
            # 2. Formulate Prompt
            if context:
                prompt = f"Use the following document snippet context to answer the question:\n\n{context}\n\nQuestion: {self.raw_query}\nAnswer:"
            else:
                prompt = self.raw_query

            # 3. Connect to Ollama
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                },
                stream=True
            )
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    result = json.loads(decoded_line)
                    if "response" in result:
                        self.chunk_received.emit(result["response"])
            
            self.finished.emit()

        except requests.exceptions.ConnectionError:
            # Mock fallback if Ollama is not installed or running
            mock_response = (
                "⚠️ **Ollama is Offline**\n\n"
                "I see you haven't installed or started Ollama yet. "
                "Since FinAuditPro runs AI completely offline to protect your data, "
                "you need to download Ollama from https://ollama.com and run it locally.\n\n"
                "For your RTX 3060 (4GB) or Mac M4 Pro, I recommend using `llama3.2` as it is highly efficient.\n\n"
                "Once installed, open your terminal and run:\n"
                "`ollama run llama3.2`\n\n"
                "Once it finishes downloading, try sending a message again!"
            )
            for word in mock_response.split(" "):
                self.chunk_received.emit(word + " ")
                time.sleep(0.05) # Simulate typing effect
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()
