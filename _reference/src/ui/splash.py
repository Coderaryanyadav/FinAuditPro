"""
FinAuditPro — Splash Screen
Clean, light splash screen with trust sky blue accent.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal


class SplashScreen(QWidget):
    finished = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 280)

        # Center
        screen = QApplication.primaryScreen().geometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2,
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        # Card
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #ffffff;
                border-radius: 14px;
                border: 1px solid #e2e8f0;
            }
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(44, 44, 44, 36)
        cl.setSpacing(0)

        # Logo row
        logo_row = QHBoxLayout()
        logo_box = QLabel("FA")
        logo_box.setFixedSize(32, 32)
        logo_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_box.setStyleSheet(
            "background: #0284c7; color: #fff; border-radius: 7px;"
            "font-size: 12px; font-weight: 800; border: none;"
        )
        app_name = QLabel("FinAuditPro")
        app_name.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #0f172a; border: none; margin-left: 10px;"
        )
        logo_row.addWidget(logo_box)
        logo_row.addWidget(app_name)
        logo_row.addStretch()
        cl.addLayout(logo_row)
        cl.addSpacing(28)

        # Headline
        headline = QLabel("Smart Financial\nAudit Assistant.")
        headline.setStyleSheet(
            "font-size: 28px; font-weight: 700; color: #0f172a; border: none; letter-spacing: -0.5px;"
        )
        cl.addWidget(headline)
        cl.addStretch()

        # Status
        self.status_lbl = QLabel("Initializing…")
        self.status_lbl.setStyleSheet(
            "font-size: 11px; color: #64748b; border: none; font-weight: 500;"
        )
        cl.addWidget(self.status_lbl)
        cl.addSpacing(10)

        # Progress
        self.bar = QProgressBar()
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(3)
        self.bar.setRange(0, 100)
        self.bar.setStyleSheet("""
            QProgressBar { border:none; background:#e2e8f0; border-radius:1px; }
            QProgressBar::chunk { background:#0284c7; border-radius:1px; }
        """)
        cl.addWidget(self.bar)
        cl.addSpacing(16)

        # Footer
        ver = QLabel("Enterprise v2.4.0")
        ver.setStyleSheet("font-size: 10px; color: #94a3b8; border: none;")
        cl.addWidget(ver)

        outer.addWidget(card)

        self._progress = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    _MESSAGES = {
        10: "Connecting to encrypted database…",
        35: "Loading AI engines…",
        60: "Bootstrapping RAG index…",
        85: "Verifying audit rulesets…",
        98: "Ready.",
    }

    def _tick(self):
        self._progress += 1
        self.bar.setValue(self._progress)
        if self._progress in self._MESSAGES:
            self.status_lbl.setText(self._MESSAGES[self._progress])
        if self._progress >= 100:
            self._timer.stop()
            self.finished.emit()
            self.close()
