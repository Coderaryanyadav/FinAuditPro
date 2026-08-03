"""
About & Release Notes Dialog for FinAuditPro.
Displays application version, ICAI compliance badges, release notes, and system diagnostics.
"""

try:
    from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                                   QPushButton, QFrame, QTextEdit)
    from PySide6.QtCore import Qt
except ImportError:
    import logging
    logging.getLogger(__name__).warning("PySide6 not available. About dialog disabled.")
    QDialog = object
    QVBoxLayout = QHBoxLayout = QLabel = QPushButton = QFrame = QTextEdit = Qt = None
from deployment.version_checker import VersionChecker
from deployment.diagnostics import SystemDiagnostics

class AboutDialog(QDialog):
    """About & Release Notes modal dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About FinAuditPro")
        self.setFixedSize(540, 480)
        self.setStyleSheet("background-color: #ffffff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_frame = QFrame()
        h_layout = QHBoxLayout(h_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        
        icon_lbl = QLabel("")
        icon_lbl.setStyleSheet("font-size: 36px; border: none;")
        
        info_box = QVBoxLayout()
        title = QLabel("FinAuditPro")
        title.setStyleSheet("font-size: 20px; font-weight: 600; color: #1d1d1f; letter-spacing: -0.4px;")
        
        ver_info = VersionChecker.get_version_info()
        sub = QLabel(f"Version {ver_info.version} (Build {ver_info.build_number}) — {ver_info.edition}")
        sub.setStyleSheet("font-size: 12px; color: #6e6e73;")
        
        info_box.addWidget(title)
        info_box.addWidget(sub)
        
        h_layout.addWidget(icon_lbl)
        h_layout.addSpacing(12)
        h_layout.addLayout(info_box)
        h_layout.addStretch()
        
        layout.addWidget(h_frame)

        # Badges Frame
        badges_frame = QFrame()
        badges_frame.setStyleSheet("background-color: #f5f5f7; border: 1px solid #e5e5ea; border-radius: 8px; padding: 10px;")
        b_layout = QHBoxLayout(badges_frame)
        
        b1 = QLabel(" 100% Offline AI")
        b1.setStyleSheet("color: #007aff; font-weight: 600; font-size: 11px;")
        b2 = QLabel(" ICAI Standard & CA Policy Compliant")
        b2.setStyleSheet("color: #34c759; font-weight: 600; font-size: 11px;")
        
        b_layout.addWidget(b1)
        b_layout.addStretch()
        b_layout.addWidget(b2)
        
        layout.addWidget(badges_frame)

        # Release Notes Text Area
        notes_label = QLabel("Release Notes & Version History:")
        notes_label.setStyleSheet("font-weight: 600; color: #1d1d1f; font-size: 12px;")
        layout.addWidget(notes_label)

        notes_box = QTextEdit()
        notes_box.setReadOnly(True)
        notes_box.setStyleSheet("border: 1px solid #e5e5ea; border-radius: 8px; padding: 8px; font-family: sans-serif; font-size: 12px; color: #1d1d1f; background-color: #f5f5f7;")
        
        notes_html = "<ul style='line-height: 1.5;'>"
        for note in ver_info.release_notes:
            notes_html += f"<li>{note}</li>"
        notes_html += "</ul>"
        notes_box.setHtml(notes_html)
        
        layout.addWidget(notes_box)

        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(36)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #007aff;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #0062cc; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)
