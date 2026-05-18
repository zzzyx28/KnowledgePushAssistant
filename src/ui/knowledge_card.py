"""可复用知识卡片 —— 完整展示摘要，Apple 卡片布局。"""

from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)

from .styles import (
    BG_GLASS_CARD, BORDER_GLASS, ACCENT, RADIUS_SM, RADIUS_LG, ACCENT_FILL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, WARNING, DANGER, BG_HOVER,
    tag_style,
)
from .widgets import WrappingLabel


def _format_time(dt: datetime.datetime | None) -> str:
    if not dt:
        return ""
    if dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    now = datetime.datetime.utcnow()
    diff = now - dt
    if diff.days == 0:
        return "今天"
    if diff.days == 1:
        return "昨天"
    if diff.days < 7:
        return f"{diff.days} 天前"
    return dt.strftime("%Y-%m-%d")


def _clamp_summary(text: str, compact: bool) -> str:
    text = (text or "").strip() or "暂无摘要"
    if not compact:
        return text
    max_chars = 100
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "…"


class KnowledgeCard(QFrame):
    """知识卡片 — 点击卡片打开详情，按钮独立响应。"""

    detail_requested = Signal(int)
    source_opened = Signal(str)
    delete_requested = Signal(int)

    def __init__(
        self,
        item,
        *,
        compact: bool = False,
        show_source: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._item_id = item.id
        self._compact = compact
        is_unread = not getattr(item, "is_read", True)

        self.setObjectName("knowledgeCard")
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

        border = ACCENT if is_unread else BORDER_GLASS
        self.setStyleSheet(f"""
            QFrame#knowledgeCard {{
                background: {BG_GLASS_CARD};
                border: 1px solid {border};
                border-radius: {RADIUS_LG};
            }}
            QFrame#knowledgeCard:hover {{
                border-color: {ACCENT};
                background: rgba(255, 255, 255, 0.82);
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(8)

        # 顶栏：标签 + 时间
        top = QHBoxLayout()
        top.setSpacing(8)
        domain_tag = QLabel(item.domain_name or "未分类")
        domain_tag.setStyleSheet(tag_style())
        top.addWidget(domain_tag, 0, Qt.AlignVCenter)

        top.addStretch()
        if is_unread:
            unread = QLabel("未读")
            unread.setStyleSheet(
                f"color: {ACCENT}; font-size: 11px; font-weight: 600;"
            )
            top.addWidget(unread, 0, Qt.AlignVCenter)
            # dot separator
            dot = QLabel("·")
            dot.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 11px;")
            top.addWidget(dot, 0, Qt.AlignVCenter)

        time_label = QLabel(_format_time(getattr(item, "created_at", None)))
        time_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; font-weight: 500;"
        )
        top.addWidget(time_label, 0, Qt.AlignVCenter)
        root.addLayout(top)

        # 标题
        title = WrappingLabel(item.title or "无标题")
        title.setStyleSheet(
            f"font-weight: {'600' if compact else '700'}; "
            f"font-size: {'14px' if compact else '16px'}; "
            f"color: {TEXT_PRIMARY}; letter-spacing: -0.3px;"
        )
        title.setMinimumLines(1)
        root.addWidget(title)

        # 摘要 — 完整换行展示
        summary = WrappingLabel(_clamp_summary(item.summary, compact))
        summary.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.45;"
        )
        summary.setMinimumLines(2)
        root.addWidget(summary)

        # 底栏
        footer = QHBoxLayout()
        footer.setSpacing(8)
        detail_link = QPushButton("查看详情")
        detail_link.setCursor(Qt.PointingHandCursor)
        detail_link.setProperty("cssClass", "ghost")
        detail_link.clicked.connect(
            lambda: self.detail_requested.emit(self._item_id)
        )
        footer.addWidget(detail_link)

        if show_source and bool(item.source_url):
            src_link = QPushButton("来源")
            src_link.setCursor(Qt.PointingHandCursor)
            src_link.setFixedHeight(28)
            src_link.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_HOVER};
                    border: none;
                    border-radius: {RADIUS_SM};
                    font-size: 12px;
                    font-weight: 500;
                    color: {TEXT_SECONDARY};
                    padding: 4px 12px;
                }}
                QPushButton:hover {{
                    background: {BORDER_LIGHT};
                    color: {TEXT_PRIMARY};
                }}
            """)
            src_link.clicked.connect(
                lambda: self.source_opened.emit(item.source_url)
            )
            footer.addWidget(src_link)

        footer.addStretch()

        del_btn = QPushButton("删除")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFixedHeight(28)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {RADIUS_SM};
                font-size: 12px;
                font-weight: 500;
                color: {TEXT_TERTIARY};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background: #FFF0F0;
                color: {DANGER};
            }}
        """)
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self._item_id)
        )
        footer.addWidget(del_btn)
        root.addLayout(footer)

    def sizeHint(self) -> QSize:
        return QSize(380, 130 if self._compact else 160)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            w = self.childAt(event.position().toPoint())
            while w and w is not self:
                if isinstance(w, QPushButton):
                    return super().mouseReleaseEvent(event)
                w = w.parentWidget()
            self.detail_requested.emit(self._item_id)
        super().mouseReleaseEvent(event)
