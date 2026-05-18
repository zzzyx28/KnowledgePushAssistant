"""仪表盘页面 —— 时间问候 + 统计条 + 知识列表。"""

import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QMessageBox,
)

from ..knowledge_card import KnowledgeCard
from ..widgets import SmoothScrollArea
from ..styles import (
    BG_CARD, BORDER_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    ACCENT, ACCENT_FILL, RADIUS_MD, RADIUS_LG, PAGE_MARGIN_H, PAGE_MARGIN_V,
    primary_button_style, slim_stat_style,
)


def _greeting() -> str:
    h = datetime.datetime.now().hour
    if h < 12:
        return "上午好"
    if h < 18:
        return "下午好"
    return "晚上好"


def _last_push_time(db_session_factory) -> str:
    try:
        with db_session_factory() as session:
            from ...storage import repository as repo
            items = repo.get_knowledge_items(session, limit=1)
            if items:
                dt = getattr(items[0], "created_at", None)
                if dt:
                    if dt.tzinfo:
                        dt = dt.replace(tzinfo=None)
                    now = datetime.datetime.utcnow()
                    diff = now - dt
                    if diff.days == 0:
                        mins = max(diff.seconds // 60, 0)
                        if mins < 1:
                            return "刚刚"
                        if mins < 60:
                            return f"{mins} 分钟前"
                        return f"{diff.seconds // 3600} 小时前"
                    if diff.days == 1:
                        return "昨天"
                    if diff.days < 7:
                        return f"{diff.days} 天前"
                    return dt.strftime("%m-%d")
            return "尚未推送"
    except Exception:
        return "--"


class DashboardPage(QWidget):
    """仪表盘页面。"""

    push_requested = Signal()
    detail_requested = Signal(int)

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            PAGE_MARGIN_H, PAGE_MARGIN_V, PAGE_MARGIN_H, PAGE_MARGIN_V
        )
        layout.setSpacing(28)

        # ── 问候 ──
        greeting = QHBoxLayout()
        greeting.setContentsMargins(0, 0, 0, 0)
        greeting.setSpacing(0)

        left = QVBoxLayout()
        left.setSpacing(4)
        self.greeting_label = QLabel(_greeting())
        self.greeting_label.setProperty("cssClass", "greeting")
        left.addWidget(self.greeting_label)

        self.greeting_sub = QLabel()
        self.greeting_sub.setProperty("cssClass", "greeting-sub")
        left.addWidget(self.greeting_sub)
        greeting.addLayout(left)
        greeting.addStretch()

        self.push_btn = QPushButton("智能推送")
        self.push_btn.setCursor(Qt.PointingHandCursor)
        self.push_btn.setFixedHeight(38)
        self.push_btn.setStyleSheet(primary_button_style(height=38))
        self.push_btn.clicked.connect(self.push_requested.emit)
        greeting.addWidget(self.push_btn, 0, Qt.AlignTop)
        layout.addLayout(greeting)

        # ── 统计 ──
        stat_bar = QHBoxLayout()
        stat_bar.setSpacing(10)

        self.stat_total = self._slim_stat("0", "知识总量")
        self.stat_weekly = self._slim_stat("0", "本周新增")
        self.stat_push = self._slim_stat("待机中", "推送状态")
        self.stat_last = self._slim_stat("--", "最近推送")
        for w in (self.stat_total, self.stat_weekly, self.stat_push, self.stat_last):
            stat_bar.addWidget(w, 1)
        layout.addLayout(stat_bar)

        # ── 分隔 ──
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(
            f"background: {BORDER_LIGHT}; border: none; margin: 0;"
        )
        layout.addWidget(divider)

        # ── 最近知识 ──
        section_row = QHBoxLayout()
        section_row.setSpacing(8)
        section_title = QLabel("最近知识")
        section_title.setProperty("cssClass", "section-title")
        section_row.addWidget(section_title)
        section_row.addStretch()
        self.section_count = QLabel()
        self.section_count.setStyleSheet(
            f"color: {TEXT_TERTIARY}; font-size: 12px;"
        )
        section_row.addWidget(self.section_count)
        layout.addLayout(section_row)

        scroll = SmoothScrollArea()
        self._recent_container = QWidget()
        self.recent_list = QVBoxLayout(self._recent_container)
        self.recent_list.setAlignment(Qt.AlignTop)
        self.recent_list.setSpacing(10)
        self.recent_list.setContentsMargins(0, 0, 4, 16)
        scroll.setWidget(self._recent_container)
        layout.addWidget(scroll, 1)

        # ── 空状态 ──
        self._empty_widget = self._make_empty_state()

    @staticmethod
    def _slim_stat(value: str, label: str) -> QFrame:
        card = QFrame()
        card.setObjectName("slimStat")
        card.setStyleSheet(slim_stat_style())
        inner = QVBoxLayout(card)
        inner.setContentsMargins(18, 16, 18, 16)
        inner.setSpacing(2)

        val = QLabel(value)
        val.setProperty("cssClass", "stat-value-sm")
        inner.addWidget(val)

        lbl = QLabel(label)
        lbl.setProperty("cssClass", "stat-label-sm")
        inner.addWidget(lbl)
        return card

    def _set_slim_value(self, card: QFrame, value: str):
        for i in range(card.layout().count()):
            w = card.layout().itemAt(i).widget()
            if isinstance(w, QLabel) and w.property("cssClass") == "stat-value-sm":
                w.setText(value)
                return

    def _make_empty_state(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(0, 32, 0, 32)
        lay.setSpacing(12)

        icon = QLabel("\U0001F4E5")
        icon.setStyleSheet("font-size: 40px;")
        icon.setAlignment(Qt.AlignCenter)
        lay.addWidget(icon)

        hint = QLabel("还没有知识卡片")
        hint.setProperty("cssClass", "empty-hint")
        hint.setAlignment(Qt.AlignCenter)
        lay.addWidget(hint)

        sub = QLabel("点击右上角「智能推送」开始获取内容")
        sub.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 13px;")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)

        btn = QPushButton("立即推送")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(primary_button_style(height=38))
        btn.clicked.connect(self.push_requested.emit)
        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.addWidget(btn)
        lay.addLayout(btn_row)

        w.hide()
        return w

    def refresh(self):
        from ...storage import repository as repo

        with self._session_factory() as session:
            total = repo.get_knowledge_count(session)
            recent7 = repo.get_recent_count(session, days=7)
            items = repo.get_knowledge_items(session, limit=8)

        # 问候
        self.greeting_label.setText(_greeting())
        if total > 0:
            self.greeting_sub.setText(f"共收录 {total} 条知识")
        else:
            self.greeting_sub.setText("开始构建你的知识库吧")

        # 统计
        self._set_slim_value(self.stat_total, str(total))
        self._set_slim_value(self.stat_weekly, str(recent7))
        last = _last_push_time(self._session_factory)
        self._set_slim_value(self.stat_last, last)

        self.section_count.setText(f"{len(items)} 条" if items else "")

        # 清理列表
        children = []
        for i in range(self.recent_list.count()):
            lay_item = self.recent_list.itemAt(i)
            if lay_item and lay_item.widget():
                w = lay_item.widget()
                if w is not self._empty_widget:
                    children.append(w)
        for w in children:
            w.deleteLater()

        # 空状态 vs 列表
        if not items:
            if self._empty_widget.parent() is None:
                self.recent_list.addWidget(self._empty_widget)
            self._empty_widget.show()
            return

        self._empty_widget.hide()
        if self._empty_widget.parent():
            self.recent_list.removeWidget(self._empty_widget)

        for item in items:
            card = KnowledgeCard(item, compact=True, show_source=False)
            card.detail_requested.connect(self.detail_requested.emit)
            card.delete_requested.connect(self._delete_item)
            self.recent_list.addWidget(card)

    def _delete_item(self, item_id: int):
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这条知识卡片吗？此操作不可撤销。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        with self._session_factory() as session:
            from ...storage import repository as repo
            repo.delete_knowledge_item(session, item_id)
        self.refresh()

    def set_push_status(self, text: str):
        self._set_slim_value(self.stat_push, text)
