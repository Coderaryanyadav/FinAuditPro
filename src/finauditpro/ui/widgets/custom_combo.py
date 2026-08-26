from PySide6.QtWidgets import QComboBox, QStyledItemDelegate
from PySide6.QtCore import Qt, Signal

class CustomComboBox(QComboBox):
    empty_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(QStyledItemDelegate(self))

    def mousePressEvent(self, event):
        if self.count() == 1 and self.itemData(0) is None:
            self.empty_clicked.emit()
            return
        super().mousePressEvent(event)
