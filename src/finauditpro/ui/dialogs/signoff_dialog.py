"""Sign-off dialog with explicit legal disclaimers and content hash binding."""

from finauditpro.ui.widgets.custom_combo import CustomComboBox
from finauditpro.ui.widgets.custom_combo import CustomComboBox
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import SignOffDTO
from finauditpro.domain.working_paper_entities import SignOffLevelEnum, WorkingPaper


class SignOffDialog(QDialog):
    """Dialog for executing Working Paper sign-offs with legal disclaimers."""

    def __init__(
        self,
        working_paper: WorkingPaper,
        working_paper_service: WorkingPaperService,
        user_session: UserSession | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.wp = working_paper
        self.wp_service = working_paper_service
        self.user_session = user_session

        self.setWindowTitle(f"Sign Off Working Paper — {self.wp.index_reference}")
        self.resize(550, 420)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. Prominent Legal Disclaimer Banner
        disclaimer_box = QGroupBox("LEGAL & STATUTORY SIGN-OFF DISCLAIMER")
        disclaimer_box.setStyleSheet(
            "QGroupBox { font-weight: bold; color: #b45309; background-color: #fef3c7; "
            "border: 1px solid #fde68a; border-radius: 8px; margin-top: 10px; padding: 12px; } "
            "QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; color: #92400e; }"
        )
        disc_layout = QVBoxLayout(disclaimer_box)

        disc_text = QLabel(
            "<b>NOTICE:</b> This electronic sign-off is an internal audit workflow attestation "
            "and tamper-evident integrity record.<br><br>"
            "• It is <b>NOT</b> an IT Act 2000 Class 3 PKI Digital Signature Certificate (DSC).<br>"
            "• It is <b>NOT</b> an ICAI Unique Document Identification Number (UDIN).<br>"
            "• It confers no external legal validity on any report or financial statement."
        )
        disc_text.setWordWrap(True)
        disc_text.setStyleSheet(
            "color: #78350f; font-size: 12px; background: transparent; border: none;"
        )
        disc_layout.addWidget(disc_text)
        layout.addWidget(disclaimer_box)

        # 2. Form Inputs
        form = QFormLayout()

        self.level_combo = CustomComboBox()
        self.level_combo.addItem("Reviewed", SignOffLevelEnum.REVIEWED)
        self.level_combo.addItem("Signed Off (Final Lock)", SignOffLevelEnum.FINAL_SIGN_OFF)

        default_user = self.user_session.username if self.user_session else "Lead Auditor"
        self.user_id_input = QLineEdit(default_user)
        self.role_input = CustomComboBox()
        self.role_input.addItems(["Associate", "Senior", "Manager", "Partner", "Administrator"])

        if self.user_session:
            role_val = (
                self.user_session.role.value
                if hasattr(self.user_session.role, "value")
                else str(self.user_session.role)
            )
            idx = self.role_input.findText(role_val)
            if idx >= 0:
                self.role_input.setCurrentIndex(idx)
        else:
            self.role_input.setCurrentIndex(3)  # Partner default

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Optional sign-off notes...")

        form.addRow("Sign-Off Level:", self.level_combo)
        form.addRow("Signer Identity (User ID):", self.user_id_input)
        form.addRow("Signer Role:", self.role_input)
        form.addRow("Sign-Off Note:", self.note_input)

        layout.addLayout(form)

        # 3. Actions
        btn_box = QHBoxLayout()
        btn_sign = QPushButton("Execute Sign-Off & Lock Paper")
        btn_sign.setStyleSheet("background-color: #10b981; color: white; font-weight: bold;")
        btn_sign.clicked.connect(self._on_sign_off_clicked)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(btn_sign)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

    def _on_sign_off_clicked(self) -> None:
        user_id = self.user_id_input.text().strip()
        user_role = self.role_input.currentText()
        raw_level = self.level_combo.currentData()
        if isinstance(raw_level, SignOffLevelEnum):
            level = raw_level
        elif isinstance(raw_level, str):
            try:
                level = SignOffLevelEnum(raw_level)
            except ValueError:
                level = (
                    SignOffLevelEnum[raw_level]
                    if raw_level in SignOffLevelEnum.__members__
                    else SignOffLevelEnum.REVIEWED
                )
        else:
            level = SignOffLevelEnum.REVIEWED
        note = self.note_input.text().strip()

        if not user_id:
            QMessageBox.warning(self, "Validation Error", "Please enter signer User ID.")
            return

        try:
            self.wp_service.sign_off_working_paper(
                SignOffDTO(
                    working_paper_id=self.wp.id,
                    level=level,
                    user_id=user_id,
                    user_role=user_role,
                    note=note if note else None,
                )
            )
            QMessageBox.information(
                self,
                "Sign-Off Complete",
                f"Working Paper '{self.wp.index_reference}' successfully signed off!\nPaper is now locked and content hash bound.",
            )
            self.accept()
        except Exception as ex:
            QMessageBox.critical(self, "Sign-Off Violation", f"Sign-off failed: {ex}")
