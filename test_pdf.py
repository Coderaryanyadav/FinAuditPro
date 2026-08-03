
import sys; sys.path.append('src')
from reportlab.pdfgen import canvas
c = canvas.Canvas('test_doc.pdf')
c.drawString(100, 750, 'This is a test invoice.')
c.save()
print('PDF created.')
from document_intelligence.document_pipeline import DocumentPipeline
pipeline = DocumentPipeline()
try:
    res = pipeline.process_and_ingest('test_doc.pdf', 1, 1)
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()

