"""应用入口 —— 初始化数据库、启动 UI、配置系统托盘和调度器。"""

import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle, QMessageBox
from PySide6.QtGui import QIcon, QAction, QCursor

from .storage.migrations import init_database
from .scheduler.push_scheduler import PushScheduler
from .config import SETTINGS_PATH, resolve_tray_icon_path
from .ui.main_window import MainWindow


def _show_tray_menu(menu: QMenu) -> None:
    """在光标处显示托盘菜单（exec 在 Win/mac 上比 popup 更可靠）。"""
    pos = QCursor.pos()
    if pos.x() == 0 and pos.y() == 0:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            pos = geo.bottomRight() - QPoint(200, 120)
    menu.exec(pos)


def _build_tray_menu(tray: QSystemTrayIcon, window: MainWindow, app: QApplication) -> QMenu:
    """构建托盘右键菜单（父对象为 tray，避免被 GC）。"""
    menu = QMenu(tray)
    menu.setMinimumWidth(168)
    menu.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)

    show_action = QAction("打开主面板", menu)
    show_action.triggered.connect(window.show_and_raise)
    menu.addAction(show_action)

    push_now_action = QAction("立即推送一条", menu)
    push_now_action.triggered.connect(
        lambda: window._on_push_requested(show_agent_panel=True)
    )
    menu.addAction(push_now_action)

    menu.addSeparator()

    quit_action = QAction("退出", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)

    return menu


def create_tray_icon(app: QApplication, window: MainWindow) -> QSystemTrayIcon | None:
    """创建系统托盘图标；不可用时返回 None。

    交互约定：
    - Windows：左键打开主窗口，右键弹出菜单
    - macOS：单击弹出菜单（含「打开」「退出」），双击打开主窗口
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

    menu = _build_tray_menu(tray, window, app)
    window._tray_menu = menu  # 防止菜单被回收

    def on_activated(reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            # Windows 右键（及部分 macOS 辅助点按）
            _show_tray_menu(menu)
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            window.show_and_raise()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            if sys.platform == "win32":
                # Windows 左键：打开主窗口
                window.show_and_raise()
            else:
                # macOS 无独立右键信号时，单击弹出菜单
                _show_tray_menu(menu)

    tray.activated.connect(on_activated)

    # Windows：勿同时使用 setContextMenu 与 activated，否则右键菜单常被吞掉。
    # macOS：注册 contextMenu 供辅助点按走原生路径，单击仍由 Trigger 手动弹出。
    if sys.platform == "darwin":
        tray.setContextMenu(menu)

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
