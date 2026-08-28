#!/usr/bin/env python3
"""Build and package FinAuditPro for macOS (Application Bundle & Polished DMG)."""

import os
import platform
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def run_command(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    """Run shell command with error checking and output streaming."""
    print(f"  → Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, env=env or os.environ.copy(), check=True)


def build_macos_app() -> Path:
    """Build macOS .app bundle using PyInstaller."""
    from finauditpro.version import APP_NAME, __version__

    print("=" * 60)
    print(f" BUILDING {APP_NAME} v{__version__} FOR macOS ({platform.machine()})")
    print("=" * 60)

    # 1. Ensure icons are generated
    icons_dir = PROJECT_ROOT / "src" / "finauditpro" / "assets" / "icons"
    if not (icons_dir / "FinAuditPro.icns").exists():
        print("Icons missing. Generating application icons...")
        from scripts.packaging.generate_icons import generate_all_icons
        generate_all_icons(icons_dir)

    # 2. Run clean
    from scripts.packaging.clean import clean_build_artifacts
    clean_build_artifacts()

    # 3. Pre-build checks
    from scripts.packaging.verify_release import run_pre_build_checks
    if not run_pre_build_checks():
        print("[FAIL] Pre-build checks failed. Aborting build.")
        sys.exit(1)

    # 4. Invoke PyInstaller
    spec_path = PROJECT_ROOT / "finauditpro.spec"
    print(f"\n[BUILD] Executing PyInstaller with spec: {spec_path.name}...")
    run_command([sys.executable, "-m", "PyInstaller", str(spec_path), "--noconfirm"])

    app_path = PROJECT_ROOT / "dist" / "FinAuditPro.app"
    if not app_path.exists():
        print(f"[FAIL] ERROR: Expected application bundle not found at: {app_path}")
        sys.exit(1)

    print(f"[OK] PyInstaller bundle created successfully: {app_path}")

    # Smoke test the built binary in an isolated temporary data dir
    print("\n[TEST] Executing runtime smoke test on packaged binary...")
    binary_path = app_path / "Contents" / "MacOS" / "FinAuditPro"
    test_env = os.environ.copy()
    with tempfile.TemporaryDirectory() as tmp_data_dir:
        test_env["FINAUDITPRO_DATA_DIR"] = tmp_data_dir
        res = subprocess.run([str(binary_path), "--headless"], env=test_env, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[FAIL] Runtime smoke test failed with exit code {res.returncode}:")
            print(res.stderr or res.stdout)
            sys.exit(1)
        print(f"[OK] Runtime smoke test passed: {res.stdout.strip()}")

    return app_path


def sign_and_notarize(app_path: Path) -> None:
    """Optional code signing and Apple notarization if credentials exist in environment."""
    signing_id = os.environ.get("APPLE_SIGNING_IDENTITY")
    keychain_profile = os.environ.get("KEYCHAIN_PROFILE")
    apple_id = os.environ.get("APPLE_ID")
    team_id = os.environ.get("APPLE_TEAM_ID")
    password = os.environ.get("APPLE_PASSWORD")

    if not signing_id:
        print("\n[SEC] [Code Signing] No APPLE_SIGNING_IDENTITY found in environment.")
        print("   Proceeding with ad-hoc signing for local execution.")
        try:
            run_command(["codesign", "--force", "--deep", "--sign", "-", str(app_path)])
            print("   [OK] Ad-hoc codesign applied.")
        except Exception as e:
            print(f"   [WARN] Ad-hoc codesign skipped: {e}")
        return

    print(f"\n[SEC] [Code Signing] Signing bundle with Developer ID: '{signing_id}'...")
    run_command([
        "codesign",
        "--deep",
        "--force",
        "--options", "runtime",
        "--timestamp",
        "--sign", signing_id,
        str(app_path)
    ])
    print("[OK] Code signing complete. Verifying...")
    run_command(["codesign", "--verify", "--deep", "--strict", "--verbose=2", str(app_path)])


def create_dmg(app_path: Path) -> Path:
    """Create polished standalone macOS DMG with Applications link."""
    from finauditpro.version import APP_NAME, __version__

    arch = platform.machine()
    dmg_name = f"{APP_NAME}-{__version__}-macOS-{arch}.dmg"
    dmg_path = PROJECT_ROOT / "dist" / dmg_name

    if dmg_path.exists():
        dmg_path.unlink()

    print(f"\n[PACKAGE] Creating macOS Disk Image (DMG): {dmg_name}...")

    # Method 1: Try dmgbuild if available
    use_dmgbuild = False
    try:
        import dmgbuild  # noqa: F401
        use_dmgbuild = True
    except ImportError:
        use_dmgbuild = False

    if use_dmgbuild:
        print("  Using dmgbuild for native drag-and-drop presentation...")
        icon_path = PROJECT_ROOT / "src" / "finauditpro" / "assets" / "icons" / "FinAuditPro.icns"

        app_size_mb = int(sum(f.stat().st_size for f in app_path.rglob("*") if f.is_file()) / (1024 * 1024)) + 400
        dmg_settings = f"""
filename = '{dmg_path}'
volume_name = '{APP_NAME}'
format = 'UDZO'
size = '{app_size_mb}M'
files = ['{app_path}']
symlinks = {{'Applications': '/Applications'}}
badge_icon = '{icon_path}' if {icon_path.exists()} else None
icon_size = 120
icon_locations = {{
    '{app_path.name}': (160, 200),
    'Applications': (440, 200)
}}
window_rect = ((200, 200), (600, 400))
default_view = 'icon-view'
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(dmg_settings)
            settings_file = f.name

        try:
            run_command([sys.executable, "-m", "dmgbuild", "-s", settings_file, APP_NAME, str(dmg_path)])
            print(f"[OK] Created DMG with dmgbuild: {dmg_path}")
            Path(settings_file).unlink(missing_ok=True)
            return dmg_path
        except Exception as ex:
            print(f"  [WARN] dmgbuild encountered an error ({ex}), falling back to native hdiutil...")
            Path(settings_file).unlink(missing_ok=True)

    # Method 2: Native hdiutil fallback
    print("  Using macOS native hdiutil...")
    with tempfile.TemporaryDirectory() as tmp_dmg_dir:
        staging_dir = Path(tmp_dmg_dir) / APP_NAME
        staging_dir.mkdir()

        # Copy .app
        dest_app = staging_dir / app_path.name
        shutil.copytree(app_path, dest_app, symlinks=True)

        # Create /Applications symlink
        os.symlink("/Applications", staging_dir / "Applications")

        # Copy Volume Icon if available
        icns_file = PROJECT_ROOT / "src" / "finauditpro" / "assets" / "icons" / "FinAuditPro.icns"
        if icns_file.exists():
            shutil.copy2(icns_file, staging_dir / ".VolumeIcon.icns")

        # Create compressed read-only DMG
        run_command([
            "hdiutil",
            "create",
            "-volname", APP_NAME,
            "-srcfolder", str(staging_dir),
            "-ov",
            "-format", "UDZO",
            str(dmg_path)
        ])

    print(f"[OK] Created DMG with hdiutil: {dmg_path}")
    return dmg_path


def main() -> None:
    """Run full macOS build pipeline."""
    if sys.platform != "darwin":
        print("[FAIL] ERROR: scripts/packaging/build_macos.py must be run on a macOS host.")
        sys.exit(1)

    app_path = build_macos_app()
    sign_and_notarize(app_path)
    dmg_path = create_dmg(app_path)

    # Run post-build checks, manifest generation & checksums
    print("\n[OK] Running Post-Build Verification...")
    from scripts.packaging.verify_release import run_post_build_checks
    run_post_build_checks()

    print("\n" + "=" * 60)
    print("  macOS PRODUCTION BUILD COMPLETE!")
    print(f" Application: {app_path}")
    print(f" DMG Package: {dmg_path}")
    print(f" Checksums:   {PROJECT_ROOT / 'dist' / 'SHA256SUMS.txt'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
