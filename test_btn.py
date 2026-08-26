import sys
from PySide6.QtWidgets import QApplication
from finauditpro.ui.views.document_view import DocumentView
app = QApplication(sys.argv)
from finauditpro.ui.styles import GLOBAL_QSS
app.setStyleSheet(GLOBAL_QSS)
view = DocumentView()
view.show()
sys.exit(app.exec())
