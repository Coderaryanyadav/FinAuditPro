"""Standardized destructive action confirmation and actionable user feedback dialogs."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


def confirm_destructive_action(
    parent: QWidget | None,
    title: str,
    message: str,
    confirm_label: str = "Confirm Action",
) -> bool:
    """Prompt user with a explicit desktop-native confirmation dialog before executing a destructive action."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setFixedSize(440, 210)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setStyleSheet(
        "QDialog { background-color: #FFFFFF; border-radius: 8px; }"
        "QLabel#confirmTitle { font-size: 16px; font-weight: 700; color: #DC2626; }"
        "QLabel#confirmMsg { font-size: 13px; color: #475569; }"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(12)

    t_lbl = QLabel(title, dialog)
    t_lbl.setObjectName("confirmTitle")
    layout.addWidget(t_lbl)

    m_lbl = QLabel(message, dialog)
    m_lbl.setObjectName("confirmMsg")
    m_lbl.setWordWrap(True)
    layout.addWidget(m_lbl)

    layout.addStretch()

    b_row = QHBoxLayout()
    b_row.setSpacing(10)
    b_row.addStretch()

    cancel_btn = QPushButton("Cancel", dialog)
    cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    cancel_btn.setStyleSheet(
        "QPushButton { background-color: #FFFFFF; color: #475569; border: 1px solid #CBD5E1; border-radius: 6px; padding: 7px 16px; font-weight: 500; }"
        "QPushButton:hover { background-color: #F8FAFC; border-color: #94A3B8; }"
    )
    cancel_btn.clicked.connect(dialog.reject)

    action_btn = QPushButton(confirm_label, dialog)
    action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    action_btn.setStyleSheet(
        "QPushButton { background-color: #DC2626; color: #FFFFFF; border: 1px solid #DC2626; border-radius: 6px; padding: 7px 16px; font-weight: 600; }"
        "QPushButton:hover { background-color: #B91C1C; }"
    )
    action_btn.clicked.connect(dialog.accept)

    b_row.addWidget(cancel_btn)
    b_row.addWidget(action_btn)
    layout.addLayout(b_row)

    return dialog.exec() == QDialog.DialogCode.Accepted


def show_actionable_error(
    parent: QWidget | None,
    title: str,
    message: str,
    next_steps: str = "Please verify your input or check entity state before retrying.",
) -> None:
    """Display clean error dialog explaining failure and giving explicit next steps to the user."""
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Error — {title}")
    dialog.setFixedSize(460, 230)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setStyleSheet(
        "QDialog { background-color: #FFFFFF; border-radius: 8px; }"
        "QLabel#errTitle { font-size: 15px; font-weight: 700; color: #B91C1C; }"
        "QLabel#errMsg { font-size: 13px; color: #334155; }"
        "QLabel#errSteps { font-size: 12px; color: #64748B; background: #FEF2F2; border: 1px solid #FEE2E2; border-radius: 6px; padding: 8px 12px; }"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)

    t_lbl = QLabel(title, dialog)
    t_lbl.setObjectName("errTitle")
    layout.addWidget(t_lbl)

    m_lbl = QLabel(message, dialog)
    m_lbl.setObjectName("errMsg")
    m_lbl.setWordWrap(True)
    layout.addWidget(m_lbl)

    s_lbl = QLabel(f"<b>What to do next:</b> {next_steps}", dialog)
    s_lbl.setObjectName("errSteps")
    s_lbl.setWordWrap(True)
    layout.addWidget(s_lbl)

    layout.addStretch()

    b_row = QHBoxLayout()
    b_row.addStretch()

    ok_btn = QPushButton("OK", dialog)
    ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    ok_btn.setStyleSheet(
        "QPushButton { background-color: #2563EB; color: #FFFFFF; border: none; border-radius: 6px; padding: 7px 20px; font-weight: 600; }"
        "QPushButton:hover { background-color: #1D4ED8; }"
    )
    ok_btn.clicked.connect(dialog.accept)
    b_row.addWidget(ok_btn)

    layout.addLayout(b_row)
    dialog.exec()


def show_success_feedback(parent: QWidget | None, title: str, message: str) -> None:
    """Display standard success feedback to the user."""
    dialog = QDialog(parent)
    dialog.setWindowTitle("Success")
    dialog.setFixedSize(400, 180)
    dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
    dialog.setStyleSheet(
        "QDialog { background-color: #FFFFFF; border-radius: 8px; }"
        "QLabel#succTitle { font-size: 15px; font-weight: 700; color: #15803D; }"
        "QLabel#succMsg { font-size: 13px; color: #334155; }"
    )

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(10)

    t_lbl = QLabel(title, dialog)
    t_lbl.setObjectName("succTitle")
    layout.addWidget(t_lbl)

    m_lbl = QLabel(message, dialog)
    m_lbl.setObjectName("succMsg")
    m_lbl.setWordWrap(True)
    layout.addWidget(m_lbl)

    layout.addStretch()

    b_row = QHBoxLayout()
    b_row.addStretch()

    ok_btn = QPushButton("OK", dialog)
    ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
    ok_btn.setStyleSheet(
        "QPushButton { background-color: #16A34A; color: #FFFFFF; border: none; border-radius: 6px; padding: 7px 20px; font-weight: 600; }"
        "QPushButton:hover { background-color: #15803D; }"
    )
    ok_btn.clicked.connect(dialog.accept)
    b_row.addWidget(ok_btn)

    layout.addLayout(b_row)
    dialog.exec()
