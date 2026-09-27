"""
User Management and 3-Tier Governance Dialog for FinAuditPro.
Enables Engagement Partner (Admin) to create, manage, reset credentials, and assign roles for Checker and Maker team members.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.security.rbac import UserSession
from finauditpro.application.services.auth_service import AuthService
from finauditpro.domain.entities import RoleEnum, User
from finauditpro.domain.exceptions import ValidationError
from finauditpro.ui.theme import CardWidget


class CreateUserSubDialog(QDialog):
    """Sub-dialog to create a new user with role and credentials."""

    def __init__(self, auth_service: AuthService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.created_user: User | None = None
        self.setWindowTitle("Create New Team Member Account")
        self.setFixedWidth(460)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)

        layout.addWidget(QLabel("<h3>Create Team Member Account</h3>"))
        sub = QLabel("Configure credentials and 3-Tier Segregation of Duties role.")
        sub.setStyleSheet("color: #64748B; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(sub)

        form = QFormLayout()
        form.setSpacing(8)
        f_style = "QLineEdit, QComboBox { border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; font-size: 13px; background: #FFF; }"

        self.inp_username = QLineEdit()
        self.inp_username.setPlaceholderText("e.g. checker_rajesh or rajesh@firm.com")
        self.inp_username.setStyleSheet(f_style)
        form.addRow("Username / Email:", self.inp_username)

        self.inp_password = QLineEdit()
        self.inp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_password.setPlaceholderText("Min 8 chars with letter & number")
        self.inp_password.setStyleSheet(f_style)
        form.addRow("Password:", self.inp_password)

        self.combo_role = QComboBox()
        self.combo_role.setStyleSheet(f_style)
        self.combo_role.addItem("Maker (Audit Assistant - Testing & Drafting)", RoleEnum.MAKER)
        self.combo_role.addItem("Checker (Audit Senior / Manager - Review & Quality)", RoleEnum.CHECKER)
        self.combo_role.addItem("Admin (Engagement Partner / CA - Sign-off & Locking)", RoleEnum.ADMIN)
        form.addRow("Governance Role:", self.combo_role)

        self.combo_force_reset = QComboBox()
        self.combo_force_reset.setStyleSheet(f_style)
        self.combo_force_reset.addItem("No (Direct active password)", False)
        self.combo_force_reset.addItem("Yes (Require password change on first login)", True)
        form.addRow("Require Reset on Login:", self.combo_force_reset)
        layout.addLayout(form)

        self.lbl_resp = QLabel()
        self.lbl_resp.setWordWrap(True)
        self.lbl_resp.setStyleSheet("background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 8px; font-size: 11px; color: #475569;")
        self._update_role_help()
        self.combo_role.currentIndexChanged.connect(self._update_role_help)
        layout.addWidget(self.lbl_resp)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("Create Account")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _update_role_help(self) -> None:
        role = self.combo_role.currentData()
        if role == RoleEnum.MAKER:
            self.lbl_resp.setText("<b>Maker:</b> Upload evidence, execute automated control tests, draft working papers.")
        elif role == RoleEnum.CHECKER:
            self.lbl_resp.setText("<b>Checker:</b> Review testing exceptions, validate sample adequacy (SA 530), issue review notes.")
        else:
            self.lbl_resp.setText("<b>Admin (Partner):</b> Final sign-off, workpaper locking, Sec 143(3)(i) IFC certificate, practice management.")

    def _on_save(self) -> None:
        username = self.inp_username.text().strip()
        password = self.inp_password.text()
        role = self.combo_role.currentData()
        must_change = self.combo_force_reset.currentData()
        if not username:
            QMessageBox.warning(self, "Validation Error", "Please enter a username.")
            return
        try:
            self.created_user = self.auth_service.create_user(username, password, role, must_change)
            QMessageBox.information(self, "Account Created", f"User '{username}' created successfully.")
            self.accept()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create user: {e}")


class ResetPasswordSubDialog(QDialog):
    """Sub-dialog for Admin to reset a user's password."""

    def __init__(self, auth_service: AuthService, user: User, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.user = user
        self.setWindowTitle(f"Reset Password - {user.username}")
        self.setFixedWidth(400)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(QLabel(f"<h3>Reset Password for '{self.user.username}'</h3>"))

        form = QFormLayout()
        form.setSpacing(8)
        f_style = "QLineEdit, QComboBox { border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px; font-size: 13px; background: #FFF; }"

        self.inp_pwd = QLineEdit()
        self.inp_pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self.inp_pwd.setPlaceholderText("New secure password")
        self.inp_pwd.setStyleSheet(f_style)
        form.addRow("New Password:", self.inp_pwd)

        self.combo_reset = QComboBox()
        self.combo_reset.setStyleSheet(f_style)
        self.combo_reset.addItem("Yes (Require reset on next login)", True)
        self.combo_reset.addItem("No (Direct new password)", False)
        form.addRow("Mandatory Reset:", self.combo_reset)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_save = QPushButton("Update Password")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _on_save(self) -> None:
        new_pwd = self.inp_pwd.text()
        req = self.combo_reset.currentData()
        try:
            self.auth_service.admin_reset_password(self.user.id, new_pwd, must_change_password=req)
            QMessageBox.information(self, "Password Reset", f"Password updated for '{self.user.username}'.")
            self.accept()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation Failed", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset password: {e}")


