"""全局样式 —— Apple Human Interface Guidelines 设计令牌。"""

# ── 色彩（macOS 浅色语义）────────────────────────────────────────
BG_MAIN = "#F0F0F5"
BG_CARD = "#FFFFFF"
BG_SIDEBAR = "rgba(242, 242, 247, 0.75)"
BG_TITLEBAR = "rgba(250, 250, 252, 0.78)"
BG_FILL = "#E8E8ED"
BG_HOVER = "#F9F9FB"
BG_ELEVATED = "#FFFFFF"
BG_INPUT = "#FFFFFF"
BG_GROUPED = "#FFFFFF"
BG_SUBTLE = "#FAFAFA"
BG_STICKY = "rgba(245, 245, 247, 0.85)"
BG_GLASS = "rgba(255, 255, 255, 0.62)"
BG_GLASS_STRONG = "rgba(255, 255, 255, 0.80)"
BG_GLASS_CARD = "rgba(255, 255, 255, 0.56)"

TEXT_PRIMARY = "#1D1D1F"
TEXT_SECONDARY = "#6E6E73"
TEXT_TERTIARY = "#AEAEB2"
TEXT_QUATERNARY = "#C7C7CC"
TEXT_SIDEBAR = "#1D1D1F"
TEXT_SIDEBAR_ACTIVE = "#007AFF"

ACCENT = "#007AFF"
ACCENT_HOVER = "#0077ED"
ACCENT_PRESSED = "#006ADB"
ACCENT_LIGHT = "rgba(0, 122, 255, 0.10)"
ACCENT_FILL = "#E8F2FF"

BORDER = "#DDDDE2"
BORDER_LIGHT = "#EBEBF0"
SEPARATOR = "#D9D9DE"
SEPARATOR_OPAQUE = "#E8E8ED"
SEPARATOR_SUBTLE = "#F2F2F7"

SUCCESS = "#34C759"
WARNING = "#FF9500"
DANGER = "#FF3B30"

USER_BUBBLE = "#007AFF"
AI_BUBBLE = "#F2F2F7"

BORDER_GLASS = "rgba(0, 0, 0, 0.06)"
BORDER_GLASS_STRONG = "rgba(0, 0, 0, 0.10)"

SHADOW_SM = "0 1px 3px rgba(0, 0, 0, 0.04)"
SHADOW_MD = "0 2px 12px rgba(0, 0, 0, 0.06)"

# ── 字体（Qt 无法解析 -apple-system 等 Web 别名，须用系统已注册族名）──
FONT_FAMILY = (
    ".AppleSystemUIFont, 'Helvetica Neue', 'PingFang SC', sans-serif"
)
FONT_MONO = "'Menlo', 'Monaco', 'Consolas', monospace"
FONT_SIZE_XS = "11px"
FONT_SIZE_SM = "12px"
FONT_SIZE_BASE = "13px"
FONT_SIZE_LG = "15px"
FONT_SIZE_XL = "17px"
FONT_SIZE_XXL = "22px"
FONT_SIZE_TITLE = "28px"
FONT_SIZE_HERO = "34px"

# ── 圆角 & 间距 ───────────────────────────────────────────────────
RADIUS_XS = "4px"
RADIUS_SM = "7px"
RADIUS_MD = "10px"
RADIUS_LG = "12px"
RADIUS_XL = "16px"
RADIUS_PILL = "20px"
RADIUS_SECTION = "14px"
RADIUS_WINDOW = "10px"

PAGE_MARGIN_H = 40
PAGE_MARGIN_V = 28
CONTENT_MAX_WIDTH = 720

SIDEBAR_WIDTH = 220


# ── 组件样式工厂 ──────────────────────────────────────────────────

def primary_button_style(height: int = 36, large: bool = False) -> str:
    fs = "15px" if large else "13px"
    return f"""
        QPushButton {{
            background: {ACCENT};
            color: #FFFFFF;
            border: none;
            border-radius: {RADIUS_MD};
            padding: 0 20px;
            min-height: {height}px;
            font-size: {fs};
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {ACCENT_HOVER}; }}
        QPushButton:pressed {{ background: {ACCENT_PRESSED}; }}
        QPushButton:disabled {{
            background: {BORDER_LIGHT};
            color: {TEXT_TERTIARY};
        }}
    """


