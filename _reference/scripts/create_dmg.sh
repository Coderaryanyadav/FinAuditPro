#!/usr/bin/env bash
# scripts/create_dmg.sh - macOS DMG Packager
# Requires `create-dmg` to be installed via brew: brew install create-dmg

set -e

APP_NAME="FinAuditPro"
APP_SOURCE="dist/$APP_NAME.app"
DMG_NAME="FinAuditPro-Installer.dmg"

if [ ! -d "$APP_SOURCE" ]; then
    echo "Error: $APP_SOURCE does not exist. Run build.sh first."
    exit 1
fi

echo "Packaging $APP_NAME for macOS..."

rm -f "$DMG_NAME" "dist/$DMG_NAME"

if command -v create-dmg &> /dev/null; then
    create-dmg \
      --volname "$APP_NAME Installer" \
      --window-pos 200 120 \
      --window-size 800 400 \
      --icon-size 100 \
      --icon "$APP_NAME.app" 200 190 \
      --hide-extension "$APP_NAME.app" \
      --app-drop-link 600 185 \
      "dist/$DMG_NAME" \
      "$APP_SOURCE"
else
    echo "create-dmg CLI tool not found; building DMG using native macOS hdiutil..."
    hdiutil create -volname "$APP_NAME" -srcfolder "$APP_SOURCE" -ov -format UDZO "dist/$DMG_NAME"
fi

echo "DMG creation complete: dist/$DMG_NAME"