class UserManagementDialog(QDialog):
    """Primary administrative management dialog for Maker -> Checker -> Admin team hierarchy."""

    def __init__(
        self,
        auth_service: AuthService,
        current_session: UserSession | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.auth_service = auth_service
        self.current_session = current_session
        self.users: list[User] = []
        self.setWindowTitle("3-Tier Team & Governance Management (Maker → Checker → Admin)")
        self.resize(760, 480)
        self._init_ui()
        self._load_users()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        header_card = CardWidget("3-TIER SEGREGATION OF DUTIES (SoD) HIERARCHY")
        info = QLabel(
            "FinAuditPro 3-tier governance: <b>Maker</b> (Testing & Drafting) → <b>Checker</b> (Review & Quality) → <b>Admin / Partner</b> (Locking & Sign-off). "
            "Manage team credentials, passwords, and role assignments below."
        )
        info.setWordWrap(True)
        info.setStyleSheet("font-size: 12px; color: #334155;")
        header_card.content_layout.addWidget(info)
        layout.addWidget(header_card)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_add = QPushButton("+ Add Team Member")
        btn_add.setObjectName("primaryButton")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(self._on_add_user)
        toolbar.addWidget(btn_add)

        self.btn_reset_pwd = QPushButton("Reset Password")
        self.btn_reset_pwd.setObjectName("secondaryButton")
        self.btn_reset_pwd.clicked.connect(self._on_reset_password)
        self.btn_reset_pwd.setEnabled(False)
        toolbar.addWidget(self.btn_reset_pwd)

        self.btn_change_role = QPushButton("Change Role")
        self.btn_change_role.setObjectName("secondaryButton")
        self.btn_change_role.clicked.connect(self._on_change_role)
        self.btn_change_role.setEnabled(False)
        toolbar.addWidget(self.btn_change_role)

        self.btn_delete = QPushButton("Delete User")
        self.btn_delete.setStyleSheet("QPushButton { background: #FEE2E2; color: #DC2626; border: 1px solid #FCA5A5; border-radius: 6px; padding: 5px 10px; font-size: 12px; }")
        self.btn_delete.clicked.connect(self._on_delete_user)
        self.btn_delete.setEnabled(False)
        toolbar.addWidget(self.btn_delete)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Username / Email", "Role & Tier", "2FA Status", "Must Reset Pwd", "Created Date"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in (1, 2, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

        btn_bottom = QHBoxLayout()
        btn_bottom.addStretch()
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_bottom.addWidget(btn_close)
        layout.addLayout(btn_bottom)

    def _load_users(self) -> None:
        try:
            self.users = self.auth_service.list_users()
            self.table.setRowCount(len(self.users))
            for row, u in enumerate(self.users):
                u_item = QTableWidgetItem(u.username)
                u_item.setData(Qt.ItemDataRole.UserRole, u.id)
                self.table.setItem(row, 0, u_item)
                r_val = u.role.value if hasattr(u.role, "value") else str(u.role)
                self.table.setItem(row, 1, QTableWidgetItem(r_val))
                self.table.setItem(row, 2, QTableWidgetItem("Enabled" if u.is_totp_enabled else "Disabled"))
                self.table.setItem(row, 3, QTableWidgetItem("Yes" if u.must_change_password else "No"))
                dt_str = u.created_at.strftime("%Y-%m-%d %H:%M") if u.created_at else "-"
                self.table.setItem(row, 4, QTableWidgetItem(dt_str))
            self._on_selection_changed()
        except Exception as e:
            QMessageBox.critical(self, "Error Loading Users", str(e))

    def _get_selected_user(self) -> User | None:
        sel = self.table.selectionModel().selectedRows()
        return self.users[sel[0].row()] if sel and 0 <= sel[0].row() < len(self.users) else None

    def _on_selection_changed(self) -> None:
        user = self._get_selected_user()
        has_sel = user is not None
        self.btn_reset_pwd.setEnabled(has_sel)
        self.btn_change_role.setEnabled(has_sel)
        self.btn_delete.setEnabled(has_sel and not (self.current_session and user.id == self.current_session.user_id))

    def _on_add_user(self) -> None:
        dlg = CreateUserSubDialog(self.auth_service, self)
        if dlg.exec():
            self._load_users()

    def _on_reset_password(self) -> None:
        user = self._get_selected_user()
        if user and ResetPasswordSubDialog(self.auth_service, user, self).exec():
            self._load_users()

    def _on_change_role(self) -> None:
        user = self._get_selected_user()
        if not user:
            return
        roles = [("Maker (Audit Assistant)", RoleEnum.MAKER), ("Checker (Audit Senior / Manager)", RoleEnum.CHECKER), ("Admin (Engagement Partner / CA)", RoleEnum.ADMIN)]
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Change Role - {user.username}")
        dlg.setFixedWidth(340)
        d_l = QVBoxLayout(dlg)
        d_l.addWidget(QLabel(f"Select role for <b>{user.username}</b>:"))
        combo = QComboBox()
        for label, r_val in roles:
            combo.addItem(label, r_val)
        for idx in range(combo.count()):
            if combo.itemData(idx) == user.role:
                combo.setCurrentIndex(idx)
                break
        d_l.addWidget(combo)
        b_r = QHBoxLayout()
        b_r.addStretch()
        b_c = QPushButton("Cancel")
        b_c.clicked.connect(dlg.reject)
        b_r.addWidget(b_c)
        b_ok = QPushButton("Save Role")
        b_ok.setObjectName("primaryButton")
        b_ok.clicked.connect(dlg.accept)
        b_r.addWidget(b_ok)
        d_l.addLayout(b_r)
        if dlg.exec():
            try:
                self.auth_service.update_user_role(user.id, combo.currentData())
                self._load_users()
            except Exception as e:
                QMessageBox.critical(self, "Error Updating Role", str(e))

    def _on_delete_user(self) -> None:
        user = self._get_selected_user()
        if not user:
            return
        if QMessageBox.question(self, "Confirm Delete", f"Delete user '{user.username}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            try:
                self.auth_service.delete_user(user.id)
                self._load_users()
            except Exception as e:
                QMessageBox.critical(self, "Error Deleting User", str(e))
