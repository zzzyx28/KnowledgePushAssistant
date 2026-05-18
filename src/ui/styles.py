"""全局样式常量 —— 颜色、字体、圆角、阴影等。"""

# 颜色
BG_MAIN = "#f5f6fa"
BG_CARD = "#ffffff"
BG_SIDEBAR = "#1e1f2b"
BG_TITLEBAR = "#ffffff"
TEXT_PRIMARY = "#1a1d2e"
TEXT_SECONDARY = "#6b7280"
TEXT_SIDEBAR = "#c4c5d0"
TEXT_SIDEBAR_ACTIVE = "#ffffff"
ACCENT = "#6366f1"
ACCENT_HOVER = "#5558e6"
ACCENT_LIGHT = "#eef2ff"
BORDER = "#e5e7eb"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
DANGER = "#ef4444"
USER_BUBBLE = "#6366f1"
AI_BUBBLE = "#ffffff"

# 字体
FONT_FAMILY = "Inter, 'Microsoft YaHei', sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Code', monospace"
FONT_SIZE_XS = "11px"
FONT_SIZE_SM = "12px"
FONT_SIZE_BASE = "13px"
FONT_SIZE_LG = "15px"
FONT_SIZE_XL = "18px"
FONT_SIZE_XXL = "22px"

# 圆角
RADIUS_SM = "6px"
RADIUS_MD = "10px"
RADIUS_LG = "14px"
RADIUS_XL = "18px"

# 通用样式表
GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BASE};
    color: {TEXT_PRIMARY};
}}

QMainWindow {{
    background: {BG_MAIN};
}}

QPushButton {{
    border: none;
    border-radius: {RADIUS_MD};
    padding: 8px 16px;
    background: {ACCENT};
    color: #ffffff;
    font-weight: 500;
}}
QPushButton:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton:pressed {{
    background: #4f46e5;
}}
QPushButton:disabled {{
    background: #c4c5d0;
    color: #9ca3af;
}}

QPushButton[cssClass="secondary"] {{
    background: {BG_CARD};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}
QPushButton[cssClass="secondary"]:hover {{
    background: {ACCENT_LIGHT};
    border-color: {ACCENT};
}}

QPushButton[cssClass="danger"] {{
    background: {DANGER};
}}
QPushButton[cssClass="danger"]:hover {{
    background: #dc2626;
}}

QPushButton[cssClass="icon-btn"] {{
    background: transparent;
    padding: 4px 8px;
    border-radius: {RADIUS_SM};
    color: {TEXT_SECONDARY};
}}
QPushButton[cssClass="icon-btn"]:hover {{
    background: {ACCENT_LIGHT};
    color: {ACCENT};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 8px 12px;
    selection-background-color: {ACCENT_LIGHT};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {ACCENT};
}}

QComboBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 6px 12px;
    min-height: 20px;
}}
QComboBox:hover {{ border-color: {ACCENT}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #d1d5db;
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: #9ca3af; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: #d1d5db;
    border-radius: 3px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

QLabel[cssClass="page-title"] {{
    font-size: {FONT_SIZE_XXL};
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel[cssClass="page-desc"] {{
    font-size: {FONT_SIZE_BASE};
    color: {TEXT_SECONDARY};
    margin-bottom: 16px;
}}

QLabel[cssClass="stat-value"] {{
    font-size: 28px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel[cssClass="stat-label"] {{
    font-size: {FONT_SIZE_SM};
    color: {TEXT_SECONDARY};
}}

QFrame[cssClass="card"] {{
    background: {BG_CARD};
    border-radius: {RADIUS_LG};
    border: 1px solid {BORDER};
}}

QFrame[cssClass="stat-card"] {{
    background: {BG_CARD};
    border-radius: {RADIUS_LG};
    border: 1px solid {BORDER};
    padding: 16px;
}}

QCheckBox {{
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 2px solid {BORDER};
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

QSlider::groove:horizontal {{
    height: 6px;
    background: {BORDER};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    background: {ACCENT};
    border-radius: 7px;
    margin: -4px 0;
}}
"""
