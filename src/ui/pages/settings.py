"""推送设置页面 —— macOS 设置式分组布局。"""

import json

from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QCheckBox, QTimeEdit, QMessageBox, QFrame, QSizePolicy,
)

from ..styles import (
    BG_MAIN, BG_CARD, BG_STICKY, BORDER_LIGHT, SEPARATOR, TEXT_PRIMARY,
    TEXT_SECONDARY, TEXT_TERTIARY, ACCENT, ACCENT_FILL, DANGER, SUCCESS,
    FONT_MONO, PAGE_MARGIN_H, PAGE_MARGIN_V, RADIUS_SM, RADIUS_MD, RADIUS_PILL,
    primary_button_style, time_edit_style,
)
from ..widgets import SmoothScrollArea, SettingsGroup, FormRow, StepperSpinBox, PageHeader


class SettingsPage(QWidget):
    """推送设置页面。"""

    settings_saved = Signal()

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = SmoothScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(
            PAGE_MARGIN_H, PAGE_MARGIN_V, PAGE_MARGIN_H, PAGE_MARGIN_V
        )
        layout.setSpacing(36)
        layout.addWidget(PageHeader("设置", "推送计划、模型连接与 Agent 行为"))

        # ── 推送计划 ──
        push_group = SettingsGroup("推送计划")

        self.push_enabled_cb = QCheckBox("启用定时推送")
        push_group.add_row(self.push_enabled_cb, divider=False)

        self.interval_stepper = StepperSpinBox(
            minimum=5, maximum=1440, value=60, suffix="分钟"
        )
        push_group.add_row(
            FormRow("推送间隔", self.interval_stepper, "两次自动推送之间的最短间隔")
        )

        time_wrap = QWidget()
        tw = QHBoxLayout(time_wrap)
        tw.setContentsMargins(0, 0, 0, 0)
        tw.setSpacing(12)

        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(8, 0))
        self.start_time.setDisplayFormat("HH:mm")
        self.start_time.setStyleSheet(time_edit_style())
        self.start_time.setFixedWidth(110)

        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(22, 0))
        self.end_time.setDisplayFormat("HH:mm")
        self.end_time.setStyleSheet(time_edit_style())
        self.end_time.setFixedWidth(110)

        tw.addWidget(self._time_block("开始", self.start_time))
        tw.addWidget(self._time_block("结束", self.end_time))
        tw.addStretch()

        push_group.add_row(
            FormRow("推送时段", time_wrap, "仅在该时间段内执行自动推送"),
            divider=False,
        )
        layout.addWidget(push_group)

        # ── 模型连接 ──
        model_group = SettingsGroup("模型连接")

        self._model_name = QLineEdit()
        self._model_name.setPlaceholderText("deepseek-chat")
        self._model_name.setFixedHeight(38)
        model_group.add_row(
            FormRow("模型名称", self._model_name), divider=False
        )

        self._base_url = QLineEdit()
        self._base_url.setPlaceholderText("https://api.deepseek.com")
        self._base_url.setFixedHeight(38)
        model_group.add_row(FormRow("接口地址", self._base_url))

        # API Key with show/hide
        key_wrap = QWidget()
        kw = QHBoxLayout(key_wrap)
        kw.setContentsMargins(0, 0, 0, 0)
        kw.setSpacing(10)
        self._api_key = QLineEdit()
        self._api_key.setEchoMode(QLineEdit.Password)
        self._api_key.setFixedHeight(38)
        self._api_key.setPlaceholderText("sk-...")
        kw.addWidget(self._api_key, 1)

        self._show_key_btn = QPushButton("显示")
        self._show_key_btn.setCheckable(True)
        self._show_key_btn.setFixedHeight(30)
        self._show_key_btn.setCursor(Qt.PointingHandCursor)
        self._show_key_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_PILL};
                font-size: 12px;
                font-weight: 500;
                padding: 4px 14px;
            }}
            QPushButton:hover {{ color: {TEXT_PRIMARY}; border-color: {TEXT_TERTIARY}; }}
            QPushButton:checked {{
                color: {ACCENT};
                border-color: {ACCENT};
                background: {ACCENT_FILL};
            }}
        """)
        self._show_key_btn.toggled.connect(self._toggle_key_visibility)
        kw.addWidget(self._show_key_btn, 0, Qt.AlignVCenter)
        model_group.add_row(FormRow("API Key", key_wrap))

        # Test connection
        test_row = QWidget()
        tr = QHBoxLayout(test_row)
        tr.setContentsMargins(0, 0, 0, 0)
        self.test_btn = QPushButton("测试连接")
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.test_btn.setFixedHeight(34)
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT_FILL};
                color: {ACCENT};
                border: none;
                border-radius: {RADIUS_SM};
                font-size: 13px;
                font-weight: 600;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: #D8EBFF; }}
        """)
        self.test_btn.clicked.connect(self._test_connection)
        tr.addWidget(self.test_btn)

        self.test_status = QLabel()
        self.test_status.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-size: 12px;"
        )
        tr.addWidget(self.test_status)
        tr.addStretch()
        model_group.add_row(test_row, divider=False)
        layout.addWidget(model_group)

        # ── Agent 策略 ──
        agent_group = SettingsGroup("Agent 策略")

        # 系统提示词（只读展示）
        sys_prompt_wrap = QWidget()
        spw = QVBoxLayout(sys_prompt_wrap)
        spw.setContentsMargins(0, 0, 0, 0)
        spw.setSpacing(6)

        sys_label = QLabel("系统提示词")
        sys_label.setStyleSheet(
            f"font-size: 14px; font-weight: 500; color: {TEXT_PRIMARY};"
        )
        spw.addWidget(sys_label)
        sys_hint = QLabel("核心行为规则，不可修改。")
        sys_hint.setWordWrap(True)
        sys_hint.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 12px;")
        spw.addWidget(sys_hint)

        self.system_prompt_view = QTextEdit()
        self.system_prompt_view.setReadOnly(True)
        self.system_prompt_view.setMinimumHeight(120)
        self.system_prompt_view.setMaximumHeight(200)
        self.system_prompt_view.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_MAIN};
                font-family: {FONT_MONO};
                font-size: 11px;
                line-height: 1.55;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_MD};
            }}
        """)
        spw.addWidget(self.system_prompt_view)
        agent_group.add_row(sys_prompt_wrap, divider=False)

        # 用户偏好提示词（可编辑）
        user_prompt_wrap = QWidget()
        upw = QVBoxLayout(user_prompt_wrap)
        upw.setContentsMargins(0, 0, 0, 0)
        upw.setSpacing(6)

        user_label = QLabel("用户偏好")
        user_label.setStyleSheet(
            f"font-size: 14px; font-weight: 500; color: {TEXT_PRIMARY};"
        )
        upw.addWidget(user_label)
        user_hint = QLabel("描述你关注的主题、期望的推送风格或特定需求，将与系统提示词共同作用。")
        user_hint.setWordWrap(True)
        user_hint.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 12px;")
        upw.addWidget(user_hint)

        self.user_preference_edit = QTextEdit()
        self.user_preference_edit.setPlaceholderText("例如：我关注后端架构与分布式系统，希望每次推送都有可执行的代码示例，语言尽量通俗易懂…")
        self.user_preference_edit.setMinimumHeight(100)
        self.user_preference_edit.setMaximumHeight(200)
        self.user_preference_edit.setStyleSheet(f"""
            QTextEdit {{
                font-family: {FONT_MONO};
                font-size: 12px;
                line-height: 1.6;
            }}
        """)
        upw.addWidget(self.user_preference_edit)

        upw_footer = QHBoxLayout()
        self.user_prompt_char_count = QLabel()
        self.user_prompt_char_count.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-size: 11px;"
        )
        upw_footer.addWidget(self.user_prompt_char_count)
        upw_footer.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.setFixedHeight(30)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_SM};
                font-size: 12px;
                font-weight: 500;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                color: {DANGER};
                border-color: {DANGER};
            }}
        """)
        clear_btn.clicked.connect(lambda: self.user_preference_edit.clear())
        upw_footer.addWidget(clear_btn)
        upw.addLayout(upw_footer)

        agent_group.add_row(user_prompt_wrap, divider=False)
        layout.addWidget(agent_group)

        # 底部留白（为 sticky save bar 腾出空间）
        layout.addSpacing(72)
        scroll.setWidget(container)

        # ── 底部 sticky 保存栏 ──
        sticky_bar = QFrame()
        sticky_bar.setFixedHeight(72)
        sticky_bar.setStyleSheet(f"""
            QFrame {{
                background: {BG_STICKY};
                border-top: 1px solid {SEPARATOR};
            }}
        """)
        sticky_layout = QHBoxLayout(sticky_bar)
        sticky_layout.setContentsMargins(PAGE_MARGIN_H, 0, PAGE_MARGIN_H, 0)
        sticky_layout.setSpacing(0)

        save_hint = QLabel()
        save_hint.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 12px;")
        sticky_layout.addWidget(save_hint)
        sticky_layout.addStretch()

        save_btn = QPushButton("保存设置")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setFixedHeight(42)
        save_btn.setStyleSheet(primary_button_style(height=42, large=True))
        save_btn.clicked.connect(self.save_settings)
        sticky_layout.addWidget(save_btn)

        outer.addWidget(scroll, 1)
        outer.addWidget(sticky_bar)

        # 连接字符计数（用户偏好）
        self.user_preference_edit.textChanged.connect(
            lambda: self.user_prompt_char_count.setText(
                f"{len(self.user_preference_edit.toPlainText())} 字符"
            )
        )

    def _toggle_key_visibility(self, checked: bool):
        self._api_key.setEchoMode(
            QLineEdit.Normal if checked else QLineEdit.Password
        )
        self._show_key_btn.setText("隐藏" if checked else "显示")

    @staticmethod
    def _time_block(label: str, widget: QTimeEdit) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 500; color: {TEXT_SECONDARY};"
        )
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return w

    def load_settings(self):
        from ...storage import repository as repo
        from ...agent.defaults import DEFAULT_SYSTEM_PROMPT

        with self._session_factory() as session:
            settings = repo.get_all_settings(session)

        self.push_enabled_cb.setChecked(settings.get("push_enabled", True))
        self.interval_stepper.setValue(settings.get("push_interval_minutes", 60))
        self.start_time.setTime(QTime(settings.get("push_start_hour", 8), 0))
        self.end_time.setTime(QTime(settings.get("push_end_hour", 22), 0))

        self._model_name.setText(settings.get("model_name", "deepseek-chat"))
        self._base_url.setText(
            settings.get("model_base_url", "https://api.deepseek.com")
        )
        self._api_key.setText(settings.get("model_api_key", ""))

        # 系统提示词始终显示默认值（只读）
        self.system_prompt_view.setText(DEFAULT_SYSTEM_PROMPT)

        # 用户偏好
        user_pref = settings.get("user_preference_prompt", "")
        self.user_preference_edit.setText(user_pref if user_pref else "")

    def save_settings(self):
        from ...storage import repository as repo

        data = {
            "push_enabled": self.push_enabled_cb.isChecked(),
            "push_interval_minutes": self.interval_stepper.value(),
            "push_start_hour": self.start_time.time().hour(),
            "push_end_hour": self.end_time.time().hour(),
            "model_name": self._model_name.text().strip(),
            "model_base_url": self._base_url.text().strip(),
            "model_api_key": self._api_key.text().strip(),
            "user_preference_prompt": self.user_preference_edit.toPlainText(),
        }

        with self._session_factory() as session:
            for key, value in data.items():
                repo.set_setting(session, key, json.dumps(value, ensure_ascii=False))

        self.settings_saved.emit()
        QMessageBox.information(self, "保存成功", "设置已保存。")

    def _test_connection(self):
        self.test_status.setText("正在连接...")
        self.test_status.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 12px;")
        self.test_btn.setEnabled(False)

        try:
            from ...llm.client import create_client

            client = create_client(
                self._base_url.text().strip(), self._api_key.text().strip()
            )
            resp = client.chat.completions.create(
                model=self._model_name.text().strip(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10,
            )
            self.test_status.setText("连接成功")
            self.test_status.setStyleSheet(
                f"color: {SUCCESS}; font-size: 12px; font-weight: 600;"
            )
        except Exception as e:
            self.test_status.setText(f"失败：{str(e)[:60]}")
            self.test_status.setStyleSheet(
                f"color: {DANGER}; font-size: 12px;"
            )
        finally:
            self.test_btn.setEnabled(True)

    def get_settings_dict(self) -> dict:
        return {
            "push_enabled": self.push_enabled_cb.isChecked(),
            "push_interval_minutes": self.interval_stepper.value(),
            "push_start_hour": self.start_time.time().hour(),
            "push_end_hour": self.end_time.time().hour(),
            "model_name": self._model_name.text().strip(),
            "model_base_url": self._base_url.text().strip(),
            "model_api_key": self._api_key.text().strip(),
            "user_preference_prompt": self.user_preference_edit.toPlainText(),
        }
