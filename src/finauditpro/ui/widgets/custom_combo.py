from PySide6.QtCore import Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QWidget


class CustomComboBox(QComboBox):
    """Custom QComboBox supporting custom signals on empty dropdown clicks."""

    empty_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setItemDelegate(QStyledItemDelegate(self))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.count() == 1 and self.itemData(0) is None:
            self.empty_clicked.emit()
            return
        super().mousePressEvent(event)
