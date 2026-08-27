#!/usr/bin/env python3
"""Build and package FinAuditPro for Windows (Standalone Executable & Inno Setup Installer)."""

import os
import platform
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def run_command(cmd: list[str], cwd: Path | None = None) -> None:
    """Run shell command with error checking."""
    print(f"  → Running: {' '.join(cmd)}")
    subprocess.run(cmd, cwd=cwd or PROJECT_ROOT, check=True)


def find_inno_setup_compiler() -> Path | None:
    """Find Inno Setup compiler (ISCC.exe)."""
    # 1. PATH check
    iscc = shutil.which("ISCC.exe") or shutil.which("iscc")
    if iscc:
        return Path(iscc)

    # 2. Standard Program Files locations
    candidates = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    for c in candidates:
        if c.exists():
            return c

    return None


def build_windows_app() -> Path:
    """Build Windows executable using PyInstaller."""
    from finauditpro.version import APP_NAME, __version__

    print("=" * 60)
    print(f" BUILDING {APP_NAME} v{__version__} FOR Windows ({platform.machine()})")
    print("=" * 60)

    # 1. Ensure icons exist
    icons_dir = PROJECT_ROOT / "src" / "finauditpro" / "assets" / "icons"
    if not (icons_dir / "FinAuditPro.ico").exists():
        print("Icons missing. Generating application icons...")
        from scripts.packaging.generate_icons import generate_all_icons
        generate_all_icons(icons_dir)

    # 2. Run clean
    from scripts.packaging.clean import clean_build_artifacts
    clean_build_artifacts()

    # 3. Pre-build checks
    from scripts.packaging.verify_release import run_pre_build_checks
    if not run_pre_build_checks():
        print("❌ Pre-build checks failed. Aborting build.")
        sys.exit(1)

    # 4. Invoke PyInstaller
    spec_path = PROJECT_ROOT / "finauditpro.spec"
    print(f"\n📦 Executing PyInstaller with spec: {spec_path.name}...")
    run_command([sys.executable, "-m", "PyInstaller", str(spec_path), "--noconfirm"])

    output_dir = PROJECT_ROOT / "dist" / "FinAuditPro"
    exe_path = output_dir / "FinAuditPro.exe"
    if not output_dir.exists() and not (PROJECT_ROOT / "dist" / "FinAuditPro.exe").exists():
        print(f"❌ ERROR: Output executable not found at: {output_dir}")
        sys.exit(1)

    target_exe = exe_path if exe_path.exists() else (PROJECT_ROOT / "dist" / "FinAuditPro.exe")
    print(f"✓ PyInstaller bundle created successfully: {target_exe}")

    # Smoke test on Windows
    print("\n🧪 Executing runtime smoke test on packaged Windows binary...")
    test_env = os.environ.copy()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_data_dir:
        test_env["FINAUDITPRO_DATA_DIR"] = tmp_data_dir
        res = subprocess.run([str(target_exe), "--headless"], env=test_env, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"❌ Runtime smoke test failed with exit code {res.returncode}:")
            print(res.stderr or res.stdout)
            sys.exit(1)
        print(f"✓ Runtime smoke test passed: {res.stdout.strip()}")

    return output_dir


def create_installer_or_archive(bundle_dir: Path) -> Path:
    """Compile Inno Setup Installer or create portable zip archive."""
    from finauditpro.version import APP_NAME, __version__

    iscc = find_inno_setup_compiler()
    iss_file = PROJECT_ROOT / "scripts" / "packaging" / "finauditpro.iss"

    if iscc and iss_file.exists():
        print(f"\n💿 Inno Setup Compiler found: {iscc}")
        print("   Compiling Windows Installer (Setup.exe)...")
        run_command([str(iscc), str(iss_file)])
        installer_name = f"{APP_NAME}-Setup-{__version__}-x64.exe"
        installer_path = PROJECT_ROOT / "dist" / installer_name
        print(f"✓ Created Windows Installer: {installer_path}")
        return installer_path
    else:
        print("\n📦 Inno Setup not found. Creating standalone portable ZIP distribution...")
        zip_name = f"{APP_NAME}-{__version__}-Windows-x64.zip"
        zip_path = PROJECT_ROOT / "dist" / zip_name

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in bundle_dir.rglob("*"):
                zf.write(item, arcname=f"{APP_NAME}/{item.relative_to(bundle_dir)}")

        print(f"✓ Created standalone portable archive: {zip_path}")
        return zip_path


def main() -> None:
    """Run full Windows build pipeline."""
    if sys.platform != "win32":
        print("⚠ NOTICE: scripts/packaging/build_windows.py is designed for Windows runners.")
        print("  On macOS/Linux, PyInstaller cannot cross-compile Windows native PE binaries.")
        print("  Use GitHub Actions or a Windows machine to build the Windows release.")
        sys.exit(1)

    bundle_dir = build_windows_app()
    artifact_path = create_installer_or_archive(bundle_dir)

    print("\n🔍 Running Post-Build Verification...")
    from scripts.packaging.verify_release import run_post_build_checks
    run_post_build_checks()

    print("\n" + "=" * 60)
    print(" 🎉 Windows PRODUCTION BUILD COMPLETE!")
    print(f" Output:    {artifact_path}")
    print(f" Checksums: {PROJECT_ROOT / 'dist' / 'SHA256SUMS.txt'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
