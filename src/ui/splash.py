from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt, QTimer, Signal

class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 340)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Container to act as the glass panel
        self.container = QWidget(self)
        self.container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.5);
            }
        """)
        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo/Title
        self.title = QLabel("FinAuditPro")
        self.title.setStyleSheet("font-size: 42px; font-weight: bold; color: #0f172a; background: transparent; border: none;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle = QLabel("Smart Financial Audit Assistant")
        self.subtitle.setStyleSheet("font-size: 16px; color: #64748b; font-weight: 500; background: transparent; border: none;")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #e2e8f0;
                border-radius: 3px;
                border: none;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0ea5e9, stop:1 #38bdf8);
                border-radius: 3px;
            }
        """)

        # Status text
        self.status = QLabel("Initializing AI Engine...")
        self.status.setStyleSheet("font-size: 11px; color: #94a3b8; font-weight: 600; text-transform: uppercase; background: transparent; border: none;")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        container_layout.addStretch()
        container_layout.addWidget(self.title)
        container_layout.addWidget(self.subtitle)
        container_layout.addSpacing(40)
        container_layout.addWidget(self.status)
        container_layout.addWidget(self.progress_bar)
        container_layout.addStretch()
        
        layout.addWidget(self.container)

        self.progress = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(25)

    def update_progress(self):
        self.progress += 1
        self.progress_bar.setValue(self.progress)
        
        if self.progress == 30:
            self.status.setText("Establishing Secure Connection...")
        elif self.progress == 60:
            self.status.setText("Initializing Machine Learning Models...")
        elif self.progress == 85:
            self.status.setText("Verifying Compliance Rulesets...")
            
        if self.progress >= 100:
            self.timer.stop()
            self.finished.emit()
            self.close()
