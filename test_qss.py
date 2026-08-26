import sys
from PySide6.QtWidgets import QApplication, QWidget
from finauditpro.ui.styles import GLOBAL_QSS
app = QApplication(sys.argv)
w = QWidget()
w.setStyleSheet(GLOBAL_QSS)
print("No errors" if not app.instance().styleSheet() else "Error")
