"""教学对话页面 —— Agent 驱动的对话，可查知识库 + 联网搜索来回答。"""

import json
import threading
import uuid

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtGui import QFont

from ..styles import (
    BG_CARD, BORDER, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG,
    TEXT_PRIMARY, TEXT_SECONDARY, USER_BUBBLE, AI_BUBBLE, BG_MAIN
)


class ChatPage(QWidget):
    """教学对话页面。"""

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory
        self._session_id = str(uuid.uuid4())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(12)

        # 标题
        title = QLabel("教学对话")
        title.setProperty("cssClass", "page-title")
        layout.addWidget(title)

        desc = QLabel("向 AI 提问，Agent 可查询知识库并联网搜索来回答")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # 对话区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(12)

        scroll.setWidget(self.chat_widget)
        layout.addWidget(scroll, 1)

        # 输入区
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("输入你的问题...")
        self.input_edit.setFixedHeight(60)
        self.input_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 8px 12px;
                font-size: 13px;
            }}
        """)
        input_row.addWidget(self.input_edit, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(64, 60)
        self.send_btn.clicked.connect(self._send_message)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

        # 加载历史
        self._load_history()

    def _load_history(self):
        """加载对话历史到 UI。"""
        from ...storage import repository as repo
        with self._session_factory() as session:
            messages = repo.get_chat_history(session, self._session_id, limit=50)
        for msg in messages:
            is_user = msg.role == "user"
            self._add_bubble(msg.content, is_user)

    def _send_message(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self._add_bubble(text, is_user=True)
        self.input_edit.clear()

        from ...storage import repository as repo
        with self._session_factory() as session:
            repo.save_chat_message(session, self._session_id, "user", text)
            settings = repo.get_all_settings(session)
            history_msgs = repo.get_chat_history(session, self._session_id, limit=20)

        model = settings.get("model_name", "deepseek-chat")
        base_url = settings.get("model_base_url", "https://api.deepseek.com")
        api_key = settings.get("model_api_key", "")
        system_prompt = settings.get("system_prompt", "")

        # 构建 messages
        chat_messages = [{"role": "system", "content": system_prompt or "你是教学助手，帮助用户学习知识。"}]
        for m in history_msgs:
            chat_messages.append({"role": m.role, "content": m.content})

        db_session = self._session_factory()

        def run():
            try:
                from ...llm.client import create_client
                from ...agent.tools import TOOL_SCHEMAS, ToolContext, execute_tool

                client = create_client(base_url, api_key)
                ctx = ToolContext(session=db_session)

                for turn in range(6):
                    resp = client.chat.completions.create(
                        model=model,
                        messages=chat_messages,
                        tools=TOOL_SCHEMAS,
                        max_tokens=4096,
                    )
                    msg = resp.choices[0].message

                    if msg.content:
                        self._reply_signal.emit(msg.content)

                    if msg.tool_calls:
                        for tc in msg.tool_calls:
                            args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                            self._tool_signal.emit(f"🔧 正在{tc.function.name}...")
                            result = execute_tool(ctx, tc.function.name, args)
                            chat_messages.append({
                                "role": "assistant",
                                "content": msg.content,
                                "tool_calls": [{
                                    "id": tc.id, "type": "function",
                                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                                }],
                            })
                            chat_messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": result,
                            })
                    else:
                        break
            finally:
                db_session.close()

        self._reply_signal = _ChatSignal()
        self._tool_signal = _ChatSignal()
        self._reply_signal.signal.connect(lambda t: self._on_reply(t))
        self._tool_signal.signal.connect(lambda t: self._on_tool_status(t))
        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        self.send_btn.setEnabled(False)

    def _on_reply(self, text: str):
        self._add_bubble(text, is_user=False)
        from ...storage import repository as repo
        with self._session_factory() as session:
            repo.save_chat_message(session, self._session_id, "assistant", text)
        self.send_btn.setEnabled(True)

    def _on_tool_status(self, text: str):
        status = QLabel(text)
        status.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-style: italic; padding: 4px 0;")
        self.chat_layout.addWidget(status)

    def _add_bubble(self, text: str, is_user: bool):
        bubble = QFrame()
        bg = USER_BUBBLE if is_user else AI_BUBBLE
        text_color = "#ffffff" if is_user else TEXT_PRIMARY
        alignment = Qt.AlignRight if is_user else Qt.AlignLeft

        bubble.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: {RADIUS_MD};
                padding: 10px 14px;
            }}
        """)

        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(0, 0, 0, 0)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"color: {text_color}; font-size: 13px;")
        inner.addWidget(label)

        wrapper = QHBoxLayout()
        if is_user:
            wrapper.addStretch()
        wrapper.addWidget(bubble)
        if not is_user:
            wrapper.addStretch()

        self.chat_layout.addLayout(wrapper)


class _ChatSignal(QWidget):
    signal = Signal(str)
