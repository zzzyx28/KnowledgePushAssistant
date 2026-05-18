"""配置管理：应用路径、默认设置键名等。"""

import os
import sys
from pathlib import Path

APPDIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "KnowledgePushAssistant"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = BASE_DIR / "assets"


def resolve_tray_icon_path() -> Path | None:
    """托盘图标路径（开发/打包环境均可用）。"""
    candidates = [ASSETS_DIR / "icon.png"]
    if sys.platform == "darwin":
        candidates.append(ASSETS_DIR / "icon.icns")
    elif sys.platform == "win32":
        candidates.append(ASSETS_DIR / "icon.ico")
    for path in candidates:
        if path.is_file():
            return path
    return None

DB_PATH = APPDIR / "knowledge_push.db"
SETTINGS_PATH = APPDIR / "settings.json"

DEFAULT_SETTINGS = {
    "push_enabled": True,
    "push_interval_minutes": 60,
    "push_start_hour": 8,
    "push_end_hour": 22,
    "model_name": "deepseek-chat",
    "model_base_url": "https://api.deepseek.com",
    "model_api_key": "",
    "user_preference_prompt": "",
    "system_prompt": "",  # 空则使用 defaults.py 中的默认值
    "window_x": 200,
    "window_y": 100,
    "window_width": 900,
    "window_height": 600,
}
