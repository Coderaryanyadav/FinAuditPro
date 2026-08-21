import sys
import os
sys.path.append('src')

from database.database import get_session
from database.models import User, Client, Engagement, Document, AuditProject
from services.document_service import DocumentService
from database.repositories.document_repo import DocumentRepository
from ui.documents import AIProcessWorker
from PySide6.QtWidgets import QApplication
from security.security_manager import SecurityManager
import logging
logging.basicConfig(level=logging.DEBUG)

def run_worker_test():
    if not QApplication.instance():
        app = QApplication(sys.argv)

    with get_session() as session:
        proj = session.query(AuditProject).first()
        if not proj:
            return
        proj_id = proj.id

        sm = SecurityManager()
        user = session.query(User).first()
        if not user:
            return
        class MockSession:
            def __init__(self, uid, role):
                self.user_id = uid
                self.role = role
        sm.current_session = MockSession(user.id, user.role)

        repo = DocumentRepository(session)
        service = DocumentService(repo)
        
        files = ['valid1.pdf', 'corrupt.pdf', 'valid2.pdf']
        doc_ids = []
        for file in files:
            path = os.path.abspath(file)
            if os.path.exists(path):
                doc = service.upload_audit_document(audit_id=proj_id, file_path=path, doc_type="Uploaded")
                doc_ids.append(doc.id)
            
        print("Documents uploaded with IDs:", doc_ids)

    if doc_ids:
        worker = AIProcessWorker(doc_ids)
        def on_finished(failures):
            print("\n=== PROCESSING FINISHED ===")
            print("Failures:", failures)
            with get_session() as s:
                for doc_id in doc_ids:
                    d = s.query(Document).filter_by(id=doc_id).first()
                    if d:
                        print(f"{d.file_name}: {d.doc_type} | {d.error_message}")
            if QApplication.instance():
                QApplication.quit()

        worker.finished.connect(on_finished)
        worker.run()

if __name__ == '__main__':
    run_worker_test()