def secondary_button_style(height: int = 32) -> str:
    return f"""
        QPushButton {{
            background: {BG_FILL};
            color: {TEXT_PRIMARY};
            border: none;
            border-radius: {RADIUS_SM};
            padding: 0 16px;
            min-height: {height}px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background: #DCDCE0; }}
        QPushButton:pressed {{ background: #C7C7CC; }}
    """


def ghost_button_style() -> str:
    return f"""
        QPushButton {{
            background: transparent;
            color: {ACCENT};
            border: none;
            border-radius: {RADIUS_SM};
            padding: 6px 10px;
            font-size: 13px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background: {ACCENT_FILL}; }}
    """


def card_style(radius: str = RADIUS_LG) -> str:
    return f"""
        background: {BG_CARD};
        border: 1px solid {BORDER_LIGHT};
        border-radius: {radius};
    """


def scroll_area_style() -> str:
    return f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollArea > QWidget > QWidget {{
            background: transparent;
        }}
        {scroll_bar_style()}
    """


def scroll_bar_style() -> str:
    """macOS 风格细滚动条 — 悬停时显现。"""
    return f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 4px 2px 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.18);
            border-radius: 4px;
            min-height: 32px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.28);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
            border: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0 4px 2px 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: rgba(0, 0, 0, 0.18);
            border-radius: 4px;
            min-width: 32px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: rgba(0, 0, 0, 0.28);
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """


def spinbox_center_style() -> str:
    """步进器中间数值区。"""
    return f"""
        QSpinBox {{
            background: {BG_CARD};
            border: none;
            padding: 0 8px;
            font-size: 17px;
            font-weight: 600;
            color: {TEXT_PRIMARY};
            min-height: 44px;
        }}
        QSpinBox:focus {{
            background: {BG_CARD};
        }}
    """


def stepper_button_style(side: str = "left") -> str:
    radius_left = f"{RADIUS_MD} 0 0 {RADIUS_MD}"
    radius_right = f"0 {RADIUS_MD} {RADIUS_MD} 0"
    radius_l = radius_left if side == "left" else radius_right
    return f"""
        QPushButton {{
            background: {BG_FILL};
            border: none;
            border-radius: {radius_l};
            color: {ACCENT};
            font-size: 20px;
            font-weight: 400;
        }}
        QPushButton:hover {{
            background: #DCDCE0;
        }}
        QPushButton:pressed {{
            background: #C7C7CC;
        }}
        QPushButton:disabled {{
            color: {TEXT_QUATERNARY};
            background: #F5F5F7;
        }}
    """


def stepper_container_style() -> str:
    return f"""
        QFrame#stepperContainer {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_MD};
        }}
    """


def time_edit_style() -> str:
    return f"""
        QTimeEdit {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_MD};
            padding: 10px 14px;
            min-height: 22px;
            font-size: 15px;
            font-weight: 500;
            color: {TEXT_PRIMARY};
        }}
        QTimeEdit:focus {{
            border: 2px solid {ACCENT};
            padding: 9px 13px;
        }}
        QTimeEdit::up-button, QTimeEdit::down-button {{
            width: 22px;
            border: none;
            background: transparent;
        }}
        QTimeEdit::up-button:hover, QTimeEdit::down-button:hover {{
            background: {BG_FILL};
            border-radius: 4px;
        }}
    """


def tag_style(accent: bool = True) -> str:
    if accent:
        return f"""
            background: {ACCENT_FILL};
            color: {ACCENT};
            border-radius: 6px;
            padding: 3px 9px;
            font-size: 11px;
            font-weight: 600;
        """
    return f"""
        background: {BG_FILL};
        color: {TEXT_SECONDARY};
        border-radius: 6px;
        padding: 3px 9px;
        font-size: 11px;
        font-weight: 500;
    """


