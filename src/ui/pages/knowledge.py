"""知识管理页面 —— 卡片列表 + 筛选/搜索 + 收藏/评价操作。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QMenu
)
from PySide6.QtGui import QAction

from ..styles import (
    BG_CARD, BORDER, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG,
    TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS, DANGER
)


class KnowledgePage(QWidget):
    """知识管理页面。"""

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 标题
        title = QLabel("知识管理")
        title.setProperty("cssClass", "page-title")
        layout.addWidget(title)

        desc = QLabel("浏览、搜索和评价已推送的知识卡片")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # 搜索栏
        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或摘要...")
        self.search_input.setFixedHeight(36)
        self.search_input.textChanged.connect(self.refresh)
        search_row.addWidget(self.search_input, 2)

        self.domain_filter = QComboBox()
        self.domain_filter.setFixedHeight(36)
        self.domain_filter.setFixedWidth(180)
        self.domain_filter.addItem("全部领域", -1)
        self.domain_filter.currentIndexChanged.connect(self.refresh)
        search_row.addWidget(self.domain_filter)

        layout.addLayout(search_row)

        # 卡片列表滚动区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(8)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)

    def refresh(self):
        """刷新知识列表。"""
        from ...storage import repository as repo

        # 更新领域下拉
        current_domain = self.domain_filter.currentData()
        self.domain_filter.blockSignals(True)
        self.domain_filter.clear()
        self.domain_filter.addItem("全部领域", -1)
        with self._session_factory() as session:
            domains = repo.get_all_domains(session)
            for d in domains:
                self.domain_filter.addItem(f"{d.icon} {d.name}", d.id)
        idx = self.domain_filter.findData(current_domain)
        self.domain_filter.setCurrentIndex(max(idx, 0))
        self.domain_filter.blockSignals(False)

        keyword = self.search_input.text().strip() or None
        domain_id = self.domain_filter.currentData() if self.domain_filter.currentData() != -1 else None

        with self._session_factory() as session:
            items = repo.get_knowledge_items(session, domain_id=domain_id, keyword=keyword, limit=100)

        # 清空并重建
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in items:
            card = self._make_item_card(item)
            self.list_layout.addWidget(card)

    def _make_item_card(self, item) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 12px;
            }}
            QFrame:hover {{ border-color: {ACCENT}; }}
        """)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # 第一行：领域标签 + 标题
        row1 = QHBoxLayout()
        domain_tag = QLabel(item.domain_name)
        domain_tag.setStyleSheet(f"""
            background: {ACCENT_LIGHT}; color: {ACCENT};
            border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 500;
        """)
        row1.addWidget(domain_tag)

        title = QLabel(item.title)
        title.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {TEXT_PRIMARY};")
        row1.addWidget(title, 1)
        layout.addLayout(row1)

        # 摘要
        summary = QLabel(item.summary)
        summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        fav_btn = QPushButton("⭐ 收藏" if not item.is_favorited else "⭐ 已收藏")
        fav_btn.setProperty("cssClass", "secondary")
        fav_btn.setFixedHeight(28)
        fav_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 4px 10px; font-size: 12px;
                color: {'#f59e0b' if item.is_favorited else TEXT_SECONDARY};
            }}
            QPushButton:hover {{ border-color: #f59e0b; }}
        """)
        fav_btn.clicked.connect(lambda: self._toggle_favorite(item.id))
        btn_row.addWidget(fav_btn)

        useful_btn = QPushButton("👍 有用" if item.rating != 1 else "👍 已评价")
        useful_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 4px 10px; font-size: 12px;
                color: {'#22c55e' if item.rating == 1 else TEXT_SECONDARY};
            }}
            QPushButton:hover {{ border-color: #22c55e; }}
        """)
        useful_btn.clicked.connect(lambda: self._rate_item(item.id, 1))
        btn_row.addWidget(useful_btn)

        not_interested_btn = QPushButton("👎 不感兴趣" if item.rating != -1 else "👎 已评价")
        not_interested_btn.setStyleSheet(f"""
            QPushButton {{
                background: {BG_CARD}; border: 1px solid {BORDER};
                border-radius: 6px; padding: 4px 10px; font-size: 12px;
                color: {'#ef4444' if item.rating == -1 else TEXT_SECONDARY};
            }}
            QPushButton:hover {{ border-color: #ef4444; }}
        """)
        not_interested_btn.clicked.connect(lambda: self._rate_item(item.id, -1))
        btn_row.addWidget(not_interested_btn)

        if item.source_url:
            source_btn = QPushButton("🔗 来源")
            source_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {BG_CARD}; border: 1px solid {BORDER};
                    border-radius: 6px; padding: 4px 10px; font-size: 12px;
                    color: {TEXT_SECONDARY};
                }}
                QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
            """)
            source_btn.clicked.connect(lambda: self._open_source(item.source_url))
            btn_row.addWidget(source_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        return card

    def _toggle_favorite(self, item_id: int):
        from ...storage import repository as repo
        with self._session_factory() as session:
            item = repo.get_knowledge_item_by_id(session, item_id)
            if item:
                repo.update_knowledge_item(session, item_id, is_favorited=not item.is_favorited)
        self.refresh()

    def _rate_item(self, item_id: int, rating: int):
        from ...storage import repository as repo
        with self._session_factory() as session:
            item = repo.get_knowledge_item_by_id(session, item_id)
            if item:
                new_rating = None if item.rating == rating else rating
                repo.update_knowledge_item(session, item_id, rating=new_rating)
        self.refresh()

    def _open_source(self, url: str):
        import webbrowser
        webbrowser.open(url)
