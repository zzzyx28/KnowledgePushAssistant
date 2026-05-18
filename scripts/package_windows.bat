@echo off
REM ============================================================
REM Knowledge Push Assistant — Windows 打包脚本
REM 用法: scripts\package_windows.bat
REM 输出: dist\KnowledgePushAssistant.exe
REM ============================================================
setlocal enabledelayedexpansion

set APP_NAME=KnowledgePushAssistant
set DIST_DIR=dist
set BUILD_DIR=build

echo === 安装依赖 ===
pip install -r requirements.txt pyinstaller
pip uninstall -y PySide6 2>nul || echo PySide6 not installed (OK)

echo === PyInstaller 打包 ===
pyinstaller ^
    --name="%APP_NAME%" ^
    --windowed ^
    --onefile ^
    --icon=assets\icon.ico ^
    --add-data="src;src" ^
    --add-data="assets;assets" ^
    --hidden-import="sqlalchemy.ext.declarative" ^
    --clean ^
    --noconfirm ^
    --exclude-module="PySide6.QtWebEngine" ^
    --exclude-module="PySide6.QtWebEngineCore" ^
    --exclude-module="PySide6.QtWebEngineWidgets" ^
    --exclude-module="PySide6.QtWebChannel" ^
    --exclude-module="PySide6.QtQuick" ^
    --exclude-module="PySide6.QtQuickWidgets" ^
    --exclude-module="PySide6.QtQml" ^
    --exclude-module="PySide6.QtQmlModels" ^
    --exclude-module="PySide6.QtMultimedia" ^
    --exclude-module="PySide6.QtMultimediaWidgets" ^
    --exclude-module="PySide6.Qt3DAnimation" ^
    --exclude-module="PySide6.Qt3DCore" ^
    --exclude-module="PySide6.Qt3DExtras" ^
    --exclude-module="PySide6.Qt3DInput" ^
    --exclude-module="PySide6.Qt3DLogic" ^
    --exclude-module="PySide6.Qt3DRender" ^
    --exclude-module="PySide6.QtCharts" ^
    --exclude-module="PySide6.QtDataVisualization" ^
    --exclude-module="PySide6.QtLocation" ^
    --exclude-module="PySide6.QtPositioning" ^
    --exclude-module="PySide6.QtSensors" ^
    --exclude-module="PySide6.QtTextToSpeech" ^
    --exclude-module="PySide6.QtNfc" ^
    --exclude-module="PySide6.QtBluetooth" ^
    --exclude-module="PySide6.QtRemoteObjects" ^
    --exclude-module="PySide6.QtDesigner" ^
    --exclude-module="PySide6.QtSerialPort" ^
    run.py

echo === 打包完成 ===
echo 输出: %DIST_DIR%\%APP_NAME%.exe

REM 可选：使用 NSIS 或 Inno Setup 创建安装程序
REM 此处仅生成单个 exe，如需安装包请配合 NSIS/Inno Setup
endlocal
