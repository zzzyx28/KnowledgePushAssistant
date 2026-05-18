"""可复用 UI 组件 —— Apple HIG 风格。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSpinBox, QPushButton, QAbstractSpinBox,
    QSizePolicy,
)

from .styles import (
    BG_CARD, BG_MAIN, BORDER, BORDER_LIGHT, TEXT_PRIMARY, TEXT_SECONDARY,
    RADIUS_LG, RADIUS_SECTION, ACCENT, SEPARATOR_SUBTLE, BG_STICKY,
    scroll_area_style, section_heading_style, settings_row_style,
    spinbox_center_style, stepper_button_style, stepper_container_style,
)


class SmoothScrollArea(QScrollArea):
    """统一滚动条与透明背景的滚动区域。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet(scroll_area_style())


class PageHeader(QWidget):
    """页面标题 + 描述 + 可选右侧操作区。"""

    def __init__(
        self,
        title: str,
        description: str = "",
        parent=None,
    ):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 4)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(16)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)

        self._title = QLabel(title)
        self._title.setProperty("cssClass", "page-title")
        text_col.addWidget(self._title)

        self._desc = QLabel(description)
        self._desc.setProperty("cssClass", "page-desc")
        self._desc.setVisible(bool(description))
        text_col.addWidget(self._desc)

        top.addLayout(text_col, 1)
        self._actions = QHBoxLayout()
        self._actions.setSpacing(8)
        top.addLayout(self._actions)
        root.addLayout(top)

    def add_action(self, widget: QWidget):
        self._actions.addWidget(widget)


class WrappingLabel(QLabel):
    """自动计算换行高度的标签，避免内容被裁切。"""

    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setWordWrap(True)
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._min_lines = 1

    def setMinimumLines(self, lines: int):
        self._min_lines = max(1, lines)
        self._update_height()

    def setText(self, text: str):
        super().setText(text)
        self._update_height()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_height()

    def _update_height(self):
        if self.width() <= 0:
            return
        fm = QFontMetrics(self.font())
        line_h = fm.lineSpacing()
        text = self.text() or ""
        rect = fm.boundingRect(
            0, 0, max(self.width() - 4, 40), 10000,
            int(Qt.TextWordWrap), text,
        )
        lines = max(self._min_lines, rect.height() // max(line_h, 1) + (1 if text else 0))
        self.setMinimumHeight(lines * line_h + 4)


class SettingsGroup(QFrame):
    """macOS 设置式分组卡片 —— 白底圆角 inset 容器。"""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QLabel(title.upper())
        header.setStyleSheet(section_heading_style())
        layout.addWidget(header)
        layout.addSpacing(8)

        self._inner = QFrame()
        self._inner.setObjectName("settingsGroup")
        from .styles import settings_group_style as sgs
        self._inner.setStyleSheet(sgs())
        inner_layout = QVBoxLayout(self._inner)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(0)
        self.body = inner_layout
        layout.addWidget(self._inner)

    def add_row(self, widget: QWidget, *, divider: bool = True):
        if self.body.count() > 0 and divider:
            sep = QFrame()
            sep.setFixedHeight(1)
            sep.setStyleSheet(
                f"background: {SEPARATOR_SUBTLE}; border: none; "
                f"margin: 0 18px; max-height: 1px;"
            )
            self.body.addWidget(sep)
        wrap = QWidget()
        wrap.setObjectName("settingsRow")
        wrap.setStyleSheet(
            settings_row_style(last=not divider)
        )
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(0)
        lay.addWidget(widget)
        self.body.addWidget(wrap)


class FormRow(QWidget):
    """标签 + 控件 + 可选提示。"""

    def __init__(self, label: str, widget: QWidget, hint: str = "", parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)

        lbl_col = QVBoxLayout()
        lbl_col.setSpacing(2)
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 500; color: {TEXT_PRIMARY};"
        )
        lbl_col.addWidget(lbl)
        if hint:
            h = QLabel(hint)
            h.setWordWrap(True)
            h.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
            lbl_col.addWidget(h)
        lay.addLayout(lbl_col, 1)
        lay.addWidget(widget, 0, Qt.AlignRight | Qt.AlignVCenter)


class StepperSpinBox(QWidget):
    """macOS 风格步进器：圆角容器内 − 数值 +。"""

    valueChanged = Signal(int)

    def __init__(
        self,
        minimum: int = 0,
        maximum: int = 100,
        value: int = 0,
        suffix: str = "",
        parent=None,
    ):
        super().__init__(parent)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(10)

        container = QFrame()
        container.setObjectName("stepperContainer")
        container.setStyleSheet(stepper_container_style())
        container.setFixedHeight(44)

        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)

        self._minus = QPushButton("−")
        self._minus.setFixedSize(44, 44)
        self._minus.setCursor(Qt.PointingHandCursor)
        self._minus.setStyleSheet(stepper_button_style("left"))
        self._minus.clicked.connect(self._decrease)

        sep_l = QFrame()
        sep_l.setFixedWidth(1)
        sep_l.setStyleSheet(f"background: {BORDER};")

        self._spin = QSpinBox()
        self._spin.setRange(minimum, maximum)
        self._spin.setValue(value)
        self._spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self._spin.setAlignment(Qt.AlignCenter)
        self._spin.setMinimumWidth(72)
        self._spin.setStyleSheet(spinbox_center_style())
        self._spin.valueChanged.connect(self.valueChanged.emit)

        sep_r = QFrame()
        sep_r.setFixedWidth(1)
        sep_r.setStyleSheet(f"background: {BORDER};")

        self._plus = QPushButton("+")
        self._plus.setFixedSize(44, 44)
        self._plus.setCursor(Qt.PointingHandCursor)
        self._plus.setStyleSheet(stepper_button_style("right"))
        self._plus.clicked.connect(self._increase)

        row.addWidget(self._minus)
        row.addWidget(sep_l)
        row.addWidget(self._spin, 1)
        row.addWidget(sep_r)
        row.addWidget(self._plus)

        outer.addWidget(container)

        if suffix:
            suf = QLabel(suffix)
            suf.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 14px; font-weight: 500;"
            )
            outer.addWidget(suf)
        outer.addStretch()

    def _decrease(self):
        self._spin.setValue(self._spin.value() - self._spin.singleStep())

    def _increase(self):
        self._spin.setValue(self._spin.value() + self._spin.singleStep())

    def value(self) -> int:
        return self._spin.value()

    def setValue(self, v: int):
        self._spin.setValue(v)

    def setRange(self, lo: int, hi: int):
        self._spin.setRange(lo, hi)

    def setEnabled(self, enabled: bool):
        super().setEnabled(enabled)
        self._minus.setEnabled(enabled)
        self._plus.setEnabled(enabled)
        self._spin.setEnabled(enabled)


class AutoHeightBrowser(QWidget):
    """随文档高度伸缩的 Markdown 浏览器。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from PySide6.QtWidgets import QTextBrowser

        self._browser = QTextBrowser(self)
        self._browser.setOpenExternalLinks(True)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._browser.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: transparent;
                padding: 2px 0;
            }
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._browser)

        doc = self._browser.document()
        doc.contentsChanged.connect(self._sync_height)
        doc.documentLayout().documentSizeChanged.connect(self._sync_height)

    def setHtml(self, html: str):
        self._browser.setHtml(html)
        self._sync_height()

    def _sync_height(self):
        doc = self._browser.document()
        h = int(doc.size().height()) + 20
        self._browser.setFixedHeight(max(h, 60))
        self.setMinimumHeight(self._browser.height())
