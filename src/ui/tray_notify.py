"""跨平台托盘气泡通知（macOS / Windows，基于 QSystemTrayIcon.showMessage）。"""

from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtWidgets import QSystemTrayIcon


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class TrayNotifier:
    """推送成功时在系统托盘显示消息；点击消息打开详情。"""

    def __init__(
        self,
        tray: QSystemTrayIcon,
        on_open_detail: Callable[[int], None],
        *,
        display_ms: int = 8000,
    ):
        self._tray = tray
        self._on_open_detail = on_open_detail
        self._display_ms = display_ms
        self._pending_item_id: Optional[int] = None
        tray.messageClicked.connect(self._on_message_clicked)

    def show_push(self, item) -> bool:
        """显示推送托盘消息。返回 False 表示托盘不可用。"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False
        if not self._tray.isVisible():
            self._tray.show()

        self._pending_item_id = item.id
        title = _truncate(item.title or "新知识推送", 64)
        body = _truncate(item.summary or item.domain_name or "点击查看详情", 240)

        self._tray.showMessage(
            title,
            body,
            QSystemTrayIcon.MessageIcon.Information,
            self._display_ms,
        )
        return True

    def _on_message_clicked(self):
        item_id = self._pending_item_id
        self._pending_item_id = None
        if item_id is not None:
            self._on_open_detail(item_id)
