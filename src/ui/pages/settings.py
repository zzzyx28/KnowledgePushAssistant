"""推送设置页面 —— 推送配置 + 模型配置 + System Prompt 编辑器 + 领域选择。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QCheckBox, QSpinBox, QTimeEdit,
    QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import QTime

from ..styles import (
    BG_CARD, BORDER, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG,
    TEXT_PRIMARY, TEXT_SECONDARY, FONT_MONO, SUCCESS, DANGER
)


class SettingsPage(QWidget):
    """推送设置页面。"""

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题
        title = QLabel("推送设置")
        title.setProperty("cssClass", "page-title")
        layout.addWidget(title)

        desc = QLabel("配置推送计划、模型连接和 Agent 行为策略")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # ── 推送配置 ──
        layout.addWidget(self._section_title("📅 推送计划"))

        self.push_enabled_cb = QCheckBox("启用定时推送")
        layout.addWidget(self.push_enabled_cb)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("推送间隔 (分钟)"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 1440)
        self.interval_spin.setValue(60)
        self.interval_spin.setFixedWidth(100)
        row1.addWidget(self.interval_spin)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("开始时间"))
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(8, 0))
        row2.addWidget(self.start_time)
        row2.addWidget(QLabel("结束时间"))
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(22, 0))
        row2.addWidget(self.end_time)
        row2.addStretch()
        layout.addLayout(row2)

        # ── 模型配置 ──
        layout.addWidget(self._section_title("🤖 模型连接"))

        self.model_name_edit = self._labeled_input("模型名称", "deepseek-chat")
        layout.addLayout(self.model_name_edit)

        self.base_url_edit = self._labeled_input("Base URL", "https://api.deepseek.com")
        layout.addLayout(self.base_url_edit)

        self.api_key_edit = self._labeled_input("API Key", "", echo_mode=QLineEdit.Password)
        layout.addLayout(self.api_key_edit)

        test_row = QHBoxLayout()
        self.test_btn = QPushButton("🔌 测试连接")
        self.test_btn.setProperty("cssClass", "secondary")
        self.test_btn.setFixedHeight(34)
        self.test_btn.clicked.connect(self._test_connection)
        test_row.addWidget(self.test_btn)
        test_row.addStretch()
        layout.addLayout(test_row)

        # ── System Prompt 编辑器 ──
        layout.addWidget(self._section_title("🧠 Agent System Prompt"))

        prompt_hint = QLabel("编辑 Agent 的行为策略。高级用户可自定义推送决策逻辑。")
        prompt_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(prompt_hint)

        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setMinimumHeight(200)
        self.system_prompt_edit.setStyleSheet(f"""
            QTextEdit {{
                font-family: {FONT_MONO};
                font-size: 12px;
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
        """)
        layout.addWidget(self.system_prompt_edit)

        reset_row = QHBoxLayout()
        reset_btn = QPushButton("恢复默认")
        reset_btn.setProperty("cssClass", "secondary")
        reset_btn.setFixedHeight(30)
        reset_btn.clicked.connect(self._reset_prompt)
        reset_row.addWidget(reset_btn)
        reset_row.addStretch()
        layout.addLayout(reset_row)

        # ── 保存按钮 ──
        save_btn = QPushButton("💾 保存设置")
        save_btn.setFixedHeight(42)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                border-radius: {RADIUS_LG};
            }}
            QPushButton:hover {{ background: #5558e6; }}
        """)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        scroll.setWidget(container)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet("font-weight: 700; font-size: 16px; margin-top: 8px; padding-top: 8px;")
        return label

    def _labeled_input(self, label: str, default: str, echo_mode=None) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        lbl = QLabel(label)
        lbl.setFixedWidth(80)
        row.addWidget(lbl)
        edit = QLineEdit(default)
        if echo_mode:
            edit.setEchoMode(echo_mode)
        edit.setProperty("field", label)
        row.addWidget(edit, 1)
        return row

    def _get_field_value(self, widget, label: str) -> str:
        """从 _labeled_input 布局中获取输入框的值。"""
        for i in range(widget.count()):
            item = widget.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLineEdit):
                    return w.text()
        return ""

    def load_settings(self):
        """从数据库加载设置到 UI。"""
        from ...storage import repository as repo
        from ...agent.defaults import DEFAULT_SYSTEM_PROMPT

        with self._session_factory() as session:
            settings = repo.get_all_settings(session)

        self.push_enabled_cb.setChecked(settings.get("push_enabled", True))
        self.interval_spin.setValue(settings.get("push_interval_minutes", 60))

        start_h = settings.get("push_start_hour", 8)
        end_h = settings.get("push_end_hour", 22)
        self.start_time.setTime(QTime(start_h, 0))
        self.end_time.setTime(QTime(end_h, 0))

        # 模型配置字段
        for i in range(self.model_name_edit.count()):
            w = self.model_name_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit):
                w.setText(settings.get("model_name", "deepseek-chat"))
        for i in range(self.base_url_edit.count()):
            w = self.base_url_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit):
                w.setText(settings.get("model_base_url", "https://api.deepseek.com"))
        for i in range(self.api_key_edit.count()):
            w = self.api_key_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit):
                w.setText(settings.get("model_api_key", ""))

        prompt = settings.get("system_prompt", "")
        self.system_prompt_edit.setText(prompt if prompt else DEFAULT_SYSTEM_PROMPT)

    def save_settings(self):
        """保存设置到数据库。"""
        from ...storage import repository as repo
        import json

        model_name = ""
        base_url = ""
        api_key = ""
        for i in range(self.model_name_edit.count()):
            w = self.model_name_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): model_name = w.text()
        for i in range(self.base_url_edit.count()):
            w = self.base_url_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): base_url = w.text()
        for i in range(self.api_key_edit.count()):
            w = self.api_key_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): api_key = w.text()

        data = {
            "push_enabled": self.push_enabled_cb.isChecked(),
            "push_interval_minutes": self.interval_spin.value(),
            "push_start_hour": self.start_time.time().hour(),
            "push_end_hour": self.end_time.time().hour(),
            "model_name": model_name,
            "model_base_url": base_url,
            "model_api_key": api_key,
            "system_prompt": self.system_prompt_edit.toPlainText(),
        }

        with self._session_factory() as session:
            for key, value in data.items():
                repo.set_setting(session, key, json.dumps(value, ensure_ascii=False))

        QMessageBox.information(self, "保存成功", "设置已保存。")

    def _test_connection(self):
        """测试 LLM 连接。"""
        model_name = ""
        base_url = ""
        api_key = ""
        for i in range(self.model_name_edit.count()):
            w = self.model_name_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): model_name = w.text()
        for i in range(self.base_url_edit.count()):
            w = self.base_url_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): base_url = w.text()
        for i in range(self.api_key_edit.count()):
            w = self.api_key_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): api_key = w.text()

        try:
            from ...llm.client import create_client
            client = create_client(base_url, api_key)
            resp = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            QMessageBox.information(self, "连接成功", f"模型响应: {resp.choices[0].message.content}")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", str(e))

    def _reset_prompt(self):
        from ...agent.defaults import DEFAULT_SYSTEM_PROMPT
        reply = QMessageBox.question(
            self, "确认", "确定要恢复默认 System Prompt 吗？当前编辑内容将丢失。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.system_prompt_edit.setText(DEFAULT_SYSTEM_PROMPT)

    def get_settings_dict(self) -> dict:
        """获取当前 UI 中的设置字典。"""
        model_name = ""
        base_url = ""
        api_key = ""
        for i in range(self.model_name_edit.count()):
            w = self.model_name_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): model_name = w.text()
        for i in range(self.base_url_edit.count()):
            w = self.base_url_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): base_url = w.text()
        for i in range(self.api_key_edit.count()):
            w = self.api_key_edit.itemAt(i).widget()
            if isinstance(w, QLineEdit): api_key = w.text()

        return {
            "push_enabled": self.push_enabled_cb.isChecked(),
            "push_interval_minutes": self.interval_spin.value(),
            "push_start_hour": self.start_time.time().hour(),
            "push_end_hour": self.end_time.time().hour(),
            "model_name": model_name,
            "model_base_url": base_url,
            "model_api_key": api_key,
            "system_prompt": self.system_prompt_edit.toPlainText(),
        }
