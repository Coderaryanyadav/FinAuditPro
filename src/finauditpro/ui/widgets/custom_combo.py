from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QMouseEvent, QPalette
from PySide6.QtWidgets import QComboBox, QStyledItemDelegate, QWidget


class CustomComboBox(QComboBox):
    """Custom QComboBox supporting custom signals on empty dropdown clicks and resilient styling."""

    empty_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setItemDelegate(QStyledItemDelegate(self))

        self.setStyleSheet("""
            QComboBox {
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 30px 6px 12px;
                font-size: 13px;
                color: #0F172A;
                background-color: #FFFFFF;
                min-height: 22px;
            }
            QComboBox:hover {
                border-color: #94A3B8;
            }
            QComboBox:focus {
                border-color: #2563EB;
                background-color: #FFFFFF;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                width: 26px;
                border: none;
                background: transparent;
            }
            QComboBox::down-arrow {
                image: url(src/finauditpro/assets/icons/chevron_down.png);
                width: 14px;
                height: 14px;
                margin-right: 8px;
            }
        """)

        # Ensure popup listview has forced pure white background and slate text
        view = self.view()
        if view:
            palette = view.palette()
            palette.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
            palette.setColor(QPalette.ColorRole.Text, QColor("#0F172A"))
            palette.setColor(QPalette.ColorRole.Highlight, QColor("#EFF6FF"))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#2563EB"))
            view.setPalette(palette)
            view.setStyleSheet("""
                QAbstractItemView, QListView {
                    background-color: #FFFFFF;
                    color: #0F172A;
                    border: 1px solid #CBD5E1;
                    border-radius: 6px;
                    padding: 4px;
                    outline: none;
                    selection-background-color: #EFF6FF;
                    selection-color: #2563EB;
                }
                QAbstractItemView::item, QListView::item {
                    background-color: #FFFFFF;
                    color: #0F172A;
                    min-height: 28px;
                    padding: 6px 12px;
                    border-radius: 4px;
                    border: 1px solid transparent;
                }
                QAbstractItemView::item:hover, QListView::item:hover {
                    background-color: #F1F5F9;
                    color: #0F172A;
                }
                QAbstractItemView::item:selected, QListView::item:selected {
                    background-color: #EFF6FF;
                    color: #2563EB;
                    font-weight: 600;
                }
            """)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.count() == 1 and self.itemData(0) is None:
            self.empty_clicked.emit()
        super().mousePressEvent(event)
