"""仪表盘页面 —— 指标卡 + 推送按钮 + 最近知识预览 + 领域分布。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea
)
from sqlalchemy.orm import Session

from ..styles import BG_CARD, BORDER, ACCENT, RADIUS_LG, TEXT_SECONDARY


class DashboardPage(QWidget):
    """仪表盘页面。"""

    push_requested = Signal()

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        # 标题
        title = QLabel("仪表盘")
        title.setProperty("cssClass", "page-title")
        layout.addWidget(title)

        desc = QLabel("知识推送助手运行概况")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # 指标卡片行
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        self.stat_total = self._make_stat_card("知识总量", "0")
        self.stat_recent = self._make_stat_card("最近 7 天", "0")
        self.stat_status = self._make_stat_card("推送状态", "待机")
        cards_layout.addWidget(self.stat_total)
        cards_layout.addWidget(self.stat_recent)
        cards_layout.addWidget(self.stat_status)
        layout.addLayout(cards_layout)

        # 智能推送按钮
        btn_row = QHBoxLayout()
        self.push_btn = QPushButton("🚀  智能推送")
        self.push_btn.setFixedHeight(48)
        self.push_btn.setStyleSheet(f"""
            QPushButton {{
                background: {ACCENT};
                color: #ffffff;
                font-size: 16px;
                font-weight: 600;
                border-radius: {RADIUS_LG};
            }}
            QPushButton:hover {{ background: #5558e6; }}
        """)
        self.push_btn.clicked.connect(self.push_requested.emit)
        btn_row.addWidget(self.push_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 最近知识预览
        section_label = QLabel("最近知识卡片")
        section_label.setStyleSheet("font-weight: 600; font-size: 15px; margin-top: 8px;")
        layout.addWidget(section_label)

        self.recent_list = QVBoxLayout()
        self.recent_list.setSpacing(8)
        layout.addLayout(self.recent_list)

        layout.addStretch()

    def _make_stat_card(self, label: str, value: str) -> QFrame:
        card = QFrame()
        card.setProperty("cssClass", "stat-card")
        card.setStyleSheet(f"""
            QFrame[cssClass="stat-card"] {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_LG};
                padding: 16px;
            }}
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(4)

        val = QLabel(value)
        val.setProperty("cssClass", "stat-value")
        layout.addWidget(val)

        lbl = QLabel(label)
        lbl.setProperty("cssClass", "stat-label")
        layout.addWidget(lbl)

        return card

    def refresh(self):
        """刷新仪表盘数据。"""
        from ...storage import repository as repo

        with self._session_factory() as session:
            total = repo.get_knowledge_count(session)
            recent = repo.get_recent_count(session, days=7)
            domains = repo.get_all_domains(session)

        self.stat_total.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(str(total))
        self.stat_recent.findChild(QLabel, "", Qt.FindChildrenRecursively).setText(str(recent))

        # 清空并重建最近列表
        children = []
        for i in range(self.recent_list.count()):
            item = self.recent_list.itemAt(i)
            if item and item.widget():
                children.append(item.widget())
        for w in children:
            w.deleteLater()

        with self._session_factory() as session:
            items = repo.get_knowledge_items(session, limit=3)

        for item in items:
            card = self._make_item_card(item)
            self.recent_list.addWidget(card)

    def _make_item_card(self, item) -> QFrame:
        from ...storage.models import KnowledgeItem
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)

        left = QVBoxLayout()
        left.setSpacing(4)
        title = QLabel(item.title)
        title.setStyleSheet("font-weight: 600; font-size: 13px;")
        left.addWidget(title)
        summary = QLabel(item.summary)
        summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        summary.setWordWrap(True)
        left.addWidget(summary)
        layout.addLayout(left, 1)

        domain_label = QLabel(item.domain_name)
        domain_label.setStyleSheet(f"""
            background: #eef2ff; color: {ACCENT}; border-radius: 6px;
            padding: 2px 8px; font-size: 11px; font-weight: 500;
        """)
        layout.addWidget(domain_label)

        return card

    def set_push_status(self, text: str):
        """更新推送状态标签。"""
        labels = self.stat_status.findChildren(QLabel)
        if labels:
            labels[-1].setText(text)
