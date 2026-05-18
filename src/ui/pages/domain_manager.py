"""领域管理页面 —— 增删改查 + 启用/禁用。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QDialog, QLineEdit, QTextEdit,
    QDialogButtonBox, QMessageBox,
)

from ..widgets import SmoothScrollArea, PageHeader, WrappingLabel
from ..styles import (
    BG_CARD, BG_HOVER, BORDER_LIGHT, ACCENT, RADIUS_SM, RADIUS_LG, TEXT_PRIMARY, TEXT_SECONDARY,
    SUCCESS, DANGER, WARNING, PAGE_MARGIN_H, PAGE_MARGIN_V,
    primary_button_style, ACCENT_FILL,
)


class DomainManagerPage(QWidget):
    """领域管理页面。"""

    def __init__(self, db_session_factory, parent=None):
        super().__init__(parent)
        self._session_factory = db_session_factory

        layout = QVBoxLayout(self)
        layout.setContentsMargins(PAGE_MARGIN_H, PAGE_MARGIN_V, PAGE_MARGIN_H, PAGE_MARGIN_V)
        layout.setSpacing(16)

        page_header = PageHeader(
            "领域",
            "管理知识分类：名称、描述与搜索关键词，点击卡片可快速编辑",
        )
        add_btn = QPushButton("新增领域")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.setStyleSheet(primary_button_style(height=36))
        add_btn.clicked.connect(self._add_domain)
        page_header.add_action(add_btn)
        layout.addWidget(page_header)

        scroll = SmoothScrollArea()

        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignTop)
        self.list_layout.setSpacing(12)
        self.list_layout.setContentsMargins(0, 0, 4, 24)

        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll, 1)

        self._empty_label = QLabel(
            "暂无领域，点击「新增领域」创建第一个分类"
        )
        self._empty_label.setAlignment(Qt.AlignCenter)
        self._empty_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 14px; padding: 48px 16px;"
        )
        self._empty_label.hide()

    def refresh(self):
        """刷新领域列表。"""
        from ...storage import repository as repo
        from ...storage.models import KnowledgeItem

        with self._session_factory() as session:
            domains = repo.get_all_domains(session)
            counts = {}
            for d in domains:
                counts[d.id] = (
                    session.query(KnowledgeItem)
                    .filter(KnowledgeItem.domain_id == d.id)
                    .count()
                )

        while self.list_layout.count():
            lay_item = self.list_layout.takeAt(0)
            w = lay_item.widget()
            if w and w is not self._empty_label:
                w.deleteLater()

        if not domains:
            if self._empty_label.parent() is None:
                self.list_layout.addWidget(self._empty_label)
            self._empty_label.show()
            return

        self._empty_label.hide()
        if self._empty_label.parent():
            self.list_layout.removeWidget(self._empty_label)

        for domain in domains:
            card = DomainCard(
                domain,
                knowledge_count=counts.get(domain.id, 0),
                parent=self.list_widget,
            )
            card.toggle_requested.connect(self._toggle_domain)
            card.edit_requested.connect(self._edit_domain)
            card.delete_requested.connect(self._delete_domain)
            self.list_layout.addWidget(card)

    def _toggle_domain(self, domain_id: int):
        from ...storage import repository as repo

        with self._session_factory() as session:
            domain = repo.get_domain_by_id(session, domain_id)
            if domain:
                repo.update_domain(session, domain_id, is_enabled=not domain.is_enabled)
        self.refresh()

    def _add_domain(self):
        dialog = DomainEditDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            from ...storage import repository as repo

            with self._session_factory() as session:
                repo.create_domain(session, **data)
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
            )
            if dialog.exec() == QDialog.Accepted:
                repo.update_domain(session, domain_id, **dialog.get_data())
        self.refresh()

    def _delete_domain(self, domain_id: int):
        from ...storage import repository as repo
        from ...storage.models import KnowledgeItem

        with self._session_factory() as session:
            domain = repo.get_domain_by_id(session, domain_id)
            if not domain:
                return
            count = (
                session.query(KnowledgeItem)
                .filter(KnowledgeItem.domain_id == domain_id)
                .count()
            )
            name = domain.name

        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除领域「{name}」吗？\n\n"
            f"该领域下有 {count} 条知识，删除后它们将保留但失去领域关联。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            with self._session_factory() as session:
                repo.delete_domain(session, domain_id)
            self.refresh()


class DomainCard(QFrame):
    """领域卡片 —— 点击主体区域可编辑。"""

    toggle_requested = Signal(int)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, domain, knowledge_count: int = 0, parent=None):
        super().__init__(parent)
        self._domain_id = domain.id
        self.setObjectName("domainCard")
        self.setCursor(Qt.PointingHandCursor)

        bg = BG_CARD if domain.is_enabled else "#F5F5F7"
        self.setStyleSheet(f"""
            QFrame#domainCard {{
                background: {bg};
                border: 1px solid {BORDER_LIGHT};
                border-radius: {RADIUS_LG};
            }}
            QFrame#domainCard:hover {{
                border-color: {ACCENT};
                background: {BG_HOVER};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(10)

        top = QHBoxLayout()
        top.setSpacing(10)

        name = QLabel(domain.name)
        name.setStyleSheet(
            f"font-weight: 700; font-size: 15px; color: {TEXT_PRIMARY};"
        )
        top.addWidget(name)

        status = QLabel("已启用" if domain.is_enabled else "已禁用")
        status_color = SUCCESS if domain.is_enabled else TEXT_SECONDARY
        status_bg = ACCENT_FILL if domain.is_enabled else "#F2F2F7"
        status.setStyleSheet(f"""
            background: {status_bg}; color: {status_color};
            border-radius: {RADIUS_SM}; padding: 3px 10px; font-size: 11px; font-weight: 600;
        """)
        top.addWidget(status)

        count_label = QLabel(f"{knowledge_count} 条知识")
        count_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; padding: 0 4px;"
        )
        top.addWidget(count_label)
        top.addStretch()
        root.addLayout(top)

        if domain.description:
            desc = WrappingLabel(domain.description)
            desc.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 13px; line-height: 1.5;"
            )
            root.addWidget(desc)

        if domain.keywords:
            kw = WrappingLabel(f"关键词：{domain.keywords}")
            kw.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
            root.addWidget(kw)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        toggle_btn = QPushButton("禁用" if domain.is_enabled else "启用")
        toggle_btn.setCursor(Qt.PointingHandCursor)
        toggle_btn.setFixedHeight(30)
        toggle_color = WARNING if domain.is_enabled else SUCCESS
        toggle_btn.setStyleSheet(_action_btn_style(toggle_color))
        toggle_btn.clicked.connect(
            lambda: self.toggle_requested.emit(self._domain_id)
        )
        btn_row.addWidget(toggle_btn)

        edit_btn = QPushButton("编辑")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setFixedHeight(30)
        edit_btn.setStyleSheet(_action_btn_style(ACCENT))
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._domain_id))
        btn_row.addWidget(edit_btn)

        del_btn = QPushButton("删除")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFixedHeight(30)
        del_btn.setStyleSheet(_action_btn_style(DANGER))
        del_btn.clicked.connect(
            lambda: self.delete_requested.emit(self._domain_id)
        )
        btn_row.addWidget(del_btn)

        hint = QLabel("点击卡片空白处也可编辑")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        btn_row.addWidget(hint)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            w = self.childAt(event.position().toPoint())
            while w and w is not self:
                if isinstance(w, QPushButton):
                    return super().mouseReleaseEvent(event)
                w = w.parentWidget()
            self.edit_requested.emit(self._domain_id)
        super().mouseReleaseEvent(event)


