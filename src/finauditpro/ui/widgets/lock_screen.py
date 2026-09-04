"""Secure, production-grade lock screen overlay widget that grabs focus, supports Touch ID biometrics, and locks PySide6 main window."""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import RBACManager


class LockScreenOverlay(QWidget):
    """Apple slate-styled lock screen overlay capturing all mouse/keyboard inputs and offering Touch ID."""

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
            QFrame#lockCenterCard {
                background-color: #1E293B;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 28px 24px;
            }
            QLabel {
                color: #FFFFFF;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: transparent;
                border: none;
            }
            QLineEdit {
                border: 1.5px solid #475569;
                border-radius: 8px;
                padding: 10px 14px;
                background: #0F172A;
                color: #FFFFFF;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border-color: #38BDF8;
            }
            QPushButton#btnUnlockAction {
                background-color: #2563EB;
                color: #FFFFFF;
                font-size: 14px;
                font-weight: 600;
                border-radius: 8px;
                padding: 10px 16px;
                border: none;
                min-height: 22px;
            }
            QPushButton#btnUnlockAction:hover {
                background-color: #1D4ED8;
            }
            QPushButton#btnUnlockAction:pressed {
                background-color: #1E40AF;
            }
            QPushButton#btnTouchIDAction {
                background-color: #334155;
                color: #F8FAFC;
                font-size: 13px;
                font-weight: 600;
                border-radius: 8px;
                padding: 8px 14px;
                border: 1px solid #475569;
                min-height: 20px;
            }
            QPushButton#btnTouchIDAction:hover {
                background-color: #475569;
                border-color: #38BDF8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        card = QFrame()
        card.setObjectName("lockCenterCard")
        card.setFixedWidth(380)
        card_l = QVBoxLayout(card)
        card_l.setSpacing(14)
        card_l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(48, 48)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #0284C7);"
            "color: #FFFFFF; border-radius: 10px; font-size: 18px; font-weight: 800;"
        )
        logo_row.addWidget(logo_box)
        card_l.addLayout(logo_row)

        title = QLabel("Workstation Locked")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #F8FAFC;")
        card_l.addWidget(title)

        subtitle = QLabel("Session secured under SQC-1. Use Touch ID or passcode.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: 12px; color: #94A3B8;")
        subtitle.setWordWrap(True)
        card_l.addWidget(subtitle)

        self.input_passcode = QLineEdit()
        self.input_passcode.setPlaceholderText("Enter passcode to unlock...")
        self.input_passcode.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_passcode.returnPressed.connect(self._handle_unlock)
        card_l.addWidget(self.input_passcode)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color: #F87171; font-size: 12px; font-weight: 500;")
        self.lbl_error.setVisible(False)
        card_l.addWidget(self.lbl_error)

        btn_unlock = QPushButton("Unlock Workstation")
        btn_unlock.setObjectName("btnUnlockAction")
        btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_unlock.clicked.connect(self._handle_unlock)
        card_l.addWidget(btn_unlock)

        if self.rbac_manager.is_biometrics_supported():
            btn_touch_id = QPushButton("🔐 Touch ID Fingerprint")
            btn_touch_id.setObjectName("btnTouchIDAction")
            btn_touch_id.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_touch_id.clicked.connect(self._handle_touch_id_unlock)
            card_l.addWidget(btn_touch_id)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def showEvent(self, event: Any) -> None:
        super().showEvent(event)
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        self.lbl_error.setVisible(False)
        self.input_passcode.clear()
        self.input_passcode.setFocus()
        self.grabKeyboard()

    def hideEvent(self, event: Any) -> None:
        self.releaseKeyboard()
        super().hideEvent(event)

    def resizeEvent(self, event: Any) -> None:
        if self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)

    def _handle_touch_id_unlock(self) -> None:
        self.releaseKeyboard()
        if self.rbac_manager.unlock_with_biometrics("Touch ID to unlock FinAuditPro Workstation"):
            self.input_passcode.clear()
            self.lbl_error.setVisible(False)
            self.unlocked.emit()
            self.close()
            self.deleteLater()
        else:
            self.grabKeyboard()
            self.lbl_error.setText("Touch ID verification failed or cancelled.")
            self.lbl_error.setVisible(True)
            self.input_passcode.setFocus()

    def _handle_unlock(self) -> None:
        passcode = self.input_passcode.text().strip()
        if not passcode:
            self.lbl_error.setText("Please enter your passcode to unlock.")
            self.lbl_error.setVisible(True)
            self.input_passcode.setFocus()
            return

        try:
            self.rbac_manager.unlock_session(passcode)
            self.input_passcode.clear()
            self.lbl_error.setVisible(False)
            self.unlocked.emit()
            self.close()
            self.deleteLater()
        except Exception:
            self.lbl_error.setText("Incorrect passcode. Failed to unlock session.")
            self.lbl_error.setVisible(True)
            self.input_passcode.selectAll()
            self.input_passcode.setFocus()
