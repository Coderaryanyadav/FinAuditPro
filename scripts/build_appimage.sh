#!/usr/bin/env bash
# scripts/build_appimage.sh - Linux AppImage Packager
# Requires `appimagetool` to be in PATH

set -e

APP_NAME="FinAuditPro"
APP_DIR="dist/$APP_NAME.AppDir"

if [ ! -d "dist/$APP_NAME" ]; then
    echo "Error: dist/$APP_NAME does not exist. Run build.sh first."
    exit 1
fi

echo "Packaging $APP_NAME for Linux (AppImage)..."

rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"

# Copy binary and assets
cp -r "dist/$APP_NAME/"* "$APP_DIR/"

# Create AppRun
cat << 'EOF' > "$APP_DIR/AppRun"
#!/bin/sh
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/FinAuditPro" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Create .desktop file
cat << EOF > "$APP_DIR/$APP_NAME.desktop"
[Desktop Entry]
Name=$APP_NAME
Exec=FinAuditPro
Icon=FinAuditPro
Type=Application
Categories=Office;Finance;
EOF

# Copy Icon
if [ -f "assets/icon.png" ]; then
    cp "assets/icon.png" "$APP_DIR/FinAuditPro.png"
else
    touch "$APP_DIR/FinAuditPro.png"
fi

# Build AppImage
if command -v appimagetool &> /dev/null; then
    appimagetool "$APP_DIR" "dist/$APP_NAME-x86_64.AppImage"
    echo "AppImage creation complete: dist/$APP_NAME-x86_64.AppImage"
else
    echo "Error: appimagetool not found. Please install it from https://github.com/AppImage/AppImageKit"
    exit 1
fi