def search_field_style() -> str:
    return f"""
        QLineEdit {{
            background: {BG_FILL};
            border: none;
            border-radius: {RADIUS_PILL};
            padding: 0 16px;
            font-size: 14px;
            color: {TEXT_PRIMARY};
            selection-background-color: {ACCENT_FILL};
        }}
        QLineEdit:focus {{
            background: {BG_CARD};
            border: 2px solid {ACCENT};
            padding: 0 14px;
        }}
    """


def combo_field_style() -> str:
    return f"""
        QComboBox {{
            background: {BG_CARD};
            border: 1px solid {BORDER};
            border-radius: {RADIUS_MD};
            padding: 8px 12px;
            min-height: 22px;
            font-size: 14px;
        }}
        QComboBox:hover {{ border-color: {TEXT_TERTIARY}; }}
        QComboBox:focus {{ border: 2px solid {ACCENT}; padding: 7px 11px; }}
        QComboBox::drop-down {{ border: none; width: 28px; }}
    """


def settings_group_style() -> str:
    """macOS 设置式白底圆角分组容器。"""
    return f"""
        QFrame#settingsGroup {{
            background: {BG_CARD};
            border: 1px solid {BORDER_LIGHT};
            border-radius: {RADIUS_SECTION};
        }}
    """


def settings_row_style(last: bool = False) -> str:
    """分组内单行样式。"""
    if last:
        return f"""
            QWidget#settingsRow {{
                background: {BG_CARD};
                border: none;
                border-radius: 0 0 {RADIUS_SECTION} {RADIUS_SECTION};
                min-height: 44px;
            }}
        """
    return f"""
        QWidget#settingsRow {{
            background: {BG_CARD};
            border: none;
            border-bottom: 1px solid {SEPARATOR_SUBTLE};
            min-height: 44px;
        }}
    """


def section_heading_style() -> str:
    """分组标题。"""
    return f"""
        QLabel {{
            font-size: 11px;
            font-weight: 600;
            color: {TEXT_SECONDARY};
            text-transform: uppercase;
            letter-spacing: 0.4px;
            padding: 0 4px;
        }}
    """


def slim_stat_style() -> str:
    """紧凑型统计数字卡片 —— 毛玻璃效果。"""
    return f"""
        QFrame#slimStat {{
            background: {BG_GLASS_CARD};
            border: 1px solid {BORDER_GLASS};
            border-radius: {RADIUS_MD};
        }}
    """


def glass_card_style() -> str:
    """毛玻璃卡片 —— 半透明背景 + 极淡边框。"""
    return f"""
        QFrame#glassCard {{
            background: {BG_GLASS};
            border: 1px solid {BORDER_GLASS};
            border-radius: {RADIUS_LG};
        }}
    """


