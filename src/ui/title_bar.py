"""自定义标题栏 —— frameless 窗口 + 品牌名/状态点 + 窗口控制。"""

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent, QIcon
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy


class TitleBar(QWidget):
    """可拖拽的自定义标题栏。"""

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_pos = QPoint()
        self.setFixedHeight(40)
        self.setObjectName("titleBar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(0)

        # 左侧 —— 品牌名 + 状态点
        left = QHBoxLayout()
        left.setSpacing(8)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #22c55e; font-size: 10px;")
        self.status_dot.setFixedWidth(14)
        left.addWidget(self.status_dot)

        brand = QLabel("Knowledge Push")
        brand.setStyleSheet("font-weight: 600; font-size: 13px; color: #1a1d2e;")
        left.addWidget(brand)

        left.addStretch()
        layout.addLayout(left, 1)

        # 右侧 —— 窗口控制按钮
        for icon, signal_name, css_class in [
            ("─", "minimize_clicked", "min-btn"),
            ("□", "maximize_clicked", "max-btn"),
            ("✕", "close_clicked", "close-btn"),
        ]:
            btn = QPushButton(icon)
            btn.setFixedSize(32, 28)
            btn.setStyleSheet(self._btn_style(css_class))
            btn.clicked.connect(getattr(self, signal_name))
            layout.addWidget(btn)

    def _btn_style(self, css_class: str) -> str:
        base = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                color: #6b7280;
                padding: 0;
            }
            QPushButton:hover { background: #e5e7eb; }
        """
        if css_class == "close-btn":
            base += "QPushButton:hover { background: #ef4444; color: #ffffff; }"
        return base

    def set_status(self, online: bool):
        color = "#22c55e" if online else "#9ca3af"
        self.status_dot.setStyleSheet(f"color: {color}; font-size: 10px;")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self._drag_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._dragging and event.buttons() & Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self._drag_pos
            window = self.window()
            if window:
                window.move(window.pos() + delta)
            self._drag_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.maximize_clicked.emit()
