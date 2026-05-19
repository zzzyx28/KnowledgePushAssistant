#!/usr/bin/env bash
set -euo pipefail

# Build Knowledge Push Assistant for current platform.
# Outputs: macOS .dmg or Windows .exe/.msi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/desktop"
cd "$PROJECT_DIR"

VERSION=$(node -p "require('./package.json').version")
echo "Building KPA v${VERSION}"

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm ci --legacy-peer-deps
fi

if ! command -v cargo &>/dev/null; then
  if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
  else
    echo "Rust not found. Install from https://rustup.rs"
    exit 1
  fi
fi

echo "Compiling..."
npm run tauri build

BUNDLE_DIR="src-tauri/target/release/bundle"
ARCH=$(uname -m)
TAURI_ARCH="$ARCH"
[ "$ARCH" = "arm64" ] && TAURI_ARCH="aarch64"
[ "$ARCH" = "x86_64" ] && TAURI_ARCH="x64"

DIST_DIR="$SCRIPT_DIR/../dist"
mkdir -p "$DIST_DIR"

case "$(uname -s)" in
  Darwin)
    DMG_SRC="$BUNDLE_DIR/dmg/Knowledge Push Assistant_${VERSION}_${TAURI_ARCH}.dmg"
    if [ -f "$DMG_SRC" ]; then
      cp "$DMG_SRC" "$DIST_DIR/KPA-v${VERSION}-macos-${ARCH}.dmg"
      echo "Done: $DIST_DIR/KPA-v${VERSION}-macos-${ARCH}.dmg"
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*)
    MSI_SRC=$(ls "$BUNDLE_DIR/msi/"*.msi 2>/dev/null | head -1)
    EXE_SRC=$(ls "$BUNDLE_DIR/nsis/"*.exe 2>/dev/null | head -1)
    [ -f "$MSI_SRC" ] && cp "$MSI_SRC" "$DIST_DIR/KPA-v${VERSION}-windows-${ARCH}.msi" && echo "Done: .msi"
    [ -f "$EXE_SRC" ] && cp "$EXE_SRC" "$DIST_DIR/KPA-v${VERSION}-windows-${ARCH}.exe" && echo "Done: .exe"
    ;;
  *)
    echo "Unsupported platform. CI builds macOS (.dmg) and Windows (.exe)."
    exit 1
    ;;
esac
