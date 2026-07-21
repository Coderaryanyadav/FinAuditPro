import os
import shutil
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QFileDialog, QListWidget, 
                               QProgressBar, QComboBox, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from database.database import SessionLocal
from database.models import Client, AuditProject, Document
from .styles import apply_shadow

# class AIProcessWorker... (Skipping class code since we edit widget __init__)


class AIProcessWorker(QThread):
    progress = Signal(str, int)  # status message, percentage
    finished = Signal(bool)

    def __init__(self, document_ids):
        super().__init__()
        self.document_ids = document_ids

    def run(self):
        session = SessionLocal()
        try:
            from document_intelligence.document_pipeline import DocumentPipeline
            pipeline = DocumentPipeline()
            total = len(self.document_ids)
            for i, doc_id in enumerate(self.document_ids):
                doc = session.query(Document).filter_by(id=doc_id).first()
                if not doc: continue
                
                def progress_cb(stage_name, pct):
                    overall_pct = int((i / total) * 100 + (pct / total))
                    self.progress.emit(f"Ingesting {doc.file_name} ({stage_name})...", overall_pct)
                
                result = pipeline.process_and_ingest(
                    file_path=doc.file_path,
                    engagement_id=doc.audit_id,
                    client_id=doc.audit_id,
                    document_id=doc.id,
                    progress_callback=progress_cb
                )
                
                if result and result.status == "SUCCESS":
                    doc.doc_type = "Ingested"
                    session.commit()
                else:
                    doc.doc_type = "Failed"
                    session.commit()
            
            self.progress.emit("AI Processing Complete", 100)
            self.finished.emit(True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Document Ingestion Error")
            self.finished.emit(False)
        finally:
            session.close()

class DocumentUploadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f1f5f9;")
        self.session = SessionLocal()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Action Bar
        action_bar = QFrame()
        action_bar.setFixedHeight(80)
        action_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e2e8f0;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 0, 24, 0)
        
        title = QLabel("Upload Documents")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        action_layout.addWidget(title)
        
        # Dropdown to select Client/Audit Project
        action_layout.addSpacing(40)
        proj_label = QLabel("Audit Project:")
        proj_label.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold;")
        action_layout.addWidget(proj_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setFixedWidth(280)
        self.project_combo.setStyleSheet("""
            QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; background-color: #ffffff; color: #0f172a; }
        """)
        self.project_combo.currentIndexChanged.connect(self.load_uploaded_files)
        action_layout.addWidget(self.project_combo)
        
        action_layout.addStretch()
        main_layout.addWidget(action_bar)
        
        # OCR Graceful Feature Detection Banner
        try:
            from document_intelligence.ocr_engine import OCREngine
            ocr_ok, ocr_msg = OCREngine.is_ocr_available()
            if not ocr_ok:
                ocr_banner = QFrame()
                ocr_banner.setStyleSheet("background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 8px; margin: 10px 40px 0 40px;")
                b_layout = QHBoxLayout(ocr_banner)
                b_layout.setContentsMargins(16, 8, 16, 8)
                warn_lbl = QLabel(f"⚠️ {ocr_msg}")
                warn_lbl.setStyleSheet("color: #92400e; font-size: 13px; font-weight: 500; border: none; background: transparent;")
                b_layout.addWidget(warn_lbl)
                main_layout.addWidget(ocr_banner)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"OCR Banner initialization exception: {e}")
        
        # Content
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(24)
        
        # Upload Area
        self.upload_area = QFrame()
        self.upload_area.setStyleSheet("""
            QFrame { background-color: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 12px; }
        """)
        self.upload_area.setFixedHeight(220)
        upload_layout = QVBoxLayout(self.upload_area)
        upload_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel("📄")
        icon_lbl.setStyleSheet("font-size: 48px; border: none; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc_lbl = QLabel("Drag & drop financial documents here\nor click to browse (PDF, Excel, Images)")
        desc_lbl.setStyleSheet("color: #64748b; font-size: 14px; text-align: center; border: none; background: transparent;")
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.btn_browse = QPushButton("Browse Files")
        self.btn_browse.setFixedWidth(150)
        self.btn_browse.setStyleSheet("""
            QPushButton { padding: 10px; border: none; border-radius: 6px; background-color: #0ea5e9; color: white; font-weight: bold; }
            QPushButton:hover { background-color: #0284c7; }
        """)
        self.btn_browse.clicked.connect(self.browse_files)
        
        upload_layout.addWidget(icon_lbl)
        upload_layout.addWidget(desc_lbl)
        upload_layout.addSpacing(12)
        upload_layout.addWidget(self.btn_browse, alignment=Qt.AlignmentFlag.AlignCenter)
        
        content_layout.addWidget(self.upload_area)
        
        # Progress & File List
        list_lbl = QLabel("Uploaded Files Queue:")
        list_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0f172a;")
        content_layout.addWidget(list_lbl)
        
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget { background-color: white; border: 1px solid #e2e8f0; border-radius: 8px; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
        """)
        content_layout.addWidget(self.file_list)
        
        # Progress Bar for AI Process
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #cbd5e1; border-radius: 6px; text-align: center; background-color: #e2e8f0; }
            QProgressBar::chunk { background-color: #10b981; }
        """)
        content_layout.addWidget(self.progress_bar)
        
        self.btn_process = QPushButton("Process Documents with AI")
        self.btn_process.setFixedHeight(45)
        self.btn_process.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; font-weight: bold; font-size: 14px; border-radius: 8px; }
            QPushButton:hover { background-color: #059669; }
        """)
        self.btn_process.clicked.connect(self.start_ai_processing)
        content_layout.addWidget(self.btn_process)
        
        main_layout.addLayout(content_layout)
        
        self.load_audit_projects()
        
    def load_audit_projects(self):
        self.project_combo.clear()
        projects = self.session.query(AuditProject).all()
        for proj in projects:
            client = self.session.query(Client).filter_by(id=proj.client_id).first()
            name = client.name if client else "Unknown Client"
            display_text = f"{name} ({proj.financial_year})"
            self.project_combo.addItem(display_text, proj.id)
            
    def load_uploaded_files(self):
        self.file_list.clear()
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        
        docs = self.session.query(Document).filter_by(audit_id=proj_id).all()
        for doc in docs:
            status_icon = "🟢" if doc.doc_type == "Ingested" else "⏳"
            self.file_list.addItem(f"{status_icon} {doc.file_name} (Status: {doc.doc_type or 'Uploaded'})")

    def browse_files(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.UPLOAD_DOCUMENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to upload documents.")
            return

        proj_id = self.project_combo.currentData()
        if proj_id is None:
            QMessageBox.warning(self, "No Project Selected", "Please select or create an audit project first.")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Financial Documents",
            "",
            "Documents (*.pdf *.xls *.xlsx *.csv)"
        )
        if files:
            dest_dir = f"data/documents/proj_{proj_id}"
            os.makedirs(dest_dir, exist_ok=True)
            
            for file_path in files:
                filename = os.path.basename(file_path)
                dest_path = os.path.join(dest_dir, filename)
                
                # Check for naming collisions and append timestamp to avoid overwriting
                if os.path.exists(dest_path):
                    import time
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{int(time.time())}{ext}"
                    dest_path = os.path.join(dest_dir, filename)
                
                # Copy file locally
                shutil.copy(file_path, dest_path)
                
                # Save to database
                doc = Document(
                    audit_id=proj_id,
                    file_path=dest_path,
                    file_name=filename,
                    doc_type="Uploaded"
                )
                self.session.add(doc)
                self.session.commit()
                
            self.load_uploaded_files()

    def start_ai_processing(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        
        # Get all non-ingested docs
        docs = self.session.query(Document).filter_by(audit_id=proj_id).filter(Document.doc_type != "Ingested").all()
        if not docs:
            QMessageBox.information(self, "Up to Date", "All documents in this project are already processed!")
            return
            
        doc_ids = [d.id for d in docs]
        
        self.progress_bar.setVisible(True)
        self.btn_process.setEnabled(False)
        
        self.worker = AIProcessWorker(doc_ids)
        self.worker.progress.connect(self.on_process_progress)
        self.worker.finished.connect(self.on_process_finished)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_process_progress(self, msg, pct):
        self.progress_bar.setValue(pct)
        self.progress_bar.setFormat(f"{msg} ({pct}%)")

    def on_process_finished(self, success):
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        self.load_uploaded_files()
        if success:
            QMessageBox.information(self, "Processing Complete", "AI Document Ingestion Completed Successfully!")
        else:
            QMessageBox.critical(self, "Error", "AI Document Ingestion Failed.")

    def delete_selected_document(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.DELETE_DOCUMENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to delete documents.")
            return

        item = self.file_list.currentItem()
        if not item: return
        self.file_list.takeItem(self.file_list.row(item))

    def closeEvent(self, event):
        self.session.close()
        event.accept()
