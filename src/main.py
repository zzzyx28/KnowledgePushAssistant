"""应用入口 —— 初始化数据库、启动 UI、配置系统托盘和调度器。"""

import sys

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle, QMessageBox
from PySide6.QtGui import QIcon, QAction, QCursor

from .storage.migrations import init_database
from .scheduler.push_scheduler import PushScheduler
from .config import SETTINGS_PATH, resolve_tray_icon_path
from .ui.main_window import MainWindow


def _build_tray_menu(window: MainWindow, app: QApplication) -> QMenu:
    """构建托盘菜单（父对象为主窗口，避免被 GC）。"""
    menu = QMenu(window)
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


def _popup_tray_menu(menu: QMenu) -> None:
    """非阻塞弹出菜单（避免 exec 嵌套事件循环导致卡死）。"""
    if menu.isVisible():
        return
    pos = QCursor.pos()
    if pos.x() == 0 and pos.y() == 0:
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            pos = geo.bottomRight() - QPoint(200, 120)
    menu.popup(pos)


def _wire_tray_macos(tray: QSystemTrayIcon, menu: QMenu, window: MainWindow) -> None:
    """macOS：仅使用 setContextMenu，由系统显示菜单；勿再手动 popup/exec。"""
    tray.setContextMenu(menu)

    def on_activated(reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            window.show_and_raise()

    tray.activated.connect(on_activated)


def _wire_tray_windows(tray: QSystemTrayIcon, menu: QMenu, window: MainWindow) -> None:
    """Windows：不用 setContextMenu（会与 activated 冲突）；右键手动 popup。"""
    # 勿调用 tray.setContextMenu(menu)

    def on_activated(reason: QSystemTrayIcon.ActivationReason):
        if reason == QSystemTrayIcon.ActivationReason.Context:
            _popup_tray_menu(menu)
        elif reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            window.show_and_raise()

    tray.activated.connect(on_activated)


def _wire_tray_linux(tray: QSystemTrayIcon, menu: QMenu, window: MainWindow) -> None:
    """Linux 等：与 Windows 相同策略。"""
    _wire_tray_windows(tray, menu, window)


def create_tray_icon(app: QApplication, window: MainWindow) -> QSystemTrayIcon | None:
    """创建系统托盘图标；不可用时返回 None。

    交互约定：
    - macOS：单击由系统弹出菜单（setContextMenu），双击打开主窗口
    - Windows：左键打开主窗口，右键弹出菜单
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

    menu = _build_tray_menu(window, app)
    window._tray_menu = menu

    if sys.platform == "darwin":
        _wire_tray_macos(tray, menu, window)
    elif sys.platform == "win32":
        _wire_tray_windows(tray, menu, window)
    else:
        _wire_tray_linux(tray, menu, window)

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
