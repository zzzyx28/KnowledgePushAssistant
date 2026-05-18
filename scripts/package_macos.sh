#!/usr/bin/env bash
# ============================================================
# Knowledge Push Assistant — macOS DMG 打包脚本
# 用法: bash scripts/package_macos.sh
# 输出: dist/KnowledgePushAssistant.dmg
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

APP_NAME="KnowledgePushAssistant"
DIST_DIR="dist"
BUILD_DIR="build"
DMG_NAME="${APP_NAME}.dmg"
APP_BUNDLE="${APP_NAME}.app"

echo "=== 安装依赖 ==="
pip install -r requirements.txt pyinstaller

echo "=== PyInstaller 打包 ==="
pyinstaller \
    --name="${APP_NAME}" \
    --windowed \
    --onedir \
    --icon=assets/icon.icns \
    --add-data="src:src" \
    --add-data="assets:assets" \
    --hidden-import="sqlalchemy.ext.declarative" \
    --osx-bundle-identifier="com.knowledgepush.assistant" \
    --clean \
    --noconfirm \
    run.py

echo "=== 创建 DMG ==="
APP_PATH="${DIST_DIR}/${APP_BUNDLE}"
if [ -d "${APP_PATH}" ]; then
    # 创建 DMG
    DMG_PATH="${DIST_DIR}/${DMG_NAME}"
    rm -f "${DMG_PATH}"

    # 创建临时目录用于 DMG 布局
    TMP_DMG_DIR="${BUILD_DIR}/dmg_layout"
    rm -rf "${TMP_DMG_DIR}"
    mkdir -p "${TMP_DMG_DIR}"
    cp -R "${APP_PATH}" "${TMP_DMG_DIR}/"
    ln -s /Applications "${TMP_DMG_DIR}/Applications"

    hdiutil create \
        -volname "${APP_NAME}" \
        -srcfolder "${TMP_DMG_DIR}" \
        -ov -format UDZO \
        "${DMG_PATH}"

    rm -rf "${TMP_DMG_DIR}"
    echo "=== DMG 已生成: ${DMG_PATH} ==="
else
    echo "错误: .app bundle 未找到: ${APP_PATH}"
    exit 1
fi
