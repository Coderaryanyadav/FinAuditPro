from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QLineEdit, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QSplitter, QDialog, 
                               QDialogButtonBox, QFormLayout, QMessageBox)
from PySide6.QtCore import Qt
from database.database import SessionLocal
from database.models import Client, AuditProject
from .styles import apply_shadow

class AddClientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add New Client")
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")
        self.resize(450, 320)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        
        title = QLabel("Add New Audit Client")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #0f172a; margin-bottom: 12px;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_layout = QFormLayout(form_frame)
        form_layout.setSpacing(12)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. TechCorp Solutions Pvt Ltd")
        self.gst_input = QLineEdit()
        self.gst_input.setPlaceholderText("e.g. 27AADCT1234E1Z5")
        self.pan_input = QLineEdit()
        self.pan_input.setPlaceholderText("e.g. AADCT1234E")
        self.industry_input = QLineEdit()
        self.industry_input.setPlaceholderText("e.g. Technology / Retail / Finance")
        
        for input_field in [self.name_input, self.gst_input, self.pan_input, self.industry_input]:
            input_field.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; color: #0f172a; background-color: #f8fafc;")
            
        form_layout.addRow("Client Name *", self.name_input)
        form_layout.addRow("GST Number", self.gst_input)
        form_layout.addRow("PAN Number", self.pan_input)
        form_layout.addRow("Industry", self.industry_input)
        
        layout.addWidget(form_frame)
        
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.setStyleSheet("""
            QPushButton { padding: 6px 16px; border-radius: 4px; }
            QPushButton[text="OK"] { background-color: #0ea5e9; color: white; border: none; font-weight: bold; }
            QPushButton[text="Cancel"] { background-color: #f1f5f9; color: #475569; border: 1px solid #cbd5e1; }
        """)
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def validate_and_accept(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Client Name is required!")
        else:
            self.accept()

class ClientManagementWidget(QWidget):
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
        
        title = QLabel("Clients")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #0f172a; border: none;")
        action_layout.addWidget(title)
        
        # Search
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search client name, GST, PAN...")
        self.search_box.setFixedWidth(300)
        self.search_box.setStyleSheet("padding: 8px; border: 1px solid #e2e8f0; border-radius: 6px; background-color: #f8fafc; color: #0f172a;")
        self.search_box.textChanged.connect(self.load_clients)
        action_layout.addSpacing(20)
        action_layout.addWidget(self.search_box)
        
        action_layout.addStretch()
        
        # Buttons
        btn_add = QPushButton("Add New Client")
        btn_add.setStyleSheet("padding: 8px 16px; border: none; border-radius: 6px; background-color: #0ea5e9; color: white; font-weight: bold;")
        btn_add.clicked.connect(self.open_add_client_dialog)
        
        action_layout.addWidget(btn_add)
        main_layout.addWidget(action_bar)
        
        # Splitter for Main Content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #e2e8f0; }")
        
        # Left Side (Table)
        table_container = QFrame()
        table_container.setStyleSheet("background-color: white; border: none; margin: 24px; border-radius: 12px; border: 1px solid #e2e8f0;")
        apply_shadow(table_container, blur=15, dy=3, alpha=15)
        table_layout = QVBoxLayout(table_container)
        
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Client / Company Name", "GST & PAN", "Industry", "Status", "Risk Level"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("""
            QTableWidget { border: none; gridline-color: #f1f5f9; }
            QHeaderView::section { background-color: #f8fafc; color: #64748b; padding: 12px; font-weight: 600; text-align: left; border: none; border-bottom: 1px solid #e2e8f0; }
            QTableWidget::item { padding: 12px; border-bottom: 1px solid #f1f5f9; color: #0f172a; }
            QTableWidget::item:selected { background-color: #f0f9ff; color: #0f172a; border-left: 3px solid #0ea5e9; }
        """)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.itemSelectionChanged.connect(self.on_client_selected)
        
        table_layout.addWidget(self.table)
        
        # Right Side (Details Panel)
        self.details_panel = QFrame()
        self.details_panel.setStyleSheet("background-color: white; border-left: 1px solid #e2e8f0;")
        self.details_panel.setFixedWidth(380)
        self.details_layout = QVBoxLayout(self.details_panel)
        self.details_layout.setContentsMargins(24, 24, 24, 24)
        self.details_layout.setSpacing(16)
        
        self.header_lbl = QLabel("No Client Selected")
        self.header_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f172a; border: none;")
        self.industry_lbl = QLabel("")
        self.industry_lbl.setStyleSheet("color: #64748b; font-size: 14px; border: none;")
        
        self.details_layout.addWidget(self.header_lbl)
        self.details_layout.addWidget(self.industry_lbl)
        
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px;")
        apply_shadow(self.info_frame, blur=10, dy=2, alpha=10)
        self.info_layout = QVBoxLayout(self.info_frame)
        self.details_layout.addWidget(self.info_frame)
        self.details_layout.addStretch()
        
        splitter.addWidget(table_container)
        splitter.addWidget(self.details_panel)
        splitter.setSizes([800, 380])
        
        main_layout.addWidget(splitter)
        
        # Initial database seed (if empty) & load
        self.seed_mock_data_if_empty()
        self.load_clients()
        
    def seed_mock_data_if_empty(self):
        if self.session.query(Client).count() == 0:
            c1 = Client(name="TechCorp Solutions Pvt Ltd", gst_number="27AADCT1234E1Z5", pan_number="AADCT1234E", industry="IT / Technology")
            c2 = Client(name="Global Impex Ltd.", gst_number="07BXYZI9876Q1Z9", pan_number="BXYZI9876Q", industry="Import/Export")
            c3 = Client(name="Mega Mart Retail", gst_number="29ABCDE1234F2Z5", pan_number="ABCDE1234F", industry="Retail")
            self.session.add_all([c1, c2, c3])
            self.session.commit()
            
            # Seed matching audit projects
            ap1 = AuditProject(client_id=c1.id, financial_year="2025-26", status="In Progress", risk_score=24.0, risk_level="Low")
            ap2 = AuditProject(client_id=c2.id, financial_year="2025-26", status="Pending Review", risk_score=56.0, risk_level="Medium")
            ap3 = AuditProject(client_id=c3.id, financial_year="2025-26", status="Completed", risk_score=82.0, risk_level="High")
            self.session.add_all([ap1, ap2, ap3])
            self.session.commit()

    def load_clients(self):
        search_text = self.search_box.text().strip()
        query = self.session.query(Client)
        if search_text:
            query = query.filter(Client.name.like(f"%{search_text}%") | 
                                 Client.gst_number.like(f"%{search_text}%") | 
                                 Client.pan_number.like(f"%{search_text}%"))
        clients = query.all()
        
        self.table.setRowCount(0)
        for r, client in enumerate(clients):
            self.table.insertRow(r)
            
            # Fetch latest audit project info
            latest_audit = self.session.query(AuditProject).filter_by(client_id=client.id).order_by(AuditProject.id.desc()).first()
            status = latest_audit.status if latest_audit else "Not Started"
            risk = latest_audit.risk_level if latest_audit else "Unknown"
            
            self.table.setItem(r, 0, QTableWidgetItem(client.name))
            self.table.setItem(r, 1, QTableWidgetItem(f"GST: {client.gst_number or 'N/A'}\nPAN: {client.pan_number or 'N/A'}"))
            self.table.setItem(r, 2, QTableWidgetItem(client.industry or "N/A"))
            self.table.setItem(r, 3, QTableWidgetItem(status))
            self.table.setItem(r, 4, QTableWidgetItem(risk))
            
            # Attach Client ID to item for retrieval on selection
            self.table.item(r, 0).setData(Qt.ItemDataRole.UserRole, client.id)

    def on_client_selected(self):
        selected_rows = self.table.selectedItems()
        if not selected_rows: return
        client_id = selected_rows[0].data(Qt.ItemDataRole.UserRole)
        
        client = self.session.query(Client).filter_by(id=client_id).first()
        if not client: return
        
        self.header_lbl.setText(client.name)
        self.industry_lbl.setText(f"{client.industry or 'General'} Sector")
        
        # Clear old details layout
        for i in reversed(range(self.info_layout.count())): 
            self.info_layout.itemAt(i).widget().setParent(None)
            
        def add_info_to_details(label, value):
            lbl1 = QLabel(label)
            lbl1.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 500; border: none;")
            lbl2 = QLabel(value)
            lbl2.setStyleSheet("color: #0f172a; font-size: 14px; font-weight: bold; border: none;")
            self.info_layout.addWidget(lbl1)
            self.info_layout.addWidget(lbl2)
            self.info_layout.addSpacing(8)
            
        add_info_to_details("GST Number", client.gst_number or "N/A")
        add_info_to_details("PAN", client.pan_number or "N/A")
        add_info_to_details("Created At", client.created_at.strftime("%d-%b-%Y") if client.created_at else "N/A")

        # Action buttons for selected client
        btn_box = QHBoxLayout()
        btn_edit = QPushButton("Edit Client")
        btn_edit.setStyleSheet("padding: 6px 12px; background-color: #f1f5f9; color: #0ea5e9; border: 1px solid #bae6fd; border-radius: 6px; font-weight: 600;")
        btn_edit.clicked.connect(lambda: self.open_edit_client_dialog(client.id))
        
        btn_del = QPushButton("Delete")
        btn_del.setStyleSheet("padding: 6px 12px; background-color: #fef2f2; color: #ef4444; border: 1px solid #fecaca; border-radius: 6px; font-weight: 600;")
        btn_del.clicked.connect(lambda: self.delete_client(client.id))
        
        btn_box.addWidget(btn_edit)
        btn_box.addWidget(btn_del)
        self.info_layout.addLayout(btn_box)

    def open_add_client_dialog(self):
        from security.security_manager import SecurityManager
        from security.rbac import Permission
        sm = SecurityManager()
        if sm.current_session and not sm.check_permission(Permission.MANAGE_CLIENTS):
            QMessageBox.warning(self, "Access Denied", "Your role does not have permission to manage clients.")
            return

        dialog = AddClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name = dialog.name_input.text().strip()
            if not name: return
            
            new_client = Client(
                name=name,
                gst_number=dialog.gst_input.text().strip() or None,
                pan_number=dialog.pan_input.text().strip() or None,
                industry=dialog.industry_input.text().strip() or None
            )
            self.session.add(new_client)
            self.session.commit()
            
            # Auto add default audit project
            ap = AuditProject(client_id=new_client.id, financial_year="2025-26", status="Not Started", risk_level="Unknown")
            self.session.add(ap)
            self.session.commit()
            
            self.load_clients()

    def open_edit_client_dialog(self, client_id):
        client = self.session.query(Client).filter_by(id=client_id).first()
        if not client: return
        
        dialog = AddClientDialog(self)
        dialog.setWindowTitle("Edit Client Details")
        dialog.name_input.setText(client.name or "")
        dialog.gst_input.setText(client.gst_number or "")
        dialog.pan_input.setText(client.pan_number or "")
        dialog.industry_input.setText(client.industry or "")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            client.name = dialog.name_input.text().strip()
            client.gst_number = dialog.gst_input.text().strip() or None
            client.pan_number = dialog.pan_input.text().strip() or None
            client.industry = dialog.industry_input.text().strip() or None
            self.session.commit()
            self.load_clients()
            self.header_lbl.setText(client.name)
            self.industry_lbl.setText(f"{client.industry or 'General'} Sector")

    def delete_client(self, client_id):
        client = self.session.query(Client).filter_by(id=client_id).first()
        if not client: return
        
        ans = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete client '{client.name}' and all associated audit data?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ans == QMessageBox.StandardButton.Yes:
            self.session.delete(client)
            self.session.commit()
            self.header_lbl.setText("No Client Selected")
            self.industry_lbl.setText("")
            for i in reversed(range(self.info_layout.count())): 
                self.info_layout.itemAt(i).widget().setParent(None)
            self.load_clients()
            
    def closeEvent(self, event):
        self.session.close()
        event.accept()

