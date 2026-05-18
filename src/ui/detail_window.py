"""知识详情窗口 —— 沉浸式阅读 + 常驻问答栏。"""

import datetime
import threading
import webbrowser

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QLineEdit, QSplitter,
)

from .styles import (
    BG_CARD, BG_MAIN, BG_TITLEBAR, BG_SUBTLE,
    BORDER_LIGHT, SEPARATOR, ACCENT,
    RADIUS_SM, RADIUS_MD, RADIUS_XL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, DANGER,
    USER_BUBBLE, AI_BUBBLE,
    primary_button_style, scroll_bar_style, BG_FILL, BG_SIDEBAR,
)
from .markdown_html import render_markdown_to_html
from .knowledge_ask import build_ask_system_prompt
from .widgets import AutoHeightBrowser


def _time_ago(dt: datetime.datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    diff = now - dt
    if diff.days == 0:
        mins = max(diff.seconds // 60, 0)
        return "今天" if mins < 1 else f"{mins} 分钟前" if mins < 60 else f"{diff.seconds // 3600} 小时前"
    if diff.days == 1:
        return "昨天"
    if diff.days < 7:
        return f"{diff.days} 天前"
    return dt.strftime("%Y-%m-%d")


class DetailWindow(QWidget):
    """知识详情窗口。"""

    _ask_reply = Signal(str)
    _ask_error = Signal(str)
    _ask_finished = Signal()

    def __init__(self, item, db_session_factory, parent=None):
        super().__init__(parent)
        self._item = item
        self._item_id = item.id
        self._session_factory = db_session_factory
        self._ask_messages: list[dict] = []
        self._ask_busy = False

        self._ask_reply.connect(self._on_ask_reply)
        self._ask_error.connect(self._on_ask_error)
        self._ask_finished.connect(self._on_ask_finished)

        self.setWindowTitle(item.title or "知识详情")
        self.setMinimumSize(720, 680)
        self.resize(820, 680)
        self.setStyleSheet(f"QWidget {{ background: {BG_MAIN}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── 顶栏 ──
        bar = QFrame()
        bar.setFixedHeight(48)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {BG_TITLEBAR};
                border-bottom: 1px solid {SEPARATOR};
            }}
        """)
        bl = QHBoxLayout(bar)
        bl.setContentsMargins(16, 0, 14, 0)

        bar_title = QLabel("知识详情")
        bar_title.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {TEXT_PRIMARY};"
        )
        bl.addWidget(bar_title)
        bl.addStretch()

        done_btn = QPushButton("完成")
        done_btn.setCursor(Qt.PointingHandCursor)
        done_btn.setStyleSheet(primary_button_style(height=30))
        done_btn.setFixedHeight(30)
        done_btn.clicked.connect(self.close)
        bl.addWidget(done_btn)
        root.addWidget(bar)

        # ── 上下分栏：内容 + 问答 ──
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {SEPARATOR};
            }}
        """)

        # 上半：可滚动正文
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.NoFrame)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_scroll.setStyleSheet(
            f"QScrollArea {{ background: {BG_MAIN}; border: none; }}"
        )
        content_scroll.verticalScrollBar().setStyleSheet(scroll_bar_style())

        content_body = QWidget()
        content_layout = QVBoxLayout(content_body)
        content_layout.setContentsMargins(40, 32, 40, 32)
        content_layout.setSpacing(24)

        # ── 文章（无框线）──
        article = QFrame()
        article.setStyleSheet(
            f"QFrame {{ background: transparent; border: none; }}"
        )

        al = QVBoxLayout(article)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(22)

        # 元信息行
        meta = QHBoxLayout()
        meta.setSpacing(10)
        tag = QLabel(item.domain_name or "未分类")
        tag.setStyleSheet(f"""
            background: {BG_SIDEBAR};
            color: {TEXT_SECONDARY};
            border-radius: {RADIUS_SM};
            padding: 3px 10px;
            font-size: 12px;
            font-weight: 600;
        """)
        meta.addWidget(tag, 0, Qt.AlignVCenter)
        if item.created_at:
            t = QLabel(_time_ago(item.created_at))
            t.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 13px;")
            meta.addWidget(t, 0, Qt.AlignVCenter)
        meta.addStretch()
        al.addLayout(meta)

        # 标题
        title = QLabel(item.title or "无标题")
        title.setWordWrap(True)
        title.setStyleSheet(
            f"font-weight: 700; font-size: 26px; color: {TEXT_PRIMARY}; "
            f"letter-spacing: -0.5px; line-height: 1.25;"
        )
        al.addWidget(title)

        # 摘要
        if item.summary:
            s = QLabel(item.summary)
            s.setWordWrap(True)
            s.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 15px; line-height: 1.6;"
            )
            al.addWidget(s)

        # 分隔线 + 来源链接
        meta2 = QHBoxLayout()
        meta2.setSpacing(0)
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {BORDER_LIGHT}; border: none;")
        meta2.addWidget(sep, 1)
        if item.source_url:
            meta2.addSpacing(16)
            src = QPushButton("查看原文")
            src.setCursor(Qt.PointingHandCursor)
            src.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    color: {ACCENT}; font-size: 12px; font-weight: 500;
                }}
                QPushButton:hover {{ color: #0066D6; }}
            """)
            src.clicked.connect(lambda: webbrowser.open(item.source_url))
            meta2.addWidget(src, 0, Qt.AlignVCenter)
        al.addLayout(meta2)

        # 正文
        browser = AutoHeightBrowser()
        browser.setHtml(render_markdown_to_html(item.detail))
        al.addWidget(browser)

        content_layout.addWidget(article)
        content_scroll.setWidget(content_body)

        # 下半：常驻问答栏
        self._ask_panel = self._build_ask_panel()

        self._splitter = splitter
        splitter.addWidget(content_scroll)
        splitter.addWidget(self._ask_panel)
        splitter.setSizes([self.height() - 40, 40])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, True)
        root.addWidget(splitter, 1)

    def _build_ask_panel(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame#askPanel {{
                background: {BG_CARD};
                border-top: 1px solid {SEPARATOR};
            }}
        """)
        panel.setObjectName("askPanel")
        play = QVBoxLayout(panel)
        play.setContentsMargins(0, 0, 0, 0)
        play.setSpacing(0)

        # Header bar
        ask_header = QFrame()
        ask_header.setFixedHeight(40)
        ask_header.setStyleSheet(f"""
            QFrame {{
                background: {BG_SUBTLE};
                border-bottom: 1px solid {BORDER_LIGHT};
            }}
        """)
        hl = QHBoxLayout(ask_header)
        hl.setContentsMargins(20, 0, 20, 0)
        hl.setSpacing(0)

        ask_title = QLabel("问一问")
        ask_title.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: {TEXT_PRIMARY};"
        )
        hl.addWidget(ask_title)

        hint = QLabel("基于本条知识提问，AI 即时回答")
        hint.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-size: 11px;"
        )
        hl.addSpacing(10)
        hl.addWidget(hint)
        hl.addStretch()

        self._ask_collapse_btn = QPushButton("—")
        self._ask_collapse_btn.setCursor(Qt.PointingHandCursor)
        self._ask_collapse_btn.setFixedSize(28, 28)
        self._ask_collapse_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 500;
                border-radius: {RADIUS_SM};
            }}
            QPushButton:hover {{
                background: {BG_FILL}; color: {TEXT_PRIMARY};
            }}
        """)
        self._ask_collapse_btn.clicked.connect(self._toggle_ask_collapse)
        hl.addWidget(self._ask_collapse_btn)
        play.addWidget(ask_header)

        # Bubbles area
        self._ask_scroll = QScrollArea()
        self._ask_scroll.setWidgetResizable(True)
        self._ask_scroll.setFrameShape(QFrame.NoFrame)
        self._ask_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._ask_scroll.setStyleSheet(
            f"QScrollArea {{ background: {BG_MAIN}; border: none; }}"
        )
        self._ask_scroll.verticalScrollBar().setStyleSheet(scroll_bar_style())

        self._ask_bubbles = QWidget()
        self._ask_bubble_layout = QVBoxLayout(self._ask_bubbles)
        self._ask_bubble_layout.setAlignment(Qt.AlignTop)
        self._ask_bubble_layout.setSpacing(12)
        self._ask_bubble_layout.setContentsMargins(24, 16, 24, 16)
        self._ask_scroll.setWidget(self._ask_bubbles)
        play.addWidget(self._ask_scroll, 1)

        # Composer
        self._ask_composer = QFrame()
        self._ask_composer.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border-top: 1px solid {BORDER_LIGHT};
            }}
        """)
        cl = QHBoxLayout(self._ask_composer)
        cl.setContentsMargins(20, 12, 16, 14)
        cl.setSpacing(10)

        self._ask_input = QLineEdit()
        self._ask_input.setPlaceholderText("基于本条知识提问…")
        self._ask_input.setFixedHeight(38)
        self._ask_input.setStyleSheet(f"""
            QLineEdit {{
                background: {BG_MAIN};
                border: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_MD};
                padding: 0 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border: 2px solid {ACCENT};
                padding: 0 15px;
            }}
        """)
        self._ask_input.returnPressed.connect(self._send_ask)
        cl.addWidget(self._ask_input, 1)

        send_btn = QPushButton("发送")
        send_btn.setFixedSize(60, 38)
        send_btn.setCursor(Qt.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT}; color: #FFFFFF; border: none;
                border-radius: {RADIUS_MD}; font-size: 13px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #0077ED; }}
            QPushButton:pressed {{ background: #006ADB; }}
            QPushButton:disabled {{
                background: {BG_FILL}; color: {TEXT_TERTIARY};
            }}
        """)
        send_btn.clicked.connect(self._send_ask)
        cl.addWidget(send_btn)
        play.addWidget(self._ask_composer)

        # 空状态提示
        self._ask_empty_hint = QLabel("在下方输入你的问题，AI 将基于本条知识内容进行回答")
        self._ask_empty_hint.setAlignment(Qt.AlignCenter)
        self._ask_empty_hint.setWordWrap(True)
        self._ask_empty_hint.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-size: 13px; padding: 32px;"
        )
        # Insert into bubbles area before scroll
        self._ask_bubble_layout.addWidget(self._ask_empty_hint)

        self._ask_collapsed = True
        self._ask_scroll.hide()
        self._ask_composer.hide()

        return panel

    def _toggle_ask_collapse(self):
        if self._ask_collapsed:
            self._ask_scroll.show()
            self._ask_composer.show()
            self._ask_collapse_btn.setText("+")
            self._splitter.setSizes([int(self.height() * 0.58), int(self.height() * 0.42)])
            self._ask_collapsed = False
        else:
            self._ask_scroll.hide()
            self._ask_composer.hide()
            self._ask_collapse_btn.setText("+")
            self._splitter.setSizes([self.height() - 40, 40])
            self._ask_collapsed = True

    def _hide_empty_hint(self):
        if self._ask_empty_hint.isVisible():
            self._ask_empty_hint.hide()

    # ── Q&A logic ──

    def _send_ask(self):
        if self._ask_busy:
            return
        text = self._ask_input.text().strip()
        if not text:
            return
        if self._ask_collapsed:
            self._toggle_ask_collapse()
        self._hide_empty_hint()

        from ..storage import repository as repo
        with self._session_factory() as session:
            settings = repo.get_all_settings(session)

        api_key = settings.get("model_api_key", "")
        if not api_key:
            self._ask_error.emit("请先在「设置」中配置 API Key。")
            return

        model = settings.get("model_name", "deepseek-chat")
        base_url = settings.get("model_base_url", "https://api.deepseek.com")

        self._ask_input.clear()
        self._add_ask_bubble(text, is_user=True)
        self._set_ask_busy(True)
        self._add_ask_bubble("思考中…", is_user=False, is_pending=True)

        self._ask_messages.append({"role": "user", "content": text})
        messages = [
            {"role": "system", "content": build_ask_system_prompt(self._item)},
            *self._ask_messages,
        ]

        def run():
            try:
                from ..llm.client import create_client
                client = create_client(base_url, api_key)
                resp = client.chat.completions.create(
                    model=model, messages=messages, max_tokens=2048,
                )
                reply = (resp.choices[0].message.content or "").strip()
                if reply:
                    self._ask_messages.append({"role": "assistant", "content": reply})
                    self._ask_reply.emit(reply)
                else:
                    self._ask_error.emit("未收到有效回答，请重试。")
            except Exception as e:
                self._ask_error.emit(f"回答失败：{e}")
            finally:
                self._ask_finished.emit()

        threading.Thread(target=run, daemon=True).start()

    def _remove_pending_bubble(self):
        count = self._ask_bubble_layout.count()
        if count > 0:
            item = self._ask_bubble_layout.itemAt(count - 1)
            w = item.widget()
            if w and w.property("pending"):
                self._ask_bubble_layout.removeWidget(w)
                w.deleteLater()

    def _on_ask_reply(self, text: str):
        self._remove_pending_bubble()
        self._add_ask_bubble(text, is_user=False)
        self._scroll_ask_to_bottom()

    def _on_ask_error(self, text: str):
        self._remove_pending_bubble()
        self._add_ask_bubble(text, is_user=False, is_error=True)
        if self._ask_messages and self._ask_messages[-1]["role"] == "user":
            self._ask_messages.pop()
        self._scroll_ask_to_bottom()

    def _on_ask_finished(self):
        self._set_ask_busy(False)

    def _set_ask_busy(self, busy: bool):
        self._ask_busy = busy
        self._ask_input.setReadOnly(busy)

    def _add_ask_bubble(self, text: str, *, is_user: bool, is_error: bool = False, is_pending: bool = False):
        bubble = QFrame()
        if is_error:
            bg, fg, bd = "#FFF5F5", DANGER, "#FFD6D6"
            radius = RADIUS_MD
        elif is_user:
            bg, fg, bd = USER_BUBBLE, "#FFFFFF", "transparent"
            radius = f"{RADIUS_MD} {RADIUS_MD} 4px {RADIUS_MD}"
        else:
            bg, fg = AI_BUBBLE, TEXT_TERTIARY if is_pending else TEXT_PRIMARY
            bd = BORDER_LIGHT
            radius = f"{RADIUS_MD} {RADIUS_MD} {RADIUS_MD} 4px"

        bubble.setProperty("pending", is_pending)
        bubble.setStyleSheet(f"""
            QFrame {{
                background: {bg}; border: 1px solid {bd};
                border-radius: {radius};
            }}
        """)
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lbl.setStyleSheet(
            f"color: {fg}; font-size: 13px; "
            f"line-height: 1.5; background: transparent; border: none;"
        )
        inner.addWidget(lbl)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        if is_user:
            row.addStretch(1)
            row.addWidget(bubble, 0, Qt.AlignRight)
            bubble.setMaximumWidth(int(self.width() * 0.50))
        else:
            row.addWidget(bubble, 0, Qt.AlignLeft)
            bubble.setMaximumWidth(int(self.width() * 0.62))
            row.addStretch(1)
        self._ask_bubble_layout.addLayout(row)
        self._scroll_ask_to_bottom()

    def _scroll_ask_to_bottom(self):
        QTimer.singleShot(50, lambda: self._ask_scroll.verticalScrollBar().setValue(
            self._ask_scroll.verticalScrollBar().maximum()
        ))
