
import os
import sys
from reportlab.pdfgen import canvas
from document_intelligence.document_pipeline import DocumentPipeline

def test_pdf_ingestion(tmp_path):
    pdf_file = os.path.join(tmp_path, "test_doc.pdf")
    c = canvas.Canvas(pdf_file)
    c.drawString(100, 750, 'This is a test invoice.')
    c.save()
    
    pipeline = DocumentPipeline()
    res = pipeline.process_and_ingest(pdf_file, 1, 1)
    assert res is not None

