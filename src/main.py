"""应用入口 —— 初始化数据库、启动 UI、配置系统托盘和调度器。"""

import sys

from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle, QMessageBox
from PySide6.QtGui import QIcon, QAction, QCursor

from .storage.migrations import init_database
from .scheduler.push_scheduler import PushScheduler
from .config import SETTINGS_PATH, resolve_tray_icon_path
from .ui.main_window import MainWindow


def create_tray_icon(app: QApplication, window: MainWindow) -> QSystemTrayIcon | None:
    """创建系统托盘图标；不可用时返回 None。

    macOS 左/右键均弹出菜单；Windows 右键弹出菜单、双击打开窗口。
    """
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None

    tray = QSystemTrayIcon(window)
    tray.setToolTip("Knowledge Push Assistant")

    icon_path = resolve_tray_icon_path()
    if icon_path:
        tray.setIcon(QIcon(str(icon_path)))
    else:
        tray.setIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))

    # ---- 右键菜单 ----
    menu = QMenu()

    show_action = QAction("打开主面板")
    show_action.triggered.connect(window.show_and_raise)
    menu.addAction(show_action)

    push_now_action = QAction("立即推送一条")
    push_now_action.triggered.connect(
        lambda: window._on_push_requested(show_agent_panel=True)
    )
    menu.addAction(push_now_action)

    menu.addSeparator()

    quit_action = QAction("退出")
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    tray.setContextMenu(menu)

    # ---- 点击行为（跨平台适配） ----
    def on_activated(reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            window.show_and_raise()
        elif reason == QSystemTrayIcon.ActivationReason.Context:
            # macOS 右键 → 弹出菜单（setContextMenu 已处理常规情况，
            # 这里兜底处理某些 macOS 版本不自动弹出菜单的问题）
            menu.popup(QCursor.pos())
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            # macOS 左键也弹出菜单（符合 macOS 菜单栏图标习惯）
            if sys.platform == "darwin":
                menu.popup(QCursor.pos())
            else:
                window.show_and_raise()

    tray.activated.connect(on_activated)
    tray.show()
    return tray


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("KnowledgePushAssistant")
    app.setQuitOnLastWindowClosed(False)

    engine = init_database()
    window = MainWindow(engine, SETTINGS_PATH)

    def on_scheduled_push():
        window.scheduled_push_requested.emit()

    scheduler = PushScheduler(on_scheduled_push)
    window.set_push_scheduler(scheduler)
    window.apply_push_schedule()

    tray = create_tray_icon(app, window)
    if tray:
        window.set_tray(tray)
    else:
        QMessageBox.warning(
            None,
            "托盘不可用",
            "当前系统无法显示托盘图标，定时推送通知可能无法弹出。\n"
            "请保持主窗口打开，或更换桌面环境后重试。",
        )

    window.show()
    window.dashboard_page.refresh()

    exit_code = app.exec()
    scheduler.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
