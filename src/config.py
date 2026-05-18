"""配置管理：应用路径、默认设置键名等。"""

import os
import sys
from pathlib import Path

APPDIR = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "KnowledgePushAssistant"

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

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
    "system_prompt": "",  # 空则使用 defaults.py 中的默认值
    "window_x": 200,
    "window_y": 100,
    "window_width": 900,
    "window_height": 600,
}
