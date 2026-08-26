import sys
from PySide6.QtWidgets import QApplication, QMainWindow
from finauditpro.ui.styles import GLOBAL_QSS
app = QApplication(sys.argv)
w = QMainWindow()
w.setStyleSheet(GLOBAL_QSS)
app.processEvents()
