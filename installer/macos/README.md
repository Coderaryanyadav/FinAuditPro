# macOS Distribution & DMG Installer Packaging

To package FinAuditPro as a standalone drag-and-drop `.dmg` bundle for macOS (Apple Silicon / Intel):

1. **Build Standalone App via PyInstaller**:
   ```bash
   pyinstaller finauditpro.spec
   ```

2. **Code Sign the `.app` Bundle**:
   ```bash
   ./scripts/packaging/sign_and_notarize.sh "Developer ID Application: Your Firm (TEAMID)"
   ```

3. **Generate Disk Image (`.dmg`)**:
   ```bash
   create-dmg \
     --volname "FinAuditPro Installer" \
     --window-pos 200 120 \
     --window-size 600 400 \
     --icon-size 100 \
     --icon "finauditpro.app" 175 120 \
     --hide-extension "finauditpro.app" \
     --app-drop-link 425 120 \
     "dist/FinAuditPro-0.1.0-arm64.dmg" \
     "dist/finauditpro.app"
   ```
