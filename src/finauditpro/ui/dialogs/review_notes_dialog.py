"""Threaded dialog for raising, responding to, and clearing Review Notes on Working Papers."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.working_paper_service import WorkingPaperService
from finauditpro.application.working_paper_dtos import (
    ClearReviewNoteDTO,
    CreateReviewNoteDTO,
    RespondReviewNoteDTO,
)


class ReviewNotesDialog(QDialog):
    """Dialog managing review note conversations."""

    def __init__(
        self,
        working_paper_id: str,
        working_paper_service: WorkingPaperService,
        current_user: str = "Lead Auditor",
        user_role: str = "Manager",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.working_paper_id = working_paper_id
        self.wp_service = working_paper_service
        self.current_user = current_user
        self.user_role = user_role

        self.setWindowTitle("Review Notes Workspace")
        self.resize(700, 500)

        self._init_ui()
        self._load_notes()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # 1. Notes List
        self.notes_list = QListWidget()
        self.notes_list.itemSelectionChanged.connect(self._on_note_selected)
        layout.addWidget(self.notes_list)

        # 2. Raise New Note Group
        raise_box = QGroupBox("Raise New Review Note")
        raise_layout = QVBoxLayout(raise_box)

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Enter review point or feedback for preparer...")

        btn_raise = QPushButton("Raise Review Note")
        btn_raise.clicked.connect(self._on_raise_clicked)

        raise_layout.addWidget(self.note_input)
        raise_layout.addWidget(btn_raise)
        layout.addWidget(raise_box)

        # 3. Action Row for Selected Note
        action_box = QGroupBox("Selected Note Action")
        action_layout = QVBoxLayout(action_box)

        self.response_input = QLineEdit()
        self.response_input.setPlaceholderText("Preparer response...")

        btn_respond = QPushButton("Submit Response")
        btn_respond.clicked.connect(self._on_respond_clicked)

        btn_clear = QPushButton("Clear Note (Reviewer Only)")
        btn_clear.clicked.connect(self._on_clear_clicked)

        row = QHBoxLayout()
        row.addWidget(self.response_input)
        row.addWidget(btn_respond)
        row.addWidget(btn_clear)
        action_layout.addLayout(row)

        layout.addWidget(action_box)

    def _load_notes(self) -> None:
        self.notes_list.clear()
        notes = self.wp_service.list_review_notes(self.working_paper_id)

        for n in notes:
            item_text = f"[{n.status.value.upper()}] Raised by {n.raised_by}: {n.note_text}"
            if n.response_text:
                item_text += f"\n   ➜ Response ({n.responded_by}): {n.response_text}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, n.id)
            self.notes_list.addItem(item)

    def _on_note_selected(self) -> None:
        pass

    def _on_raise_clicked(self) -> None:
        txt = self.note_input.text().strip()
        if not txt:
            return

        self.wp_service.raise_review_note(
            CreateReviewNoteDTO(
                working_paper_id=self.working_paper_id,
                raised_by=self.current_user,
                note_text=txt,
            )
        )
        self.note_input.clear()
        self._load_notes()

    def _on_respond_clicked(self) -> None:
        curr = self.notes_list.currentItem()
        if not curr:
            return
        note_id = curr.data(Qt.UserRole)
        resp_txt = self.response_input.text().strip()
        if not resp_txt:
            return

        self.wp_service.respond_review_note(
            RespondReviewNoteDTO(
                review_note_id=note_id,
                response_text=resp_txt,
                responder=self.current_user,
            )
        )
        self.response_input.clear()
        self._load_notes()

    def _on_clear_clicked(self) -> None:
        curr = self.notes_list.currentItem()
        if not curr:
            return
        note_id = curr.data(Qt.UserRole)

        self.wp_service.clear_review_note(
            ClearReviewNoteDTO(
                review_note_id=note_id,
                reviewer=self.current_user,
            )
        )
        self._load_notes()
