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
    run.py

echo === 打包完成 ===
echo 输出: %DIST_DIR%\%APP_NAME%.exe

REM 可选：使用 NSIS 或 Inno Setup 创建安装程序
REM 此处仅生成单个 exe，如需安装包请配合 NSIS/Inno Setup
endlocal
