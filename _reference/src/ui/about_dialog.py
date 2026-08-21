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
        self.setStyleSheet("background-color: #ffffff; color: #0f172a;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_frame = QFrame()
        h_layout = QHBoxLayout(h_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)

        # Logo mark
        icon_lbl = QLabel("FA")
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(
            "background: #0284c7; color: #ffffff; border-radius: 10px;"
            "font-size: 16px; font-weight: 800; border: none;"
        )

        info_box = QVBoxLayout()
        title = QLabel("FinAuditPro")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #0f172a; letter-spacing: -0.4px;")

        # Item 83: Cache version info
        ver_info = VersionChecker.get_version_info()
        sub = QLabel(f"Version {ver_info.version} (Build {ver_info.build_number}) — {ver_info.edition}")
        sub.setStyleSheet("font-size: 12px; color: #64748b;")

        info_box.addWidget(title)
        info_box.addWidget(sub)

        h_layout.addWidget(icon_lbl)
        h_layout.addSpacing(14)
        h_layout.addLayout(info_box)
        h_layout.addStretch()

        layout.addWidget(h_frame)

        # Badges Frame
        badges_frame = QFrame()
        badges_frame.setStyleSheet("background-color: #f8fafc; border: 1px solid #e1e8f4; border-radius: 8px; padding: 10px;")
        b_layout = QHBoxLayout(badges_frame)

        b1 = QLabel("🔒 100% Offline AI Engine")
        b1.setStyleSheet("color: #0284c7; font-weight: 600; font-size: 11px;")
        b2 = QLabel("✓ ICAI Standard & CA Policy Compliant")
        b2.setStyleSheet("color: #047857; font-weight: 600; font-size: 11px;")

        b_layout.addWidget(b1)
        b_layout.addStretch()
        b_layout.addWidget(b2)

        layout.addWidget(badges_frame)

        # Release Notes Text Area
        notes_label = QLabel("Release Notes & Version History:")
        notes_label.setStyleSheet("font-weight: 600; color: #0f172a; font-size: 12px;")
        layout.addWidget(notes_label)

        notes_box = QTextEdit()
        notes_box.setReadOnly(True)
        notes_box.setStyleSheet("border: 1px solid #e1e8f4; border-radius: 8px; padding: 10px; font-family: sans-serif; font-size: 12px; color: #0f172a; background-color: #f8fafc;")

        notes_html = "<ul style='line-height: 1.5; color: #334155; margin-left: -15px;'>"
        for note in ver_info.release_notes:
            notes_html += f"<li>{note}</li>"
        notes_html += "</ul>"
        notes_box.setHtml(notes_html)

        layout.addWidget(notes_box)

        # Close Button
        btn_close = QPushButton("Close")
        btn_close.setFixedHeight(36)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setToolTip("Close about dialog (Esc)")
        btn_close.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 600;
                font-size: 13px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover { background-color: #0369a1; }
            QPushButton:pressed { background-color: #075985; }
        """)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    # Item 3: Bind Esc key shortcut
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