GLOBAL_STYLESHEET = f"""
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: {FONT_SIZE_BASE};
    color: {TEXT_PRIMARY};
}}

QMainWindow {{
    background: {BG_MAIN};
}}

QToolTip {{
    background: rgba(29, 29, 31, 0.92);
    color: #FFFFFF;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

QPushButton {{
    border: none;
    border-radius: {RADIUS_MD};
    padding: 8px 18px;
    background: {ACCENT};
    color: #FFFFFF;
    font-weight: 600;
    font-size: {FONT_SIZE_BASE};
}}
QPushButton:hover {{ background: {ACCENT_HOVER}; }}
QPushButton:pressed {{ background: {ACCENT_PRESSED}; }}
QPushButton:disabled {{
    background: {BORDER_LIGHT};
    color: {TEXT_TERTIARY};
}}

QPushButton[cssClass="secondary"] {{
    background: {BG_FILL};
    color: {TEXT_PRIMARY};
    font-weight: 500;
}}
QPushButton[cssClass="secondary"]:hover {{ background: #DCDCE0; }}
QPushButton[cssClass="secondary"]:pressed {{ background: #C7C7CC; }}

QPushButton[cssClass="danger"] {{
    background: {DANGER};
    color: #FFFFFF;
}}
QPushButton[cssClass="danger"]:hover {{ background: #E6352B; }}

QPushButton[cssClass="ghost"] {{
    background: transparent;
    color: {ACCENT};
    font-weight: 600;
    padding: 6px 10px;
}}
QPushButton[cssClass="ghost"]:hover {{ background: {ACCENT_FILL}; }}

QPushButton[cssClass="icon-btn"] {{
    background: transparent;
    color: {TEXT_SECONDARY};
    padding: 6px 10px;
    border-radius: {RADIUS_SM};
    font-weight: 400;
}}
QPushButton[cssClass="icon-btn"]:hover {{
    background: {BG_FILL};
    color: {TEXT_PRIMARY};
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 10px 12px;
    selection-background-color: {ACCENT_FILL};
    selection-color: {TEXT_PRIMARY};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border: 2px solid {ACCENT};
    padding: 9px 11px;
}}

QComboBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 8px 12px;
    min-height: 22px;
}}
QComboBox:hover {{ border-color: {TEXT_TERTIARY}; }}
QComboBox:focus {{ border: 2px solid {ACCENT}; padding: 7px 11px; }}
QComboBox::drop-down {{ border: none; width: 28px; }}

{scroll_bar_style()}

QLabel[cssClass="page-title"] {{
    font-size: {FONT_SIZE_TITLE};
    font-weight: 700;
    color: {TEXT_PRIMARY};
    letter-spacing: -0.6px;
}}

QLabel[cssClass="page-desc"] {{
    font-size: {FONT_SIZE_LG};
    color: {TEXT_SECONDARY};
}}

QLabel[cssClass="section-title"] {{
    font-size: {FONT_SIZE_XL};
    font-weight: 600;
    color: {TEXT_PRIMARY};
    letter-spacing: -0.2px;
}}

QLabel[cssClass="greeting"] {{
    font-size: 32px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
    letter-spacing: -0.8px;
}}

QLabel[cssClass="greeting-sub"] {{
    font-size: {FONT_SIZE_LG};
    color: {TEXT_SECONDARY};
    font-weight: 450;
}}

QLabel[cssClass="stat-value-sm"] {{
    font-size: 20px;
    font-weight: 700;
    color: {TEXT_PRIMARY};
}}

QLabel[cssClass="stat-label-sm"] {{
    font-size: 11px;
    color: {TEXT_SECONDARY};
    font-weight: 500;
}}

QLabel[cssClass="empty-hint"] {{
    font-size: {FONT_SIZE_LG};
    color: {TEXT_TERTIARY};
    line-height: 1.6;
}}

QFrame[cssClass="card"] {{
    background: {BG_CARD};
    border-radius: {RADIUS_LG};
    border: 1px solid {BORDER_LIGHT};
}}

QFrame[cssClass="stat-card"] {{
    background: {BG_CARD};
    border-radius: {RADIUS_LG};
    border: 1px solid {BORDER_LIGHT};
}}

QFrame[cssClass="settings-group"] {{
    background: {BG_GROUPED};
    border-radius: {RADIUS_LG};
    border: 1px solid {BORDER_LIGHT};
}}

QCheckBox {{
    spacing: 10px;
    font-size: {FONT_SIZE_BASE};
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1.5px solid {BORDER};
    background: {BG_CARD};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}

QSpinBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 8px 12px;
    min-height: 24px;
    font-size: 14px;
}}
QSpinBox:focus {{ border: 2px solid {ACCENT}; padding: 7px 11px; }}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 0;
    height: 0;
    border: none;
}}

QTimeEdit {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    padding: 10px 14px;
    min-height: 24px;
    font-size: 14px;
}}
QTimeEdit:focus {{ border: 2px solid {ACCENT}; padding: 9px 13px; }}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER_LIGHT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 20px;
    height: 20px;
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: {RADIUS_MD};
    margin: -8px 0;
}}

QDialog {{
    background: {BG_MAIN};
}}

QMessageBox {{
    background: {BG_CARD};
}}
"""
