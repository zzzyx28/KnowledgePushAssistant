#!/usr/bin/env bash
# 开源发布前静态检查（不修改代码）
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
FAIL=0

warn() { echo "⚠️  $*"; }
err() { echo "❌ $*"; FAIL=1; }
ok() { echo "✓ $*"; }

echo "=== Knowledge Push Assistant 发布前检查 ==="

# Python 语法
if python3 -m compileall -q src run.py; then
  ok "Python 语法 compileall"
else
  err "Python 语法检查失败"
fi

# 关键导入
if python3 -c "
from src.main import main
from src.ui.tray_notify import TrayNotifier
from src.config import resolve_tray_icon_path, DEFAULT_SETTINGS
from src.storage.migrations import init_database
"; then
  ok "关键模块可导入"
else
  err "模块导入失败（请先 pip install -r requirements.txt）"
fi

# 密钥泄漏
if grep -rE "sk-[a-zA-Z0-9]{20,}" --include='*.py' --include='*.json' --include='*.env*' . 2>/dev/null \
   | grep -v '.md:'; then
  err "发现疑似硬编码 API Key"
else
  ok "未发现硬编码 sk- 密钥"
fi

# 图标资源
if [[ -f assets/icon.icns || -f assets/icon.ico || -f assets/icon.png ]]; then
  ok "应用图标资源存在"
else
  warn "缺少 assets/icon.*，请运行: python scripts/generate_icons.py"
fi

# LICENSE / README
[[ -f LICENSE ]] && ok "LICENSE 存在" || err "缺少 LICENSE"
[[ -f README.md ]] && ok "README.md 存在" || err "缺少 README.md"

# .env 不应入库
if git check-ignore -q .env 2>/dev/null || [[ ! -f .env ]]; then
  ok ".env 已忽略或未提交"
else
  err ".env 可能被提交，请加入 .gitignore"
fi

echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "=== 全部通过 ==="
  exit 0
fi
echo "=== 存在问题，请修复后再发布 ==="
exit 1
