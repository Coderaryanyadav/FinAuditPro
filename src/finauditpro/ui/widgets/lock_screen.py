"""Secure lock screen overlay widget that grabs focus and locks PySide6 main window."""

import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFrame
)
from finauditpro.application.security.rbac import RBACManager


class LockScreenOverlay(QWidget):
    """Apple slate-styled lock screen overlay capturing all mouse/keyboard inputs."""

    unlocked = Signal()

    def __init__(self, parent: QWidget, rbac_manager: RBACManager) -> None:
        super().__init__(parent)
        self.rbac_manager = rbac_manager
        self.setObjectName("lockScreenOverlay")

        # Visual theme styling matching Cupertino dark-slate mode
        self.setStyleSheet("""
            QWidget#lockScreenOverlay {
                background-color: rgba(15, 23, 42, 0.97);
            }
            QLabel {
                color: #FFFFFF;
                font-family: 'SF Pro Text', -apple-system, sans-serif;
                background: transparent;
                border: none;
            }
            QLineEdit {
                border: 1.5px solid #475569;
                border-radius: 6px;
                padding: 10px 14px;
                background: #1E293B;
                color: #FFFFFF;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: #FFFFFF;
                font-size: 13px;
                font-weight: 600;
                border-radius: 6px;
                padding: 10px 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0062CC;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Brand / Logo mark
        logo_box = QLabel("FA")
        logo_box.setFixedSize(48, 48)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #007AFF; color: #ffffff; border-radius: 10px;"
            "font-size: 18px; font-weight: 800;"
        )
        layout.addWidget(logo_box, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Session Locked")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Workstation locked automatically due to inactivity.")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        # Unlock credentials input
        form = QFrame()
        form.setFixedWidth(300)
        fl = QVBoxLayout(form)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(10)

        self.input_passcode = QLineEdit()
        self.input_passcode.setPlaceholderText("Enter passcode to unlock")
        self.input_passcode.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_passcode.returnPressed.connect(self._handle_unlock)
        fl.addWidget(self.input_passcode)

        btn_unlock = QPushButton("Unlock Workstation")
        btn_unlock.clicked.connect(self._handle_unlock)
        fl.addWidget(btn_unlock)

        layout.addWidget(form)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.input_passcode.setFocus()
        # Grab keyboard input to isolate workstation interaction
        self.grabKeyboard()

    def hideEvent(self, event) -> None:
        self.releaseKeyboard()
        super().hideEvent(event)

    def resizeEvent(self, event) -> None:
        """Dynamic resizing keeping overlay aligned with MainWindow geometry."""
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)

    def _handle_unlock(self) -> None:
        passcode = self.input_passcode.text().strip()
        if not passcode:
            return

        try:
            self.rbac_manager.unlock_session(passcode)
            self.input_passcode.clear()
            self.unlocked.emit()
            self.close()
            self.deleteLater()
        except ValueError as ex:
            self.releaseKeyboard()
            QMessageBox.warning(self, "Access Denied", str(ex))
            self.grabKeyboard()
            self.input_passcode.clear()
            self.input_passcode.setFocus()
