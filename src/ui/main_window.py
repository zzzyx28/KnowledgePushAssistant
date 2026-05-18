"""主窗口 —— frameless 窗口 + 标题栏 + 侧边栏 + 页面栈。"""

import json
from PySide6.QtCore import Qt, QTimer, QPoint, Signal, QRectF
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QSystemTrayIcon,
)
from PySide6.QtGui import QIcon, QPainterPath, QRegion

from .styles import GLOBAL_STYLESHEET, BG_MAIN
from .title_bar import TitleBar
from .sidebar import Sidebar
from .pages.dashboard import DashboardPage
from .pages.agent_panel import AgentPanel
from .pages.knowledge import KnowledgePage
from .pages.domain_manager import DomainManagerPage
from .pages.settings import SettingsPage
from .detail_window import DetailWindow
from .tray_notify import TrayNotifier


class MainWindow(QMainWindow):
    """应用主窗口。"""

    _push_notify = Signal(object)
    scheduled_push_requested = Signal()

    def __init__(self, db_engine, settings_file):
        super().__init__()
        self._engine = db_engine
        self._settings_file = settings_file
        self._tray = None
        self._tray_notifier: TrayNotifier | None = None
        self._push_scheduler = None
        self._push_running = False

        # frameless
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setWindowTitle("Knowledge Push")
        self.setMinimumSize(960, 640)

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

        self.pages.addWidget(self.dashboard_page)   # 0
        self.pages.addWidget(self.agent_panel)       # 1
        self.pages.addWidget(self.knowledge_page)    # 2
        self.pages.addWidget(self.domain_page)       # 3
        self.pages.addWidget(self.settings_page)     # 4

        self._page_index = {
            "dashboard": 0, "agent": 1, "knowledge": 2,
            "domains": 3, "settings": 4,
        }

        # 信号连线
        self.dashboard_page.push_requested.connect(
            lambda: self._on_push_requested(show_agent_panel=True)
        )
        self.agent_panel.push_requested.connect(
            lambda: self._on_push_requested(show_agent_panel=True)
        )
        self.dashboard_page.detail_requested.connect(self._open_detail)
        self.knowledge_page.detail_requested.connect(self._open_detail)
        self._push_notify.connect(self._show_tray_notification)
        self.scheduled_push_requested.connect(self._handle_scheduled_push)
        self.settings_page.settings_saved.connect(self.apply_push_schedule)

        self.settings_page.load_settings()

        # 默认选中仪表盘
        self.sidebar.set_active("dashboard")
        self.pages.setCurrentIndex(0)

        # 窗口圆角
        self._apply_rounded_corners()

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

    def set_push_scheduler(self, scheduler):
        """注入定时调度器（由 main 在启动时调用）。"""
        self._push_scheduler = scheduler

    def set_tray(self, tray: QSystemTrayIcon):
        """注入系统托盘并初始化跨平台推送通知。"""
        self._tray = tray
        self._tray_notifier = TrayNotifier(tray, self._open_detail)

    def _load_push_settings(self) -> dict:
        from ..storage import repository as repo

        with self._create_session() as session:
            return repo.get_all_settings(session)

    def apply_push_schedule(self):
        """根据数据库中的推送设置启动/停止/更新调度器。"""
        if not self._push_scheduler:
            return

        settings = self._load_push_settings()
        enabled = settings.get("push_enabled", True)
        interval = int(settings.get("push_interval_minutes", 60))
        interval = max(5, min(interval, 1440))

        if enabled:
            if self._push_scheduler.is_running:
                self._push_scheduler.update_interval(interval)
            else:
                self._push_scheduler.start(interval)
            self.sidebar.set_status(True, "定时推送中")
        else:
            self._push_scheduler.stop()
            self.sidebar.set_status(False, "定时推送已关闭")

    def _handle_scheduled_push(self):
        """定时器触发（主线程）：校验设置后执行推送。"""
        settings = self._load_push_settings()
        if not settings.get("push_enabled", True):
            return
        if not self._push_scheduler:
            return
        start_h = int(settings.get("push_start_hour", 8))
        end_h = int(settings.get("push_end_hour", 22))
        if not self._push_scheduler.is_within_time_window(start_h, end_h):
            return
        self._on_push_requested(show_agent_panel=False)

    def _on_push_requested(self, *, show_agent_panel: bool = True):
        """触发 Agent 推送流程。"""
        if self._push_running:
            return

        # 先加载设置
        self.settings_page.load_settings()
        settings = self.settings_page.get_settings_dict()

        model = settings.get("model_name", "deepseek-chat")
        base_url = settings.get("model_base_url", "https://api.deepseek.com")
        api_key = settings.get("model_api_key", "")
        user_pref = settings.get("user_preference_prompt", "")

        from ..llm.client import create_client
        from ..agent.defaults import DEFAULT_SYSTEM_PROMPT

        # 组合系统提示词 + 用户偏好
        parts = [DEFAULT_SYSTEM_PROMPT]
        if user_pref:
            parts.append(
                "\n---\n## 用户额外偏好（请遵循以下偏好调整推送内容与风格）\n"
                + user_pref
            )
        system_prompt = "\n".join(parts)

        try:
            client = create_client(base_url, api_key)
        except Exception as e:
            self.agent_panel.add_step({"type": "error", "content": f"创建客户端失败: {e}"})
            self.sidebar.set_active("agent")
            self.pages.setCurrentIndex(1)
            return

        def on_push(item):
            self.dashboard_page.set_push_status("刚刚推送")
            self._push_notify.emit(item)

        def on_flow_finished():
            self._push_running = False

        self._push_running = True
        self.agent_panel.run_agent_flow(
            client, model, system_prompt, on_push, on_finished=on_flow_finished
        )
        if show_agent_panel:
            self.sidebar.set_active("agent")
            self.pages.setCurrentIndex(1)

    def _show_tray_notification(self, item):
        """主线程：在系统托盘显示推送消息（macOS / Windows）。"""
        if self._tray_notifier:
            self._tray_notifier.show_push(item)
        elif self._tray:
            self._tray.showMessage(
                item.title or "新知识推送",
                (item.summary or "")[:240],
                QSystemTrayIcon.MessageIcon.Information,
                8000,
            )

    def _open_detail(self, item_id: int):
        """打开知识详情并标记为已读。"""
        from ..storage import repository as repo

        session = self._create_session()
        try:
            item = repo.get_knowledge_item_by_id(session, item_id)
            if not item:
                return
            repo.update_knowledge_item(session, item_id, is_read=True)
            repo.mark_push_clicked(session, item_id)
            item = repo.get_knowledge_item_by_id(session, item_id)
            self._detail_window = DetailWindow(
                item, lambda: self._create_session(), parent=None
            )
            self._detail_window.show()
            self.knowledge_page.refresh()
            self.dashboard_page.refresh()
        finally:
            session.close()

    def show_and_raise(self):
        """从托盘恢复主窗口。"""
        self.show()
        self.raise_()
        self.activateWindow()

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
                w = data.get("window_width", 1060)
                h = data.get("window_height", 700)
                self.setGeometry(x, y, w, h)
            else:
                self.resize(1060, 700)
        except Exception:
            self.resize(1060, 700)

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

    def _apply_rounded_corners(self):
        r = 10
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), r, r)
        poly = path.toFillPolygon().toPolygon()
        self.setMask(QRegion(poly))

    def resizeEvent(self, event):
        self._save_geometry()
        self._apply_rounded_corners()
        super().resizeEvent(event)

    def closeEvent(self, event):
        self._save_geometry()
        if self._tray and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            return
        super().closeEvent(event)
