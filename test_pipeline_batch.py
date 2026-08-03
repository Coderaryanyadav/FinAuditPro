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
from security.rbac import Permission

import logging
logging.basicConfig(level=logging.DEBUG)

if not QApplication.instance():
    app = QApplication(sys.argv)

def run_test():
    with get_session() as session:
        # Create dummy project
        proj = session.query(AuditProject).first()
        if not proj:
            client = session.query(Client).first()
            if not client:
                client = Client(name="Dummy Client")
                session.add(client)
                session.commit()
            proj = AuditProject(client_id=client.id)
            session.add(proj)
            session.commit()
            
        proj_id = proj.id

        # Make sure we have a session to bypass RBAC
        sm = SecurityManager()
        user = session.query(User).first()
        if not user:
            from security.auth import PasswordHasher
            user = User(username='test', email='test@test.com', password_hash=PasswordHasher.hash_password('test'), role='Partner')
            session.add(user)
            session.commit()
            
        class MockSession:
            def __init__(self, uid, role):
                self.user_id = uid
                self.role = role
        sm.current_session = MockSession(user.id, user.role)

        # Upload files
        repo = DocumentRepository(session)
        service = DocumentService(repo)
        
        files = ['valid1.pdf', 'corrupt.pdf', 'valid2.pdf']
        doc_ids = []
        for file in files:
            path = os.path.abspath(file)
            doc = service.upload_audit_document(audit_id=proj_id, file_path=path, doc_type="Uploaded")
            doc_ids.append(doc.id)
            
        print("Documents uploaded with IDs:", doc_ids)
        
    # Run the AI Processing Thread
    worker = AIProcessWorker(doc_ids)
    
    def on_finished(failures):
        print("\n=== PROCESSING FINISHED ===")
        print("Failures returned by signal:", failures)
        
        with get_session() as s:
            for doc_id in doc_ids:
                doc = s.query(Document).filter_by(id=doc_id).first()
                print(f"Document {doc.file_name}: status={doc.doc_type}, error={doc.error_message}")
        
        QApplication.quit()
        
    def on_progress(msg, pct):
        print(f"[{pct}%] {msg}")

    worker.finished.connect(on_finished)
    worker.progress.connect(on_progress)
    worker.start()
    
    QApplication.instance().exec()

if __name__ == "__main__":
    run_test()
