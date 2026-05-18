"""应用入口 —— 初始化数据库、启动 UI、配置系统托盘和调度器。"""

import sys
import json
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle
from PySide6.QtGui import QIcon, QAction

from .storage.migrations import init_database
from .scheduler.push_scheduler import PushScheduler
from .config import APPDIR, SETTINGS_PATH
from .ui.main_window import MainWindow


def create_tray_icon(app: QApplication, window: "MainWindow", scheduler: PushScheduler):
    """创建系统托盘图标。"""
    tray = QSystemTrayIcon(window)
    tray.setToolTip("Knowledge Push Assistant")

    # 尝试加载图标，没有则用默认
    icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
    if icon_path.exists():
        tray.setIcon(QIcon(str(icon_path)))
    else:
        tray.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

    menu = QMenu()

    show_action = QAction("打开主面板")
    show_action.triggered.connect(window.show)
    menu.addAction(show_action)

    push_now_action = QAction("立即推送一条")
    push_now_action.triggered.connect(lambda: window._on_push_requested())
    menu.addAction(push_now_action)

    menu.addSeparator()

    quit_action = QAction("退出")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: window.show() if reason == QSystemTrayIcon.DoubleClick else None)
    tray.show()

    return tray


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KnowledgePushAssistant")

    # 初始化数据库
    engine = init_database()

    # 加载设置
    from .storage import repository as repo
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        settings = repo.get_all_settings(session)

    # 创建主窗口
    window = MainWindow(engine, SETTINGS_PATH)

    # 调度器 —— 定时触发 Agent
    def on_scheduled_push():
        push_enabled = settings.get("push_enabled", True)
        if not push_enabled:
            return
        start_h = settings.get("push_start_hour", 8)
        end_h = settings.get("push_end_hour", 22)
        if not scheduler.is_within_time_window(start_h, end_h):
            return
        window._on_push_requested()

    scheduler = PushScheduler(on_scheduled_push)

    push_enabled = settings.get("push_enabled", True)
    interval = settings.get("push_interval_minutes", 60)

    if push_enabled:
        scheduler.start(interval)
        window.sidebar.set_status(True, "定时推送中")
    else:
        window.sidebar.set_status(False)

    # 系统托盘
    tray = create_tray_icon(app, window, scheduler)

    window.show()

    # 启动后刷新仪表盘
    window.dashboard_page.refresh()

    exit_code = app.exec()

    # 退出时清理
    scheduler.stop()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
