import os
import json
import numpy as np

# We import these conditionally or lazily if we want to avoid slow startup,
# but since this is a dedicated backend module, standard imports are fine.
import pdfplumber
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer

class RAGPipeline:
    def __init__(self, db_path="data/vector_db"):
        self.db_path = db_path
        os.makedirs(self.db_path, exist_ok=True)
        
        self.index_file = os.path.join(self.db_path, "faiss_index.bin")
        self.metadata_file = os.path.join(self.db_path, "metadata.json")
        
        # Load a small, fast offline embedding model suitable for CPUs and 4GB VRAM
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS Index (L2 distance)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        
        self._load_db()

    def _load_db(self):
        """Loads the FAISS index and metadata if they exist."""
        if os.path.exists(self.index_file):
            self.index = faiss.read_index(self.index_file)
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, "r") as f:
                self.metadata = json.load(f)

    def _save_db(self):
        """Saves the FAISS index and metadata to disk."""
        faiss.write_index(self.index, self.index_file)
        with open(self.metadata_file, "w") as f:
            json.dump(self.metadata, f)

    def extract_text(self, file_path):
        """Extracts text based on file extension."""
        ext = file_path.lower().split('.')[-1]
        text = ""
        
        if ext == "pdf":
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                print(f"Error parsing PDF: {e}")
                
        elif ext in ["xlsx", "xls", "csv"]:
            try:
                if ext == "csv":
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                text = df.to_string()
            except Exception as e:
                print(f"Error parsing spreadsheet: {e}")
                
        return text

    def chunk_text(self, text, chunk_size=500, overlap=50):
        """Splits long text into overlapping chunks."""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def ingest_document(self, file_path, source_name):
        """Extracts, chunks, embeds, and stores a document."""
        print(f"Ingesting {source_name}...")
        text = self.extract_text(file_path)
        if not text.strip():
            print("No text found.")
            return False
            
        chunks = self.chunk_text(text)
        if not chunks:
            return False
            
        # Generate embeddings
        embeddings = self.embedding_model.encode(chunks)
        
        # Add to FAISS index
        self.index.add(np.array(embeddings, dtype=np.float32))
        
        # Store metadata
        for chunk in chunks:
            self.metadata.append({
                "source": source_name,
                "text": chunk
            })
            
        self._save_db()
        return True

    def search(self, query, top_k=3):
        """Searches the vector database for relevant chunks."""
        if self.index.ntotal == 0:
            return []
            
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.metadata):
                results.append({
                    "score": float(distances[0][i]),
                    "source": self.metadata[idx]["source"],
                    "text": self.metadata[idx]["text"]
                })
                
        return results
