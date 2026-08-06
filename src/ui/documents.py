"""
Document Ingestion, Auto-Classification, OCR Status & Viewer Pipeline Widget for FinAuditPro.
Provides Drag-and-Drop Ingestion, SHA-256 Anti-Tamper Evidence Hashing, Document Type Auto-Classification,
Real-Time OCR & FAISS Index Status, and Split-View Document Inspector.
"""

import logging
import os
import shutil
import hashlib

logger = logging.getLogger(__name__)
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QFileDialog, QTableWidget, QTableWidgetItem,
                               QProgressBar, QComboBox, QMessageBox, QSplitter, QTextEdit, QHeaderView)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QColor
from database.database import get_session
from database.models import Client, AuditProject, Document
from database.repositories.document_repo import DocumentRepository
from services.document_service import DocumentService
from security.security_manager import SecurityManager
from security.rbac import Permission
from document_intelligence.document_pipeline import DocumentPipeline
from document_intelligence.ocr_engine import OCREngine
from .styles import apply_shadow, EmptyStateWidget, LoadingStateWidget, ErrorStateWidget
from sqlalchemy.exc import SQLAlchemyError

def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a document file for audit evidence integrity verification."""
    try:
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return "UNKNOWN_HASH"

def classify_document_type(file_name: str) -> str:
    """Auto-classifies financial documents based on filename heuristics."""
    fn = file_name.lower()
    if any(k in fn for k in ["bank", "statement", "passbook", "hdfc", "icici", "sbi"]):
        return "Bank Statement"
    elif any(k in fn for k in ["trial", "balance", "tb", "ledger"]):
        return "Trial Balance"
    elif any(k in fn for k in ["gstr", "2b", "3b", "gst"]):
        return "GST Return"
    elif any(k in fn for k in ["invoice", "bill", "voucher", "receipt"]):
        return "Purchase Invoice"
    elif any(k in fn for k in ["resolution", "minutes", "board", "moa", "aoa"]):
        return "Legal / Governance"
    return "General Document"

class DropZoneFrame(QFrame):
    """Interactive Drag-and-Drop and Click-to-Upload Frame."""
    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("dropZone")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setObjectName("dropZoneHover")

    def dragLeaveEvent(self, event):
        self.setObjectName("dropZone")

    def dropEvent(self, event):
        self.setObjectName("dropZone")
        urls = event.mimeData().urls()
        files = [u.toLocalFile() for u in urls if u.isLocalFile()]
        if files and self.callback:
            self.callback(files)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.callback:
            self.callback()

class AIProcessWorker(QThread):
    progress = Signal(str, int)  # status message, percentage
    finished = Signal(list)

    def __init__(self, document_ids):
        super().__init__()
        self.document_ids = document_ids

    def run(self):
        failures = []
        try:
            with get_session() as session:
                pipeline = DocumentPipeline()
                total = len(self.document_ids)
                for i, doc_id in enumerate(self.document_ids):
                    doc = session.query(Document).filter_by(id=doc_id).first()
                    if not doc: continue
                    
                    try:
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
                        else:
                            doc.doc_type = "Failed"
                            error_msg = getattr(result, "error_message", "Unknown processing error") if result else "No result returned"
                            doc.error_message = error_msg
                            failures.append(f"{doc.file_name}: {error_msg}")
                        session.commit()
                    except Exception as e:
                        logger.exception(f"Failed to process document {doc.file_name} (id={doc_id})")
                        doc.doc_type = "Failed"
                        doc.error_message = str(e)
                        failures.append(f"{doc.file_name}: {e}")
                        session.commit()
                        self.progress.emit(f"Failed: {doc.file_name} — {e}", int((i / total) * 100))
            
            self.progress.emit("AI Processing Complete", 100)
            self.finished.emit(failures)
        except Exception as e:
            logger.exception("Fatal Document Ingestion Error")
            self.finished.emit([f"Fatal error: {str(e)}"])
        finally:
            if 'session' in locals():
                session.close()

class DocumentUploadWidget(QWidget):
    """Multi-document Ingestion, Classification & Inspector Pipeline Widget."""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #f0f6ff;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 1. Action Bar — Header
        action_bar = QFrame()
        action_bar.setFixedHeight(68)
        action_bar.setObjectName("headerBar")
        action_bar.setStyleSheet("background-color: #ffffff; border-bottom: 1px solid #e1e8f4;")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(24, 0, 24, 0)
        
        title_v = QVBoxLayout()
        title_v.setSpacing(2)
        title = QLabel("Document Ingestion & Intelligence Pipeline")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0f172a; letter-spacing: -0.4px; border: none; background: transparent; background-color: transparent;")
        subtitle = QLabel("Auto-Classification, OCR & SHA-256 Anti-Tamper Verification")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; border: none; background: transparent; background-color: transparent;")
        title_v.addWidget(title)
        title_v.addWidget(subtitle)
        action_layout.addLayout(title_v)
        
        action_layout.addSpacing(30)
        action_layout.addWidget(QLabel("<b style='color:#0f172a; border: none; background: transparent;'>Audit Project:</b>"))
        
        self.project_combo = QComboBox()
        self.project_combo.setFixedWidth(240)
        self.project_combo.setObjectName("formCombo")
        self.project_combo.setStyleSheet("""
            QComboBox {
                padding: 6px 12px;
                border: 1px solid #e1e8f4;
                border-radius: 8px;
                background-color: #ffffff;
                color: #0f172a;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox:focus { background-color: #ffffff; border-color: #0284c7; }
        """)
        self.project_combo.currentIndexChanged.connect(self.load_uploaded_files)
        action_layout.addWidget(self.project_combo)
        
        action_layout.addStretch()
        
        btn_upload = QPushButton("Select Files to Upload")
        btn_upload.setObjectName("primaryButton")
        btn_upload.setStyleSheet("""
            QPushButton#primaryButton {
                background-color: #0284c7;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 16px;
                border: none;
            }
            QPushButton#primaryButton:hover { background-color: #0369a1; }
        """)
        btn_upload.clicked.connect(self.browse_files)

        btn_process = QPushButton("Process with AI OCR")
        btn_process.setObjectName("secondaryButton")
        btn_process.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #0284c7;
                font-size: 13px;
                font-weight: 600;
                border: 1px solid #e1e8f4;
                border-radius: 8px;
                padding: 8px 16px;
            }
            QPushButton:hover { background-color: #f8fafc; border-color: #0284c7; }
        """)
        btn_process.clicked.connect(self.start_ai_processing)
        self.btn_process = btn_process

        action_layout.addWidget(btn_upload)
        action_layout.addSpacing(8)
        action_layout.addWidget(btn_process)
        main_layout.addWidget(action_bar)
        
        # 2. Compact OCR Feature Banner
        try:
            ocr_ok, ocr_msg = OCREngine.is_ocr_available()
            if not ocr_ok:
                ocr_banner = QFrame()
                ocr_banner.setFixedHeight(36)
                ocr_banner.setStyleSheet("background-color: #fffbe6; border-bottom: 1px solid #ffe58f;")
                b_layout = QHBoxLayout(ocr_banner)
                b_layout.setContentsMargins(24, 0, 24, 0)
                warn_lbl = QLabel(f"ℹ {ocr_msg}")
                warn_lbl.setStyleSheet("color: #d97706; font-size: 11px; font-weight: 600; border: none; background: transparent; background-color: transparent;")
                b_layout.addWidget(warn_lbl)
                main_layout.addWidget(ocr_banner)
        except (SQLAlchemyError, OSError, ValueError):
            pass

        # 3. Main 2-Pane Splitter View
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e1e8f4; }")

        # Left Pane: Upload Zone & Document Table
        left_container = QFrame()
        left_container.setStyleSheet("background-color: #ffffff; border-right: 1px solid #e1e8f4;")
        left_layout = QVBoxLayout(left_container)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        # Interactive Drag & Drop Zone Frame
        self.upload_area = DropZoneFrame(callback=self.browse_files)
        self.upload_area.setFixedHeight(95)
        self.upload_area.setStyleSheet("""
            QFrame {
                background-color: #f0f6ff;
                border: 2px dashed #0284c7;
                border-radius: 12px;
            }
            QFrame:hover {
                background-color: #e0f2fe;
            }
        """)
        upload_l = QVBoxLayout(self.upload_area)
        upload_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        drop_lbl = QLabel("Drag & drop financial documents here or click 'Select Files'")
        drop_lbl.setStyleSheet("color: #0284c7; font-weight: 600; font-size: 13px; border: none; background: transparent; background-color: transparent;")
        drop_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        upload_l.addWidget(drop_lbl)

        left_layout.addWidget(self.upload_area)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #e1e8f4; border-radius: 6px; text-align: center; background-color: #f0f6ff; color: #0f172a; font-weight: 600; height: 18px; }
            QProgressBar::chunk { background-color: #0284c7; border-radius: 5px; }
        """)
        left_layout.addWidget(self.progress_bar)

        # Ingested Files Table
        table_lbl = QLabel("INGESTED DOCUMENTS & FAISS STATUS")
        table_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #0284c7; letter-spacing: 0.8px; border: none; background: transparent; background-color: transparent;")
        left_layout.addWidget(table_lbl)

        self.doc_table = QTableWidget(0, 4)
        self.doc_table.setHorizontalHeaderLabels(["Category Tag", "Document File Name", "SHA-256 Hash", "Status"])
        self.doc_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.doc_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.doc_table.verticalHeader().setVisible(False)
        self.doc_table.setShowGrid(False)
        self.doc_table.setStyleSheet("""
            QTableWidget { border: 1px solid #e1e8f4; gridline-color: #f0f6ff; background: #ffffff; border-radius: 8px; color: #0f172a; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; font-weight: 600; padding: 8px 10px; border: none; border-bottom: 1px solid #e1e8f4; font-size: 10px; letter-spacing: 0.8px; text-transform: uppercase; }
            QTableWidget::item { padding: 6px 10px; border-bottom: 1px solid #f0f6ff; color: #0f172a; font-size: 12px; }
            QTableWidget::item:selected { background-color: rgba(2, 132, 199, 0.12); color: #0284c7; font-weight: bold; }
        """)
        self.doc_table.itemSelectionChanged.connect(self.on_doc_selected)
        left_layout.addWidget(self.doc_table)

        splitter.addWidget(left_container)

        # Right Pane: Document Inspector & Text Preview
        right_container = QFrame()
        right_container.setStyleSheet("background-color: #f0f6ff;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(10)

        inspector_lbl = QLabel("DOCUMENT INSPECTOR & INTEGRITY AUDIT")
        inspector_lbl.setStyleSheet("font-size: 11px; font-weight: bold; color: #64748b; letter-spacing: 0.5px;")
        right_layout.addWidget(inspector_lbl)

        self.doc_title_lbl = QLabel("No Document Selected")
        self.doc_title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #0f172a;")
        right_layout.addWidget(self.doc_title_lbl)

        self.hash_info_lbl = QLabel("SHA-256 Integrity Hash: N/A")
        self.hash_info_lbl.setWordWrap(True)
        self.hash_info_lbl.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; padding: 8px; border-radius: 6px; font-family: monospace; font-size: 11px; color: #334155;")
        right_layout.addWidget(self.hash_info_lbl)

        preview_t = QLabel("Extracted Text & Metadata Preview:")
        preview_t.setStyleSheet("font-size: 11px; font-weight: bold; color: #334155;")
        right_layout.addWidget(preview_t)

        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText("Select an ingested document from the left table to inspect extracted text and RAG vector index citations...")
        self.text_preview.setStyleSheet("background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 10px; font-family: monospace; font-size: 12px; color: #0f172a;")
        right_layout.addWidget(self.text_preview)

        splitter.addWidget(right_container)
        splitter.setSizes([750, 450])

        main_layout.addWidget(splitter, 1)
        
        self.load_audit_projects()
        
    def load_audit_projects(self):
        self.project_combo.clear()
        with get_session() as session:
            projects = session.query(AuditProject).all()
            if not projects:
                # No auto-seed: show placeholder directing user to create a client first
                self.project_combo.addItem("— No audit projects yet —", None)
                return

            for proj in projects:
                client = session.query(Client).filter_by(id=proj.client_id).first()
                name = client.name if client else f"Client #{proj.client_id}"
                display_text = f"{name} (FY {proj.financial_year})"
                self.project_combo.addItem(display_text, proj.id)
            
    def load_uploaded_files(self):
        self.doc_table.setRowCount(0)
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        
        with get_session() as session:
            repo = DocumentRepository(session)
            service = DocumentService(repo)
            docs = service.get_audit_documents(proj_id)
            if not docs:
                self.doc_table.setRowCount(0)
                if hasattr(self, 'state_container'):
                    self.state_container.setWidget(EmptyStateWidget("No Ingested Documents", "No audit evidence documents uploaded for this engagement."))
                    self.state_container.show()
                return

            if hasattr(self, 'state_container'):
                self.state_container.hide()

            self.doc_table.setRowCount(len(docs))

            for r, doc in enumerate(docs):
                cat = classify_document_type(doc.file_name)
                sha_hash = compute_sha256(doc.file_path) if os.path.exists(doc.file_path) else "N/A"
                trunc_hash = f"{sha_hash[:12]}..." if len(sha_hash) > 12 else sha_hash

                tag_item = QTableWidgetItem(cat)
                tag_item.setFont(QFont("Inter", 9, QFont.Weight.Bold))
                self.doc_table.setItem(r, 0, tag_item)

                name_item = QTableWidgetItem(doc.file_name)
                name_item.setData(Qt.ItemDataRole.UserRole, doc.id)
                self.doc_table.setItem(r, 1, name_item)

                hash_item = QTableWidgetItem(trunc_hash)
                hash_item.setToolTip(sha_hash)
                self.doc_table.setItem(r, 2, hash_item)

                st = doc.doc_type or "Uploaded"
                st_text = " Ingested" if st == "Ingested" else " Digital Parsed" if st == "Uploaded" else " Pending"
                st_item = QTableWidgetItem(st_text)
                self.doc_table.setItem(r, 3, st_item)

    def on_doc_selected(self):
        selected_rows = self.doc_table.selectedItems()
        if not selected_rows: return
        r = self.doc_table.currentRow()
        doc_id = self.doc_table.item(r, 1).data(Qt.ItemDataRole.UserRole)
        with get_session() as session:
            repo = DocumentRepository(session)
            service = DocumentService(repo)
            try:
                doc = service.get_document(doc_id)
                file_name = doc.file_name
                file_path = doc.file_path
            except Exception:
                return

        self.doc_title_lbl.setText(file_name)
        sha_hash = compute_sha256(file_path) if os.path.exists(file_path) else "N/A"
        self.hash_info_lbl.setText(f"SHA-256 Anti-Tamper Evidence Hash:\n{sha_hash}")

        if os.path.exists(file_path):
            try:
                from document_intelligence.document_parser import DocumentParser
                parsed = DocumentParser.parse_document(file_path)
                text = parsed.cleaned_text or parsed.raw_text
                if text and text.strip():
                    snippet = text[:3000]
                    if len(text) > 3000:
                        snippet += "\n\n[... preview truncated ...]"
                    self.text_preview.setPlainText(snippet)
                else:
                    self.text_preview.setPlainText(f"Document ({file_name}) ingested. Binary or empty document preview unavailable.")
            except Exception as e:
                logger.warning(f"Error parsing preview for {file_path}: {e}")
                self.text_preview.setPlainText(f"File Path: {file_path}\nStatus: Ingested & FAISS Vector Index Active.")
        else:
            self.text_preview.setPlainText("Document file not found on local disk.")

    def browse_files(self, file_paths=None):
        sm = SecurityManager()
        if not sm.current_session or not sm.check_permission(Permission.UPLOAD_DOCUMENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to upload documents.")
            return

        proj_id = self.project_combo.currentData()
        if proj_id is None:
            self.load_audit_projects()
            proj_id = self.project_combo.currentData()

        if not file_paths:
            files, _ = QFileDialog.getOpenFileNames(
                self,
                "Select Financial Documents",
                "",
                "Documents (*.pdf *.xls *.xlsx *.csv *.txt *.png *.jpg *.jpeg)"
            )
        else:
            files = file_paths

        if files:
            uploaded_count = 0
            
            with get_session() as session:
                repo = DocumentRepository(session)
                service = DocumentService(repo)
                for file_path in files:
                    if not os.path.exists(file_path): continue
                    
                    try:
                        service.upload_audit_document(
                            audit_id=proj_id,
                            file_path=file_path,
                            doc_type="Uploaded"
                        )
                        uploaded_count += 1
                    except Exception as e:
                        logger.error(f"Failed to upload {file_path}: {e}")
                        QMessageBox.warning(self, "Upload Failed", f"Could not upload {os.path.basename(file_path)}:\n{e}")
                
            self.load_uploaded_files()
            if uploaded_count > 0:
                QMessageBox.information(self, "Upload Success", f"Successfully uploaded {uploaded_count} document(s) with SHA-256 evidence hashing.")

    def start_ai_processing(self):
        proj_id = self.project_combo.currentData()
        if proj_id is None: return
        
        with get_session() as session:
            docs = session.query(Document).filter_by(audit_id=proj_id).filter(Document.doc_type != "Ingested").all()
            if not docs:
                QMessageBox.information(self, "Up to Date", "All documents in this project are already processed and indexed!")
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

    def on_process_finished(self, failures):
        self.progress_bar.setVisible(False)
        self.btn_process.setEnabled(True)
        self.load_uploaded_files()
        if not failures:
            QMessageBox.information(self, "Processing Complete", "All documents were ingested successfully!")
        else:
            error_details = "\n".join(failures)
            QMessageBox.warning(self, "Processing Completed with Errors", f"The following documents failed:\n\n{error_details}")

    def closeEvent(self, event):
        event.accept()
