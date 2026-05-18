"""领域管理页面 —— 增删改查 + 启用/禁用 + 排序。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog, QVBoxLayout, QLineEdit,
    QTextEdit, QCheckBox, QDialogButtonBox, QMessageBox
)

from ..styles import (
    BG_CARD, BORDER, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG,
    TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS, DANGER, WARNING
)


class DomainManagerPage(QWidget):
    """领域管理页面。"""

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        # 标题行
        header = QHBoxLayout()
        title = QLabel("领域管理")
        title.setProperty("cssClass", "page-title")
        header.addWidget(title)
        header.addStretch()

        add_btn = QPushButton("+ 新增领域")
        add_btn.setFixedHeight(36)
        add_btn.clicked.connect(self._add_domain)
        header.addWidget(add_btn)
        layout.addLayout(header)

        desc = QLabel("管理知识领域，可自定义名称、描述、关键词和图标")
        desc.setProperty("cssClass", "page-desc")
        layout.addWidget(desc)

        # 领域列表
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
        """刷新领域列表。"""
        from ...storage import repository as repo

        with self._session_factory() as session:
            domains = repo.get_all_domains(session)

        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for domain in domains:
            card = self._make_domain_card(domain)
            self.list_layout.addWidget(card)

    def _make_domain_card(self, domain) -> QFrame:
        card = QFrame()
        opacity = "1" if domain.is_enabled else "0.5"
        card.setStyleSheet(f"""
            QFrame {{
                background: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: {RADIUS_MD};
                padding: 12px;
                opacity: {opacity};
            }}
            QFrame:hover {{ border-color: {ACCENT}; }}
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(14)

        # 图标
        icon_label = QLabel(domain.icon)
        icon_label.setStyleSheet("font-size: 28px; padding-right: 4px;")
        icon_label.setFixedWidth(40)
        layout.addWidget(icon_label)

        # 信息
        info = QVBoxLayout()
        info.setSpacing(2)

        name = QLabel(domain.name)
        name.setStyleSheet(f"font-weight: 600; font-size: 14px; color: {TEXT_PRIMARY};")
        info.addWidget(name)

        desc = QLabel(domain.description[:80] if domain.description else "")
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        desc.setWordWrap(True)
        info.addWidget(desc)

        kw = QLabel(f"关键词: {domain.keywords[:60]}" if domain.keywords else "")
        kw.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        info.addWidget(kw)

        layout.addLayout(info, 1)

        # 操作按钮
        btn_area = QVBoxLayout()
        btn_area.setSpacing(6)

        toggle_btn = QPushButton("禁用" if domain.is_enabled else "启用")
        toggle_btn.setFixedSize(56, 26)
        toggle_btn.setStyleSheet(self._small_btn_style(WARNING if domain.is_enabled else SUCCESS))
        toggle_btn.clicked.connect(lambda: self._toggle_domain(domain.id))
        btn_area.addWidget(toggle_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.setFixedSize(56, 26)
        edit_btn.setStyleSheet(self._small_btn_style(ACCENT))
        edit_btn.clicked.connect(lambda: self._edit_domain(domain.id))
        btn_area.addWidget(edit_btn)

        del_btn = QPushButton("删除")
        del_btn.setFixedSize(56, 26)
        del_btn.setStyleSheet(self._small_btn_style(DANGER))
        del_btn.clicked.connect(lambda: self._delete_domain(domain.id))
        btn_area.addWidget(del_btn)

        layout.addLayout(btn_area)

        return card

    def _small_btn_style(self, color: str) -> str:
        return f"""
            QPushButton {{
                background: {BG_CARD};
                border: 1px solid {color};
                border-radius: 6px;
                font-size: 11px;
                color: {color};
                padding: 2px 6px;
            }}
            QPushButton:hover {{
                background: {color};
                color: #ffffff;
            }}
        """

    def _toggle_domain(self, domain_id: int):
        from ...storage import repository as repo
        with self._session_factory() as session:
            domain = repo.get_domain_by_id(session, domain_id)
            if domain:
                repo.update_domain(session, domain_id, is_enabled=not domain.is_enabled)
        self.refresh()

    def _add_domain(self):
        dialog = DomainEditDialog(self)
        if dialog.exec():
            from ...storage import repository as repo
            with self._session_factory() as session:
                repo.create_domain(
                    session,
                    name=dialog.name_edit.text().strip(),
                    description=dialog.desc_edit.toPlainText().strip(),
                    keywords=dialog.kw_edit.text().strip(),
                    icon=dialog.icon_edit.text().strip() or "📚",
                )
            self.refresh()

    def _edit_domain(self, domain_id: int):
        from ...storage import repository as repo
        with self._session_factory() as session:
            domain = repo.get_domain_by_id(session, domain_id)
            if not domain:
                return
            dialog = DomainEditDialog(
                self,
                name=domain.name,
                description=domain.description or "",
                keywords=domain.keywords or "",
                icon=domain.icon or "📚",
            )
            if dialog.exec():
                repo.update_domain(
                    session, domain_id,
                    name=dialog.name_edit.text().strip(),
                    description=dialog.desc_edit.toPlainText().strip(),
                    keywords=dialog.kw_edit.text().strip(),
                    icon=dialog.icon_edit.text().strip() or "📚",
                )
        self.refresh()

    def _delete_domain(self, domain_id: int):
        from ...storage import repository as repo
        with self._session_factory() as session:
            domain = repo.get_domain_by_id(session, domain_id)
            if not domain:
                return
            count = 0
            from ...storage.models import KnowledgeItem
            count = session.query(KnowledgeItem).filter(
                KnowledgeItem.domain_id == domain_id
            ).count()

        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除领域「{domain.name}」吗？\n\n"
            f"该领域下有 {count} 条知识，删除后它们将保留但失去领域关联。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            with self._session_factory() as session:
                repo.delete_domain(session, domain_id)
            self.refresh()


class DomainEditDialog(QDialog):
    """领域编辑弹窗。"""

    def __init__(self, parent=None, name="", description="", keywords="", icon="📚"):
        super().__init__(parent)
        self.setWindowTitle("编辑领域")
        self.setFixedSize(420, 380)
        self.setStyleSheet(f"""
            QDialog {{
                background: #ffffff;
                border-radius: {RADIUS_LG};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 名称
        layout.addWidget(QLabel("名称"))
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("如: 计算机科学")
        layout.addWidget(self.name_edit)

        # 图标
        layout.addWidget(QLabel("图标 (emoji)"))
        self.icon_edit = QLineEdit(icon)
        self.icon_edit.setPlaceholderText("如: 💻")
        layout.addWidget(self.icon_edit)

        # 描述
        layout.addWidget(QLabel("描述"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("简要描述该领域包含的知识范围...")
        self.desc_edit.setFixedHeight(60)
        self.desc_edit.setText(description)
        layout.addWidget(self.desc_edit)

        # 关键词
        layout.addWidget(QLabel("搜索关键词 (空格分隔)"))
        self.kw_edit = QLineEdit(keywords)
        self.kw_edit.setPlaceholderText("如: 编程 算法 网络")
        layout.addWidget(self.kw_edit)

        layout.addStretch()

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.button(QDialogButtonBox.Cancel).setText("取消")
        layout.addWidget(buttons)
