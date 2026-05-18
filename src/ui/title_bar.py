"""标题栏 —— 可拖拽顶栏 + 简洁窗口控制。"""

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton

from .styles import BG_TITLEBAR, BORDER_GLASS, TEXT_PRIMARY, TEXT_SECONDARY, SUCCESS, BG_FILL


class TitleBar(QWidget):
    """可拖拽标题栏。"""

    minimize_clicked = Signal()
    maximize_clicked = Signal()
    close_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging = False
        self._drag_pos = QPoint()
        self.setFixedHeight(48)
        self.setObjectName("titleBar")
        self.setStyleSheet(f"""
            #titleBar {{
                background: {BG_TITLEBAR};
                border-bottom: 1px solid {BORDER_GLASS};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 10, 0)
        layout.setSpacing(0)

        # 状态指示点
        self.status_dot = QLabel()
        self.status_dot.setFixedSize(8, 8)
        self.status_dot.setStyleSheet(
            f"background: {SUCCESS}; border-radius: 4px;"
        )
        layout.addWidget(self.status_dot)
        layout.addStretch()

        # 窗口控制按钮
        btn_style = f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {TEXT_SECONDARY};
                font-size: 13px;
                font-weight: 500;
                min-width: 28px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background: {BG_FILL};
                color: {TEXT_PRIMARY};
            }}
        """

        min_btn = QPushButton("—")  # em dash
        min_btn.setCursor(Qt.PointingHandCursor)
        min_btn.setStyleSheet(btn_style)
        min_btn.clicked.connect(self.minimize_clicked.emit)
        layout.addWidget(min_btn)

        max_btn = QPushButton("⧉")  # square / maximize icon
        max_btn.setCursor(Qt.PointingHandCursor)
        max_btn.setStyleSheet(btn_style)
        max_btn.clicked.connect(self.maximize_clicked.emit)
        layout.addWidget(max_btn)

        close_btn = QPushButton("✕")  # ✕
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 4px;
                color: {TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 500;
                min-width: 28px;
                min-height: 24px;
            }}
            QPushButton:hover {{
                background: #FF3B30;
                color: #FFFFFF;
            }}
        """)
        close_btn.clicked.connect(self.close_clicked.emit)
        layout.addWidget(close_btn)

    def set_status(self, online: bool):
        color = SUCCESS if online else "#C7C7CC"
        self.status_dot.setStyleSheet(
            f"background: {color}; border-radius: 4px;"
        )

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            child = self.childAt(event.position().toPoint())
            if isinstance(child, QPushButton):
                return super().mousePressEvent(event)
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
        child = self.childAt(event.position().toPoint())
        if not isinstance(child, QPushButton):
            self.maximize_clicked.emit()
