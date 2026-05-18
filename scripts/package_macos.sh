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
pip uninstall -y PySide6 2>/dev/null || true

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
    --exclude-module="PySide6.QtWebEngine" \
    --exclude-module="PySide6.QtWebEngineCore" \
    --exclude-module="PySide6.QtWebEngineWidgets" \
    --exclude-module="PySide6.QtWebChannel" \
    --exclude-module="PySide6.QtQuick" \
    --exclude-module="PySide6.QtQuickWidgets" \
    --exclude-module="PySide6.QtQml" \
    --exclude-module="PySide6.QtQmlModels" \
    --exclude-module="PySide6.QtMultimedia" \
    --exclude-module="PySide6.QtMultimediaWidgets" \
    --exclude-module="PySide6.Qt3DAnimation" \
    --exclude-module="PySide6.Qt3DCore" \
    --exclude-module="PySide6.Qt3DExtras" \
    --exclude-module="PySide6.Qt3DInput" \
    --exclude-module="PySide6.Qt3DLogic" \
    --exclude-module="PySide6.Qt3DRender" \
    --exclude-module="PySide6.QtCharts" \
    --exclude-module="PySide6.QtDataVisualization" \
    --exclude-module="PySide6.QtLocation" \
    --exclude-module="PySide6.QtPositioning" \
    --exclude-module="PySide6.QtSensors" \
    --exclude-module="PySide6.QtTextToSpeech" \
    --exclude-module="PySide6.QtNfc" \
    --exclude-module="PySide6.QtBluetooth" \
    --exclude-module="PySide6.QtRemoteObjects" \
    --exclude-module="PySide6.QtDesigner" \
    --exclude-module="PySide6.QtSerialPort" \
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
