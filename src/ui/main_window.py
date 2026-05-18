"""主窗口 —— frameless 窗口 + 标题栏 + 侧边栏 + 页面栈。"""

import json
from PySide6.QtCore import Qt, QTimer, QPoint
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QApplication
)
from PySide6.QtGui import QIcon

from .styles import GLOBAL_STYLESHEET, BG_MAIN
from .title_bar import TitleBar
from .sidebar import Sidebar
from .pages.dashboard import DashboardPage
from .pages.agent_panel import AgentPanel
from .pages.knowledge import KnowledgePage
from .pages.domain_manager import DomainManagerPage
from .pages.settings import SettingsPage
from .pages.chat import ChatPage
from .popup import PopupWindow
from .detail_window import DetailWindow


class MainWindow(QMainWindow):
    """应用主窗口。"""

    def __init__(self, db_engine, settings_file):
        super().__init__()
        self._engine = db_engine
        self._settings_file = settings_file
        self._popup = None

        # frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Knowledge Push")
        self.setMinimumSize(900, 600)

        self.setStyleSheet(GLOBAL_STYLESHEET)
        self.setStyleSheet(self.styleSheet() + f"QMainWindow {{ background: {BG_MAIN}; }}")

        # 恢复窗口位置/大小
        self._restore_geometry()

        # 主容器
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        self.title_bar = TitleBar(self)
        self.title_bar.minimize_clicked.connect(self.showMinimized)
        self.title_bar.maximize_clicked.connect(self._toggle_maximize)
        self.title_bar.close_clicked.connect(self.close)
        main_layout.addWidget(self.title_bar)

        # 内容区 (侧边栏 + 页面栈)
        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        self.sidebar = Sidebar(self)
        self.sidebar.page_changed.connect(self._on_page_changed)
        content.addWidget(self.sidebar)

        self.pages = QStackedWidget()
        content.addWidget(self.pages, 1)

        main_layout.addLayout(content, 1)

        # 创建页面
        session_factory = lambda: self._create_session()

        self.dashboard_page = DashboardPage(session_factory)
        self.agent_panel = AgentPanel(session_factory)
        self.knowledge_page = KnowledgePage(session_factory)
        self.domain_page = DomainManagerPage(session_factory)
        self.settings_page = SettingsPage(session_factory)
        self.chat_page = ChatPage(session_factory)

        self.pages.addWidget(self.dashboard_page)   # 0
        self.pages.addWidget(self.agent_panel)       # 1
        self.pages.addWidget(self.knowledge_page)    # 2
        self.pages.addWidget(self.domain_page)       # 3
        self.pages.addWidget(self.settings_page)     # 4
        self.pages.addWidget(self.chat_page)         # 5

        self._page_index = {
            "dashboard": 0, "agent": 1, "knowledge": 2,
            "domains": 3, "settings": 4, "chat": 5,
        }

        # 信号连线
        self.dashboard_page.push_requested.connect(self._on_push_requested)
        self.agent_panel.push_requested.connect(self._on_push_requested)

        # 默认选中仪表盘
        self.sidebar.set_active("dashboard")
        self.pages.setCurrentIndex(0)

    def _create_session(self):
        from sqlalchemy.orm import Session
        return Session(self._engine)

    def _on_page_changed(self, route: str):
        idx = self._page_index.get(route, 0)
        self.pages.setCurrentIndex(idx)
        # 刷新对应页面
        page = self.pages.widget(idx)
        if hasattr(page, "refresh"):
            page.refresh()
        elif route == "settings" and hasattr(page, "load_settings"):
            page.load_settings()

    def _on_push_requested(self):
        """触发 Agent 推送流程。"""
        # 先加载设置
        self.settings_page.load_settings()
        settings = self.settings_page.get_settings_dict()

        model = settings.get("model_name", "deepseek-chat")
        base_url = settings.get("model_base_url", "https://api.deepseek.com")
        api_key = settings.get("model_api_key", "")
        system_prompt = settings.get("system_prompt", "")

        from ..llm.client import create_client
        from ..agent.defaults import DEFAULT_SYSTEM_PROMPT

        if not system_prompt:
            system_prompt = DEFAULT_SYSTEM_PROMPT

        try:
            client = create_client(base_url, api_key)
        except Exception as e:
            self.agent_panel.add_step({"type": "error", "content": f"创建客户端失败: {e}"})
            self.sidebar.set_active("agent")
            self.pages.setCurrentIndex(1)
            return

        def on_push(item):
            self.dashboard_page.set_push_status("刚刚推送")
            self._show_popup(item)

        self.agent_panel.run_agent_flow(client, model, system_prompt, on_push)
        self.sidebar.set_active("agent")
        self.pages.setCurrentIndex(1)

    def _show_popup(self, item):
        """显示知识卡片弹出窗口。"""
        screen = QApplication.primaryScreen().availableGeometry()
        x = screen.right() - 360
        y = screen.bottom() - 200

        self._popup = PopupWindow(item)
        self._popup.move(x, y)
        self._popup.clicked.connect(self._on_popup_clicked)
        self._popup.closed.connect(self._on_popup_closed)
        self._popup.start_auto_close(7)
        self._popup.show()

    def _on_popup_clicked(self, item_id: int):
        from ..storage import repository as repo
        session = self._create_session()
        item = repo.get_knowledge_item_by_id(session, item_id)
        if item:
            self._detail_window = DetailWindow(item, lambda: self._create_session())
            self._detail_window.show()
        session.close()

    def _on_popup_closed(self):
        self._popup = None

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _restore_geometry(self):
        try:
            if self._settings_file.exists():
                data = json.loads(self._settings_file.read_text(encoding="utf-8"))
                x = data.get("window_x", 200)
                y = data.get("window_y", 100)
                w = data.get("window_width", 900)
                h = data.get("window_height", 600)
                self.setGeometry(x, y, w, h)
            else:
                self.resize(900, 600)
        except Exception:
            self.resize(900, 600)

    def _save_geometry(self):
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            g = self.geometry()
            data = {
                "window_x": g.x(),
                "window_y": g.y(),
                "window_width": g.width(),
                "window_height": g.height(),
            }
            self._settings_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def moveEvent(self, event):
        self._save_geometry()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self._save_geometry()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self._save_geometry()
        super().closeEvent(event)
