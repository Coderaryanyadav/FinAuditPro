"""Secure lock screen overlay widget that grabs focus and locks PySide6 main window."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import RBACManager


class LockScreenOverlay(QWidget):
    """Apple slate-styled lock screen overlay capturing all mouse/keyboard inputs."""

    unlocked = Signal()

    def __init__(self, parent: QWidget, rbac_manager: RBACManager) -> None:
        super().__init__(parent)
        self.rbac_manager = rbac_manager
        self.setObjectName("lockScreenOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        if parent:
            self.setGeometry(parent.rect())

        self.setStyleSheet("""
            QWidget#lockScreenOverlay {
                background-color: #0F172A;
            }
            QLabel {
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
                border: none;
            }
            QLineEdit {
                border: 1.5px solid #334155;
                border-radius: 8px;
                padding: 12px 16px;
                background: #1E293B;
                color: #FFFFFF;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #38BDF8;
                background: #0F172A;
            }
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                padding: 12px 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1D4ED8;
            }
            QPushButton:pressed {
                background-color: #1E40AF;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(18)

        logo_box = QLabel("FA")
        logo_box.setFixedSize(54, 54)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #2563EB; color: #FFFFFF; border-radius: 12px;"
            "font-size: 20px; font-weight: 800;"
        )
        layout.addWidget(logo_box, alignment=Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Session Locked")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: #F8FAFC;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("Workstation locked securely due to inactivity.")
        subtitle.setStyleSheet("font-size: 13px; color: #94A3B8;")
        layout.addWidget(subtitle, alignment=Qt.AlignmentFlag.AlignCenter)

        form = QFrame()
        form.setFixedWidth(320)
        fl = QVBoxLayout(form)
        fl.setContentsMargins(0, 8, 0, 0)
        fl.setSpacing(12)

        self.input_passcode = QLineEdit()
        self.input_passcode.setPlaceholderText("Enter passcode to unlock...")
        self.input_passcode.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_passcode.returnPressed.connect(self._handle_unlock)
        fl.addWidget(self.input_passcode)

        btn_unlock = QPushButton("Unlock Workstation")
        btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_unlock.clicked.connect(self._handle_unlock)
        fl.addWidget(btn_unlock)

        layout.addWidget(form, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        self.input_passcode.setFocus()
        self.grabKeyboard()

    def hideEvent(self, event) -> None:
        self.releaseKeyboard()
        super().hideEvent(event)

    def resizeEvent(self, event) -> None:
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)

    def _handle_unlock(self) -> None:
        passcode = self.input_passcode.text().strip()
        if not passcode:
            self.releaseKeyboard()
            QMessageBox.warning(self, "Access Denied", "Please enter your passcode to unlock.")
            self.grabKeyboard()
            self.input_passcode.setFocus()
            return

        try:
            self.rbac_manager.unlock_session(passcode)
            self.input_passcode.clear()
            self.unlocked.emit()
            self.close()
            self.deleteLater()
        except Exception as ex:
            self.releaseKeyboard()
            msg = str(ex) if str(ex).strip() else "Incorrect passcode. Failed to unlock session."
            QMessageBox.warning(self, "Access Denied", msg)
            self.grabKeyboard()
            self.input_passcode.clear()
            self.input_passcode.setFocus()
