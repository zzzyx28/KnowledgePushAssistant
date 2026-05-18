"""Agent 执行面板 —— 时间线组件，实时展示 Agent 每一步决策过程。"""

import json
import threading

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

from ..styles import (
    BG_CARD, BORDER, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG,
    TEXT_PRIMARY, TEXT_SECONDARY, FONT_MONO, SUCCESS, WARNING, DANGER
)


class AgentPanel(QWidget):
    """Agent 执行面板 —— 时间线方式展示 ReAct 循环每一步。"""

    push_requested = Signal()

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 头部
        header = QHBoxLayout()
        title = QLabel("Agent 执行面板")
        title.setProperty("cssClass", "page-title")
        header.addWidget(title)
        header.addStretch()

        self.push_btn = QPushButton("🚀  手动推送")
        self.push_btn.setFixedHeight(38)
        self.push_btn.clicked.connect(self.push_requested.emit)
        header.addWidget(self.push_btn)
        layout.addLayout(header)

        desc = QLabel("查看 Agent 的思考、搜索、决策全过程，每步实时更新")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # 时间线滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)

        self.timeline_widget = QWidget()
        self.timeline = QVBoxLayout(self.timeline_widget)
        self.timeline.setAlignment(Qt.AlignTop)
        self.timeline.setSpacing(8)

        scroll.setWidget(self.timeline_widget)
        layout.addWidget(scroll, 1)

    def clear(self):
        """清空时间线。"""
        while self.timeline.count():
            item = self.timeline.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_step(self, step: dict):
        """向时间线添加一个步骤卡片。"""
        step_type = step.get("type", "")
        if step_type == "thought":
            self._add_thought(step.get("content", ""))
        elif step_type == "action":
            self._add_action(step.get("tool_name", ""), step.get("args", {}))
        elif step_type == "observation":
            self._add_observation(step.get("tool_name", ""), step.get("result", ""))
        elif step_type == "final":
            self._add_final(step.get("content", ""), step.get("result", ""))
        elif step_type == "error":
            self._add_error(step.get("content", ""))

    def _add_thought(self, content: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        icon_label = QLabel("💭  思考")
        icon_label.setStyleSheet("font-weight: 600; font-size: 12px; color: #6366f1;")
        layout.addWidget(icon_label)

        text = QLabel(content)
        text.setWordWrap(True)
        text.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px; line-height: 1.5;")
        layout.addWidget(text)

        self.timeline.addWidget(card)

    def _add_action(self, tool_name: str, args: dict):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 3px solid {ACCENT};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon = QLabel("🔧")
        header.addWidget(icon)

        name = QLabel(f"调用工具: {tool_name}")
        name.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {TEXT_PRIMARY};")
        header.addWidget(name)
        header.addStretch()
        layout.addLayout(header)

        args_text = QLabel(json.dumps(args, ensure_ascii=False, indent=2))
        args_text.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {TEXT_SECONDARY};")
        args_text.setWordWrap(True)
        layout.addWidget(args_text)

        self.timeline.addWidget(card)

    def _add_observation(self, tool_name: str, result: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-left: 3px solid #22c55e;
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        header = QHBoxLayout()
        icon = QLabel("👁")
        header.addWidget(icon)
        name = QLabel(f"{tool_name} 返回结果")
        name.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {TEXT_PRIMARY};")
        header.addWidget(name)
        header.addStretch()
        layout.addLayout(header)

        # 尝试 JSON 格式化
        try:
            parsed = json.loads(result)
            display = json.dumps(parsed, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, TypeError):
            display = result[:800]

        result_text = QLabel(display)
        result_text.setStyleSheet(f"font-family: {FONT_MONO}; font-size: 11px; color: {TEXT_SECONDARY};")
        result_text.setWordWrap(True)
        layout.addWidget(result_text)

        self.timeline.addWidget(card)

    def _add_final(self, content: str, result: str = None):
        card = QFrame()
        # 判断是推送还是跳过
        is_push = result and '"status": "success"' in result
        color = SUCCESS if is_push else WARNING
        emoji = "✅" if is_push else "⏭️"

        card.setStyleSheet(f"""
            QFrame {{
                background: {"#f0fdf4" if is_push else "#fffbeb"};
                border: 2px solid {color};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        header = QLabel(f"{emoji}  最终决策")
        header.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {color};")
        layout.addWidget(header)

        if content:
            text = QLabel(content)
            text.setWordWrap(True)
            text.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 13px;")
            layout.addWidget(text)

        self.timeline.addWidget(card)

    def _add_error(self, content: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: #fef2f2;
                border: 2px solid {DANGER};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(4)

        header = QLabel("❌  错误")
        header.setStyleSheet(f"font-weight: 700; font-size: 14px; color: {DANGER};")
        layout.addWidget(header)

        text = QLabel(content)
        text.setWordWrap(True)
        layout.addWidget(text)

        self.timeline.addWidget(card)

    def run_agent_flow(self, llm_client, model: str, system_prompt: str, on_push):
        """在后台线程运行 Agent 流程，通过 Signal 更新 UI。"""
        from ...storage import repository as repo
        from ...agent.react_loop import react_loop

        self.clear()

        # 加入初始提示
        self._add_thought("正在启动 Agent，准备分析推送时机...")

        db_session = self._session_factory()

        def run():
            try:
                for step in react_loop(llm_client, model, system_prompt, db_session, on_push=on_push):
                    self._step_signal.emit(step)
            finally:
                db_session.close()

        self._step_signal = _StepSignal()
        self._step_signal.step.connect(self.add_step)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()


class _StepSignal(QWidget):
    step = Signal(dict)
