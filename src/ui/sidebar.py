"""侧边栏 —— macOS 设置式分组导航。"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout

from .styles import (
    BG_SIDEBAR, BORDER_GLASS, ACCENT, ACCENT_FILL,
    TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS, WARNING,
    FONT_SIZE_SM, SIDEBAR_WIDTH, RADIUS_SM,
)


class Sidebar(QWidget):
    """侧边栏导航。"""

    page_changed = Signal(str)

    MENU_ITEMS = [
        ("dashboard", "仪表盘", "📊"),
        ("agent", "智能推送", "⚡"),
        ("knowledge", "知识库", "📚"),
        ("domains", "领域管理", "🏷"),
        ("settings", "设置", "⚙"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"""
            #sidebar {{
                background: {BG_SIDEBAR};
                border-right: 1px solid {BORDER_GLASS};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(2)

        # 品牌
        brand = QLabel("Knowledge Push")
        brand.setStyleSheet(f"""
            font-size: 13px;
            font-weight: 700;
            color: {TEXT_PRIMARY};
            padding: 6px 10px 18px 10px;
            letter-spacing: -0.3px;
        """)
        layout.addWidget(brand)

        # 导航按钮
        self._buttons = {}
        for route, label, icon in self.MENU_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setFixedHeight(32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("route", route)
            btn.clicked.connect(lambda checked, r=route: self._on_click(r))
            self._buttons[route] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # 状态指示器
        status_row = QHBoxLayout()
        status_row.setContentsMargins(10, 0, 10, 4)

        self.status_dot = QLabel()
        self.status_dot.setFixedSize(7, 7)
        self.status_dot.setStyleSheet(
            f"background: {SUCCESS}; border-radius: 3px;"
        )
        status_row.addWidget(self.status_dot, 0, Qt.AlignVCenter)
        status_row.addSpacing(6)

        self.status_label = QLabel("运行中")
        self.status_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_SM};"
        )
        status_row.addWidget(self.status_label, 0, Qt.AlignVCenter)
        status_row.addStretch()
        layout.addLayout(status_row)

        self._active_route = "dashboard"
        self._apply_nav_styles()

    def _nav_inactive(self) -> str:
        return f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: {RADIUS_SM};
                text-align: left;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: 450;
                color: {TEXT_PRIMARY};
            }}
            QPushButton:hover {{
                background: rgba(0, 0, 0, 0.04);
            }}
        """

    def _nav_active(self) -> str:
        return f"""
            QPushButton {{
                background: {ACCENT_FILL};
                border: none;
                border-radius: {RADIUS_SM};
                text-align: left;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: 600;
                color: {ACCENT};
            }}
        """

    def _apply_nav_styles(self):
        for route, btn in self._buttons.items():
            btn.setStyleSheet(
                self._nav_active() if route == self._active_route else self._nav_inactive()
            )

    def set_active(self, route: str):
        self._active_route = route
        self._apply_nav_styles()

    def set_status(self, enabled: bool, text: str = ""):
        dot_color = SUCCESS if enabled else "#C7C7CC"
        if not enabled:
            self.status_label.setText("已暂停")
            self.status_label.setStyleSheet(f"color: {WARNING}; font-size: {FONT_SIZE_SM};")
        elif text:
            self.status_label.setText(text)
            self.status_label.setStyleSheet(f"color: {SUCCESS}; font-size: {FONT_SIZE_SM};")
        else:
            self.status_label.setText("运行中")
            self.status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_SM};")
        self.status_dot.setStyleSheet(f"background: {dot_color}; border-radius: 3px;")

    def _on_click(self, route: str):
        self.set_active(route)
        self.page_changed.emit(route)