def _action_btn_style(color: str) -> str:
    return f"""
        QPushButton {{
            background: {BG_CARD};
            border: 1px solid {color};
            border-radius: {RADIUS_SM};
            font-size: 12px;
            font-weight: 500;
            color: {color};
            padding: 4px 14px;
            min-width: 52px;
        }}
        QPushButton:hover {{
            background: {color};
            color: #ffffff;
        }}
    """


class DomainEditDialog(QDialog):
    """领域编辑弹窗。"""

    def __init__(
        self,
        parent=None,
        name: str = "",
        description: str = "",
        keywords: str = "",
    ):
        super().__init__(parent)
        self.setWindowTitle("新增领域" if not name else "编辑领域")
        self.setMinimumWidth(440)
        self.resize(460, 360)
        self.setStyleSheet(f"""
            QDialog {{ background: {BG_CARD}; }}
            QLabel.field-label {{
                font-weight: 600; font-size: 12px; color: {TEXT_PRIMARY};
                margin-top: 4px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(10)

        name_lbl = QLabel("名称 *")
        name_lbl.setProperty("cssClass", "field-label")
        layout.addWidget(name_lbl)
        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText("例如：计算机科学、产品设计")
        self.name_edit.setFixedHeight(36)
        layout.addWidget(self.name_edit)

        desc_lbl = QLabel("描述")
        desc_lbl.setProperty("cssClass", "field-label")
        layout.addWidget(desc_lbl)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("简要说明该领域包含的知识范围，便于 Agent 理解推送方向…")
        self.desc_edit.setFixedHeight(88)
        self.desc_edit.setText(description)
        layout.addWidget(self.desc_edit)

        kw_lbl = QLabel("搜索关键词")
        kw_lbl.setProperty("cssClass", "field-label")
        layout.addWidget(kw_lbl)
        self.kw_edit = QLineEdit(keywords)
        self.kw_edit.setPlaceholderText("多个关键词用空格分隔，例如：编程 算法 网络")
        self.kw_edit.setFixedHeight(36)
        layout.addWidget(self.kw_edit)

        kw_hint = QLabel("关键词用于 Agent 检索与推送时的领域匹配")
        kw_hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(kw_hint)

        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        save_btn = buttons.button(QDialogButtonBox.Save)
        save_btn.setText("保存")
        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setText("取消")
        layout.addWidget(buttons)

    def _on_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "请填写名称", "领域名称不能为空。")
            self.name_edit.setFocus()
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "keywords": self.kw_edit.text().strip(),
            "icon": "",
        }
