"""侧边栏导航 —— 菜单项（含路由 + 图标）+ 在线状态。"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QSizePolicy


class Sidebar(QWidget):
    """侧边栏导航组件。"""

    page_changed = Signal(str)

    MENU_ITEMS = [
        ("dashboard", "📊", "仪表盘"),
        ("agent", "🧠", "Agent"),
        ("knowledge", "📖", "知识管理"),
        ("domains", "🏷️", "领域管理"),
        ("settings", "⚙️", "推送设置"),
        ("chat", "💬", "教学对话"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setObjectName("sidebar")
        self.setStyleSheet(f"""
            #sidebar {{
                background: #1e1f2b;
                border-right: 1px solid #2d2e3a;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部留白
        spacer_top = QWidget()
        spacer_top.setFixedHeight(16)
        layout.addWidget(spacer_top)

        # 菜单项
        self._buttons = {}
        for route, icon, label in self.MENU_ITEMS:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setFixedHeight(44)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("route", route)
            btn.clicked.connect(lambda checked, r=route: self._on_click(r))
            self._buttons[route] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # 底部在线状态
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(16, 12, 16, 16)

        self.status_label = QLabel("🟢  在线")
        self.status_label.setStyleSheet("color: #c4c5d0; font-size: 12px;")
        status_layout.addWidget(self.status_label)

        layout.addWidget(status_widget)

        # 初始样式
        self._update_styles()

    def _update_styles(self):
        for route, btn in self._buttons.items():
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 8px;
                    margin: 2px 10px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 13px;
                    color: #c4c5d0;
                }
                QPushButton:hover {
                    background: #2d2e3a;
                    color: #ffffff;
                }
            """)

    def set_active(self, route: str):
        """高亮当前选中的菜单项。"""
        self._update_styles()
        btn = self._buttons.get(route)
        if btn:
            btn.setStyleSheet("""
                QPushButton {
                    background: #6366f1;
                    border: none;
                    border-radius: 8px;
                    margin: 2px 10px;
                    text-align: left;
                    padding-left: 12px;
                    font-size: 13px;
                    color: #ffffff;
                }
            """)

    def set_status(self, enabled: bool, text: str = ""):
        if not enabled:
            self.status_label.setText("⏸  已暂停")
            self.status_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
        elif text:
            self.status_label.setText(f"🟢  {text}")
            self.status_label.setStyleSheet("color: #c4c5d0; font-size: 12px;")
        else:
            self.status_label.setText("🟢  在线")
            self.status_label.setStyleSheet("color: #c4c5d0; font-size: 12px;")

    def _on_click(self, route: str):
        self.set_active(route)
        self.page_changed.emit(route)
