"""学习详情窗口 —— Markdown 渲染 + 来源链接 + 收藏/评价按钮。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTextEdit, QFrame
)

from .styles import (
    BG_CARD, BG_MAIN, BORDER, ACCENT, ACCENT_LIGHT,
    RADIUS_MD, RADIUS_LG, TEXT_PRIMARY, TEXT_SECONDARY
)


class DetailWindow(QWidget):
    """知识详情窗口。"""

    def __init__(self, item, db_session_factory, parent=None):
        super().__init__(parent)
        self._item_id = item.id
        self._session_factory = db_session_factory
        self._item = item

        self.setWindowTitle(item.title)
        self.setMinimumSize(500, 480)
        self.resize(560, 560)
        self.setStyleSheet(f"background: {BG_MAIN};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 领域标签 + 标题
        header = QHBoxLayout()
        tag = QLabel(item.domain_name)
        tag.setStyleSheet(f"""
            background: {ACCENT_LIGHT}; color: {ACCENT};
            border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 500;
        """)
        header.addWidget(tag)
        header.addStretch()
        layout.addLayout(header)

        title = QLabel(item.title)
        title.setStyleSheet(f"font-weight: 700; font-size: 18px; color: {TEXT_PRIMARY};")
        title.setWordWrap(True)
        layout.addWidget(title)

        # 摘要
        summary_label = QLabel(item.summary)
        summary_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px;")
        summary_label.setWordWrap(True)
        layout.addWidget(summary_label)

        # 详情 (纯文本展示)
        detail_edit = QTextEdit()
        detail_edit.setReadOnly(True)
        detail_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 12px;
                font-size: 13px;
                line-height: 1.6;
            }}
        """)
        detail_edit.setPlainText(item.detail)
        layout.addWidget(detail_edit, 1)

        # 来源链接
        if item.source_url:
            src_row = QHBoxLayout()
            src_label = QLabel(f"来源: ")
            src_label.setStyleSheet(f"color: {TEXT_SECONDARY};")
            src_row.addWidget(src_label)
            src_link = QPushButton(item.source_title or item.source_url[:60])
            src_link.setProperty("cssClass", "icon-btn")
            src_link.setStyleSheet(f"color: {ACCENT}; font-size: 12px;")
            src_link.clicked.connect(lambda: self._open_url(item.source_url))
            src_row.addWidget(src_link)
            src_row.addStretch()
            layout.addLayout(src_row)

        # 操作按钮
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        fav_btn = QPushButton("⭐ 收藏" if not item.is_favorited else "⭐ 取消收藏")
        fav_btn.setProperty("cssClass", "secondary")
        fav_btn.setFixedHeight(34)
        fav_btn.clicked.connect(lambda: self._toggle_favorite(fav_btn))
        btn_row.addWidget(fav_btn)

        useful_btn = QPushButton("👍 有用")
        useful_btn.setProperty("cssClass", "secondary")
        useful_btn.setFixedHeight(34)
        useful_btn.clicked.connect(lambda: self._rate(1))
        btn_row.addWidget(useful_btn)

        not_btn = QPushButton("👎 不感兴趣")
        not_btn.setProperty("cssClass", "secondary")
        not_btn.setFixedHeight(34)
        not_btn.clicked.connect(lambda: self._rate(-1))
        btn_row.addWidget(not_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

    def _toggle_favorite(self, btn: QPushButton):
        from ..storage import repository as repo
        with self._session_factory() as session:
            item = repo.get_knowledge_item_by_id(session, self._item_id)
            if item:
                repo.update_knowledge_item(session, self._item_id, is_favorited=not item.is_favorited)
                btn.setText("⭐ 取消收藏" if not item.is_favorited else "⭐ 收藏")

    def _rate(self, rating: int):
        from ..storage import repository as repo
        with self._session_factory() as session:
            item = repo.get_knowledge_item_by_id(session, self._item_id)
            if item:
                new_rating = None if item.rating == rating else rating
                repo.update_knowledge_item(session, self._item_id, rating=new_rating)

    def _open_url(self, url: str):
        import webbrowser
        webbrowser.open(url)
