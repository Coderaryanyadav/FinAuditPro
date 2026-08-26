from PySide6.QtWidgets import QComboBox, QStyledItemDelegate
from PySide6.QtCore import Qt

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(QStyledItemDelegate(self))
