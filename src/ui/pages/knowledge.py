"""知识管理页面 —— 卡片列表 + 筛选/搜索。"""

import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QMessageBox,
)

from ..widgets import SmoothScrollArea, PageHeader
from ..knowledge_card import KnowledgeCard
from ..styles import (
    TEXT_SECONDARY, PAGE_MARGIN_H, PAGE_MARGIN_V,
    search_field_style, combo_field_style,
)


class KnowledgePage(QWidget):
    """知识管理页面。"""

    detail_requested = Signal(int)

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            PAGE_MARGIN_H, PAGE_MARGIN_V, PAGE_MARGIN_H, PAGE_MARGIN_V
        )
        layout.setSpacing(20)

        layout.addWidget(
            PageHeader("知识库", "浏览、搜索知识卡片，点击查看完整详情")
        )

        search_row = QHBoxLayout()
        search_row.setSpacing(12)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或摘要")
        self.search_input.setFixedHeight(40)
        self.search_input.setStyleSheet(search_field_style())
        self.search_input.textChanged.connect(self.refresh)
        search_row.addWidget(self.search_input, 2)

        self.domain_filter = QComboBox()
        self.domain_filter.setFixedHeight(40)
        self.domain_filter.setMinimumWidth(160)
        self.domain_filter.setStyleSheet(combo_field_style())
        self.domain_filter.addItem("全部领域", -1)
        self.domain_filter.currentIndexChanged.connect(self.refresh)
        search_row.addWidget(self.domain_filter)

        layout.addLayout(search_row)

        scroll = SmoothScrollArea()
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(10)
        self.list_layout.setContentsMargins(0, 0, 4, 24)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)

        self._empty_label = QLabel("暂无知识卡片\n试试「智能推送」获取新内容")
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 15px; line-height: 1.6; padding: 64px;"
        )
        self._empty_label.hide()

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

    def refresh(self):
        from ...storage import repository as repo

        current_domain = self.domain_filter.currentData()
        self.domain_filter.blockSignals(True)
        self.domain_filter.clear()
        self.domain_filter.addItem("全部领域", -1)
        with self._session_factory() as session:
            domains = repo.get_all_domains(session)
            for d in domains:
                self.domain_filter.addItem(d.name, d.id)
        idx = self.domain_filter.findData(current_domain)
        self.domain_filter.setCurrentIndex(max(idx, 0))
        self.domain_filter.blockSignals(False)

        keyword = self.search_input.text().strip() or None
        domain_id = (
            self.domain_filter.currentData()
            if self.domain_filter.currentData() != -1
            else None
        )

        with self._session_factory() as session:
            items = repo.get_knowledge_items(
                session, domain_id=domain_id, keyword=keyword, limit=100
            )

        while self.list_layout.count():
            lay_item = self.list_layout.takeAt(0)
            w = lay_item.widget()
            if w and w is not self._empty_label:
                w.deleteLater()

        if not items:
            if self._empty_label.parent() is None:
                self.list_layout.addWidget(self._empty_label)
            self._empty_label.show()
            return

        self._empty_label.hide()
        if self._empty_label.parent():
            self.list_layout.removeWidget(self._empty_label)

        for item in items:
            card = KnowledgeCard(item, compact=False, show_source=True)
            card.detail_requested.connect(self.detail_requested.emit)
            card.source_opened.connect(webbrowser.open)
            card.delete_requested.connect(self._delete_item)
            self.list_layout.addWidget(card)
