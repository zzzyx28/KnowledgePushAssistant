"""知识推送通知弹窗 —— macOS 通知卡片风格。"""

from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QMouseEvent

from .styles import (
    BG_GLASS_STRONG, BORDER_GLASS, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY,
    RADIUS_XL, tag_style, primary_button_style,
)
from .widgets import WrappingLabel


def _truncate(text: str, max_len: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


class PopupWindow(QWidget):
    """推送通知窗口。"""

    clicked = Signal(int)
    closed = Signal()

    def __init__(self, item, parent=None):
        super().__init__(
            parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self._item_id = item.id
        self._dragging = False
        self._press_pos = QPoint()
        self._moved = False
        self._auto_close_seconds = 8

        self.setFixedWidth(400)
        self.setMinimumHeight(180)
        self.setStyleSheet(f"""
            PopupWindow {{
                background: {BG_GLASS_STRONG};
                border: 1px solid {BORDER_GLASS};
                border-radius: {RADIUS_XL};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(10)

        tag = QLabel(item.domain_name or "新推送")
        tag.setStyleSheet(tag_style())
        tag.setSizePolicy(tag.sizePolicy().horizontalPolicy(), tag.sizePolicy().verticalPolicy())
        layout.addWidget(tag, 0, Qt.AlignLeft)

        title = WrappingLabel(item.title or "无标题")
        title.setStyleSheet(
            f"font-weight: 600; font-size: 16px; color: {TEXT_PRIMARY}; "
            f"letter-spacing: -0.3px;"
        )
        title.setMinimumLines(1)
        layout.addWidget(title)

        summary = WrappingLabel(_truncate(item.summary or "", 120) or "暂无摘要")
        summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        summary.setMinimumLines(2)
        layout.addWidget(summary)

        self._hint = QLabel("")
        self._hint.setStyleSheet(f"color: {TEXT_TERTIARY}; font-size: 11px;")
        layout.addWidget(self._hint)

        open_btn = QPushButton("查看详情")
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.setStyleSheet(primary_button_style(height=36))
        open_btn.clicked.connect(self._open_detail)
        layout.addWidget(open_btn)

        self.setCursor(Qt.PointingHandCursor)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)
        self.adjustSize()

    def _update_hint(self):
        self._hint.setText(f"{self._auto_close_seconds} 秒后自动关闭")

    def start_auto_close(self, seconds: int = 8):
        self._auto_close_seconds = seconds
        self._update_hint()
        self._timer.start(seconds * 1000)

    def _open_detail(self):
        self._timer.stop()
        self.clicked.emit(self._item_id)
        self.close()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._moved = False
            self._press_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._press_pos
            if delta.manhattanLength() > 4:
                self._moved = True
            self.move(self.pos() + delta)
            self._press_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self._dragging:
            self._dragging = False
            if not self._moved:
                self._open_detail()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
