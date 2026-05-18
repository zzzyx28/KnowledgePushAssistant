"""知识卡片弹出窗口 —— 定时推送时弹出，显示摘要 + 点击展开详情。"""

from PySide6.QtCore import Qt, QTimer, Signal, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtGui import QMouseEvent

from .styles import BG_CARD, ACCENT, ACCENT_LIGHT, RADIUS_MD, RADIUS_LG, TEXT_PRIMARY, TEXT_SECONDARY


class PopupWindow(QWidget):
    """知识卡片弹出窗口 —— 无边框、自动消失。"""

    clicked = Signal(int)   # item_id
    closed = Signal()

    def __init__(self, item, parent=None):
        super().__init__(parent, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self._item_id = item.id
        self._dragging = False
        self._drag_pos = QPoint()

        self.setFixedSize(340, 180)
        self.setStyleSheet(f"""
            PopupWindow {{
                background: {BG_CARD};
                border: 1px solid #e5e7eb;
                border-radius: {RADIUS_XL};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(8)

        # 领域标签
        tag = QLabel(f"{item.domain_name}")
        tag.setStyleSheet(f"""
            background: {ACCENT_LIGHT}; color: {ACCENT};
            border-radius: 6px; padding: 2px 10px; font-size: 11px; font-weight: 500;
        """)
        tag.setFixedWidth(tag.sizeHint().width() + 20)
        layout.addWidget(tag)

        # 标题
        title = QLabel(item.title)
        title.setStyleSheet(f"font-weight: 700; font-size: 16px; color: {TEXT_PRIMARY};")
        title.setWordWrap(True)
        layout.addWidget(title)

        # 摘要
        summary = QLabel(item.summary)
        summary.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        summary.setWordWrap(True)
        layout.addWidget(summary)

        # 提示
        hint = QLabel("点击卡片查看详情 · 5秒后自动关闭")
        hint.setStyleSheet(f"color: #9ca3af; font-size: 10px;")
        layout.addWidget(hint)

        layout.addStretch()

        # 点击打开详情
        self.setCursor(Qt.PointingHandCursor)

        # 自动关闭计时器
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.close)

    def start_auto_close(self, seconds: int = 5):
        self._timer.start(seconds * 1000)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._dragging:
            self._dragging = False
            # 如果没怎么拖，当作点击
            if (event.globalPosition().toPoint() - self._drag_pos).manhattanLength() < 5:
                self.clicked.emit(self._item_id)
                self._timer.stop()
                self.close()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
