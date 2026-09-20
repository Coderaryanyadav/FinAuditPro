"""Guided Audit Engagement Workflow view providing 4-stage pipeline navigation, factual progress, and stage reason tracking."""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from finauditpro.application.services.guided_workflow_service import (
    EngagementWorkflowDTO,
    GuidedWorkflowService,
    WorkflowStageDTO,
)
from finauditpro.ui.theme import CardWidget, PageHeader


class GuidedWorkflowView(QWidget):
    """Orchestration workspace rendering the 4-stage guided audit workflow pipeline."""

    navigate_to_route = Signal(str)

    def __init__(self, db_manager: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.workflow_service = GuidedWorkflowService(db_manager)
        self.current_engagement_id: str | None = None
        self.workflow_dto: EngagementWorkflowDTO | None = None
        self.active_stage_index: int = 0

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(12)

        # 1. Page Header
        self.header = PageHeader(
            title="Guided Audit Engagement Workflow",
            subtitle="Sequential 4-phase statutory audit execution pipeline (SA 200 / SA 230 / SA 300).",
        )
        layout.addWidget(self.header)

        # 2. Context Pill Banner (Firm | Client | FY | Engagement)
        self.banner_frame = QFrame()
        self.banner_frame.setStyleSheet(
            "QFrame { background: #0F172A; border-radius: 8px; padding: 10px 14px; color: #FFFFFF; }"
        )
        b_layout = QHBoxLayout(self.banner_frame)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(12)

        self.lbl_firm = QLabel("FIRM: N/A")
        self.lbl_firm.setStyleSheet("font-size: 11px; font-weight: 700; color: #94A3B8;")

        self.lbl_client = QLabel("CLIENT: N/A")
        self.lbl_client.setStyleSheet("font-size: 12px; font-weight: 700; color: #38BDF8;")

        self.lbl_fy = QLabel("FY: N/A")
        self.lbl_fy.setStyleSheet("font-size: 11px; font-weight: 700; color: #F59E0B;")

        self.lbl_engagement = QLabel("ENGAGEMENT: Select Engagement")
        self.lbl_engagement.setStyleSheet("font-size: 12px; font-weight: 700; color: #F1F5F9;")

        b_layout.addWidget(self.lbl_firm)
        b_layout.addWidget(QLabel("│"))
        b_layout.addWidget(self.lbl_client)
        b_layout.addWidget(QLabel("│"))
        b_layout.addWidget(self.lbl_fy)
        b_layout.addWidget(QLabel("│"))
        b_layout.addWidget(self.lbl_engagement, stretch=1)
        layout.addWidget(self.banner_frame)

        # 3. 4-Stage Stepper Bar
        stepper_card = CardWidget("AUDIT WORKFLOW STAGES")
        s_layout = QHBoxLayout()
        s_layout.setSpacing(8)

        self.btn_group_stages = QButtonGroup(self)
        self.stage_buttons: list[QPushButton] = []
        stage_names = [
            "1. Setup & Planning",
            "2. Financial Data",
            "3. Fieldwork & Evidence",
            "4. Review & Reporting",
        ]
        btn_style = (
            "QPushButton { background: #F8FAFC; color: #475569; border: 1px solid #CBD5E1; "
            "border-radius: 6px; padding: 8px 12px; font-weight: 600; font-size: 12px; }\n"
            "QPushButton:hover { background: #EFF6FF; color: #0284C7; border-color: #38BDF8; }\n"
            "QPushButton:checked { background: #0284C7; color: #FFFFFF; border-color: #0284C7; font-weight: 700; }"
        )
        for idx, s_name in enumerate(stage_names):
            btn = QPushButton(s_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, i=idx: self._select_stage(i))
            self.btn_group_stages.addButton(btn, idx)
            self.stage_buttons.append(btn)
            s_layout.addWidget(btn, stretch=1)

        self.stage_buttons[0].setChecked(True)
        stepper_card.content_layout.addLayout(s_layout)
        layout.addWidget(stepper_card)

        # 4. Stage Detail Card & Scroll Area
        self.detail_card = CardWidget("STAGE DETAILS & FACTUAL STEP PROGRESS")
        d_layout = QVBoxLayout()
        d_layout.setSpacing(10)

        # Stage Header Box
        sh_box = QHBoxLayout()
        self.lbl_stage_title = QLabel("Stage 1: Setup & Planning")
        self.lbl_stage_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #0F172A;")

        self.lbl_stage_status = QLabel("● In Progress (0%)")
        self.lbl_stage_status.setStyleSheet("font-size: 12px; font-weight: 700; color: #D97706;")

        sh_box.addWidget(self.lbl_stage_title)
        sh_box.addStretch()
        sh_box.addWidget(self.lbl_stage_status)
        d_layout.addLayout(sh_box)

        self.lbl_stage_desc = QLabel("Define materiality, assess audit risks, and scope procedures.")
        self.lbl_stage_desc.setStyleSheet("font-size: 12px; color: #64748B;")
        d_layout.addWidget(self.lbl_stage_desc)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background: #E2E8F0; border: none; border-radius: 4px; }\n"
            "QProgressBar::chunk { background: #0284C7; border-radius: 4px; }"
        )
        d_layout.addWidget(self.progress_bar)

        # Steps Scroll Box
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(
            "QScrollArea { border: 1px solid #E2E8F0; border-radius: 6px; background: #FFFFFF; }"
        )
        self.steps_container = QWidget()
        self.steps_layout = QVBoxLayout(self.steps_container)
        self.steps_layout.setContentsMargins(12, 12, 12, 12)
        self.steps_layout.setSpacing(10)
        self.scroll.setWidget(self.steps_container)
        d_layout.addWidget(self.scroll, stretch=1)

        self.detail_card.content_layout.addLayout(d_layout)
        layout.addWidget(self.detail_card, stretch=1)

    def set_engagement(self, engagement: Any) -> None:
        if hasattr(engagement, "id"):
            self.current_engagement_id = engagement.id
        elif engagement:
            self.current_engagement_id = str(engagement)
        else:
            self.current_engagement_id = None
        self.refresh()

    set_active_engagement = set_engagement

    def refresh(self) -> None:
        if not self.current_engagement_id:
            self.lbl_firm.setText("FIRM: N/A")
            self.lbl_client.setText("CLIENT: N/A")
            self.lbl_fy.setText("FY: N/A")
            self.lbl_engagement.setText("ENGAGEMENT: Please Select Active Engagement")
            self._render_empty_steps()
            return

        self.workflow_dto = self.workflow_service.evaluate_workflow(self.current_engagement_id)
        w = self.workflow_dto

        self.lbl_firm.setText(f"FIRM: {w.firm_name}")
        self.lbl_client.setText(f"CLIENT: {w.client_name}")
        self.lbl_fy.setText(f"FY: {w.financial_year}")
        self.lbl_engagement.setText(f"ENGAGEMENT: {w.engagement_title}")

        self._render_stage(self.active_stage_index)

    def _select_stage(self, index: int) -> None:
        self.active_stage_index = index
        self._render_stage(index)

    def _render_stage(self, index: int) -> None:
        if not self.workflow_dto or index >= len(self.workflow_dto.stages):
            self._render_empty_steps()
            return

        st: WorkflowStageDTO = self.workflow_dto.stages[index]
        self.lbl_stage_title.setText(f"Stage {st.stage_number}: {st.title}")
        self.lbl_stage_desc.setText(st.description)

        status_color = (
            "#16A34A" if st.status == "Complete"
            else ("#D97706" if st.status == "In Progress" else "#64748B")
        )
        self.lbl_stage_status.setText(f"● {st.status} ({st.completion_percentage}%)")
        self.lbl_stage_status.setStyleSheet(
            f"font-size: 12px; font-weight: 700; color: {status_color};"
        )
        self.progress_bar.setValue(int(st.completion_percentage))

        # Clear steps layout
        while self.steps_layout.count() > 0:
            child = self.steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for step in st.steps:
            item_box = QFrame()
            item_box.setStyleSheet(
                "QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; "
                "border-radius: 6px; padding: 8px 12px; }\n"
                "QFrame:hover { border-color: #CBD5E1; }"
            )
            i_layout = QHBoxLayout(item_box)
            i_layout.setContentsMargins(4, 4, 4, 4)

            # Icon & Title
            v_box = QVBoxLayout()
            title_lbl = QLabel(f"{'✔' if step.is_completed else '○'}  {step.title}")
            title_color = "#16A34A" if step.is_completed else "#0F172A"
            title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {title_color};")
            v_box.addWidget(title_lbl)

            if not step.is_completed and step.incomplete_reason:
                reason_lbl = QLabel(f"<b>Status Reason:</b> {step.incomplete_reason}")
                reason_lbl.setStyleSheet("font-size: 11px; color: #DC2626; font-style: italic;")
                v_box.addWidget(reason_lbl)

            i_layout.addLayout(v_box, stretch=1)

            # Action Jump Button
            if step.target_route:
                btn_jump = QPushButton("Open Module ▶")
                btn_jump.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_jump.setStyleSheet(
                    "QPushButton { background: #0284C7; color: #FFFFFF; border: none; "
                    "border-radius: 4px; padding: 5px 10px; font-size: 11px; font-weight: 600; }\n"
                    "QPushButton:hover { background: #0369A1; }"
                )
                btn_jump.clicked.connect(
                    lambda _, r=step.target_route: self.navigate_to_route.emit(r)
                )
                i_layout.addWidget(btn_jump)

            self.steps_layout.addWidget(item_box)

        self.steps_layout.addStretch()

    def _render_empty_steps(self) -> None:
        while self.steps_layout.count() > 0:
            child = self.steps_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        lbl = QLabel("Select an active audit engagement to display guided workflow pipeline.")
        lbl.setStyleSheet("font-size: 12px; color: #94A3B8; font-style: italic;")
        self.steps_layout.addWidget(lbl)
