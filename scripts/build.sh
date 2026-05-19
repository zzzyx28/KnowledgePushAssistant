#!/usr/bin/env bash
set -euo pipefail

# ── Build & Package Knowledge Push Assistant ──
# Produces cleanly-named artifacts for the current platform.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/desktop"
cd "$PROJECT_DIR"

# ── Detect version ──
VERSION=$(node -p "require('./package.json').version")
echo "📦 Building KPA v${VERSION}"

# ── Ensure dependencies ──
if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm ci
fi

# ── Ensure Rust toolchain ──
if ! command -v cargo &>/dev/null; then
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  else
    echo "❌ Rust not found. Install from https://rustup.rs"
    exit 1
  fi
fi

# ── Build Tauri ──
echo "Compiling..."
npm run tauri build

# ── Rename artifacts ──
BUNDLE_DIR="src-tauri/target/release/bundle"
ARCH=$(uname -m)
# Tauri uses aarch64, uname -m gives arm64 on Apple Silicon
TAURI_ARCH="$ARCH"
[ "$ARCH" = "arm64" ] && TAURI_ARCH="aarch64"
[ "$ARCH" = "x86_64" ] && TAURI_ARCH="x64"

case "$(uname -s)" in
  Darwin)
    OS="macos"
    DMG_SRC="$BUNDLE_DIR/dmg/Knowledge Push Assistant_${VERSION}_${TAURI_ARCH}.dmg"
    DMG_DST="$SCRIPT_DIR/../dist/KPA-v${VERSION}-macos-${ARCH}.dmg"
    mkdir -p "$SCRIPT_DIR/../dist"
    if [ -f "$DMG_SRC" ]; then
      cp "$DMG_SRC" "$DMG_DST"
      echo "✅ $DMG_DST"
    fi
    # Also copy .app
    APP_SRC="$BUNDLE_DIR/macos/Knowledge Push Assistant.app"
    if [ -d "$APP_SRC" ]; then
      cp -R "$APP_SRC" "$SCRIPT_DIR/../dist/KPA-v${VERSION}-macos-${ARCH}.app"
      echo "✅ dist/KPA-v${VERSION}-macos-${ARCH}.app"
    fi
    ;;
  Linux)
    OS="linux"
    DEB_SRC="$BUNDLE_DIR/deb/knowledge-push-assistant-desktop_${VERSION}_${ARCH}.deb"
    APPIMAGE_SRC="$BUNDLE_DIR/appimage/knowledge-push-assistant-desktop_${VERSION}_${ARCH}.AppImage"
    mkdir -p "$SCRIPT_DIR/../dist"
    [ -f "$DEB_SRC" ] && cp "$DEB_SRC" "$SCRIPT_DIR/../dist/KPA-v${VERSION}-linux-${ARCH}.deb"  && echo "✅ .deb"
    [ -f "$APPIMAGE_SRC" ] && cp "$APPIMAGE_SRC" "$SCRIPT_DIR/../dist/KPA-v${VERSION}-linux-${ARCH}.AppImage" && echo "✅ .AppImage"
    ;;
  *)
    echo "❌ Unknown OS"
    exit 1
    ;;
esac

echo "Done. Artifacts in dist/"
