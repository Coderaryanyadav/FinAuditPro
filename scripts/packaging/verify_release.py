#!/usr/bin/env python3
"""Release quality assurance, security credentials scan, and checksum generation."""

import argparse
import hashlib
import json
import platform
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def get_git_commit() -> str:
    """Return current git commit hash or 'unknown'."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "unknown"


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_for_secrets() -> list[str]:
    """Scan workspace for accidentally committed credentials or development databases."""
    issues = []
    print("🔒 [Pre-Build] Scanning workspace for secrets & sensitive files...")

    # Forbidden files
    forbidden_files = [".env", ".env.local", "id_rsa", "private.key"]
    for fname in forbidden_files:
        matches = list(PROJECT_ROOT.rglob(fname))
        for m in matches:
            if not any(part.startswith(".") and part not in (".env", ".env.local") for part in m.parts):
                issues.append(f"Forbidden sensitive file found: {m.relative_to(PROJECT_ROOT)}")

    # Check for hardcoded private keys or tokens in source code
    secret_patterns = [
        (re.compile(r"-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----"), "Private Key Header"),
        (re.compile(r"AIza[0-9A-Za-z-_]{35}"), "Google API Key Pattern"),
        (re.compile(r"sk-[a-zA-Z0-9]{20,48}"), "OpenAI Secret Key Pattern"),
        (re.compile(r"ghp_[a-zA-Z0-9]{36}"), "GitHub Personal Access Token"),
    ]

    for py_file in (PROJECT_ROOT / "src").rglob("*.py"):
        text = py_file.read_text(encoding="utf-8", errors="ignore")
        for pattern, desc in secret_patterns:
            if pattern.search(text):
                issues.append(f"Potential secret in {py_file.relative_to(PROJECT_ROOT)}: {desc}")

    return issues


def verify_version_consistency() -> tuple[bool, str]:
    """Check that version numbers match across version.py and pyproject.toml."""
    from finauditpro.version import __version__ as version_py

    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', pyproject_text)
    if not match:
        return False, "Could not find version in pyproject.toml"

    pyproject_ver = match.group(1)
    if version_py != pyproject_ver:
        return False, f"Version mismatch: version.py={version_py} vs pyproject.toml={pyproject_ver}"

    return True, version_py


def run_pre_build_checks() -> bool:
    """Execute pre-build sanity, security, and version checks."""
    print("=" * 60)
    print(" FINAUDITPRO — PRE-BUILD RELEASE AUDIT")
    print("=" * 60)

    # 1. Version Consistency
    ok, ver_msg = verify_version_consistency()
    if not ok:
        print(f"❌ FAIL: {ver_msg}")
        return False
    print(f"✓ Authoritative Version Verified: v{ver_msg}")

    # 2. Secret Scan
    issues = scan_for_secrets()
    if issues:
        print("❌ FAIL: Security issues detected:")
        for iss in issues:
            print(f"   - {iss}")
        return False
    print("✓ Zero committed secrets or credentials detected.")

    print("✓ Pre-build release audit passed.\n")
    return True


def run_post_build_checks() -> bool:
    """Verify built artifacts in dist/, generate SHA256SUMS.txt, and release manifest."""
    print("=" * 60)
    print(" FINAUDITPRO — POST-BUILD ARTIFACT VERIFICATION")
    print("=" * 60)

    dist_dir = PROJECT_ROOT / "dist"
    if not dist_dir.exists():
        print("❌ FAIL: dist/ directory does not exist. Run build script first.")
        return False

    from finauditpro.version import APP_NAME, __version__

    artifacts = []
    checksum_lines = []

    # Identify primary distribution artifacts
    for item in sorted(dist_dir.iterdir()):
        if item.name in ("SHA256SUMS.txt", "release_manifest.json", ".DS_Store"):
            continue

        if item.is_file() or (item.is_dir() and item.suffix == ".app"):
            size_bytes = item.stat().st_size if item.is_file() else sum(f.stat().st_size for f in item.rglob("*") if f.is_file())

            # If it's a file, compute checksum directly
            sha = compute_sha256(item) if item.is_file() else "bundle-directory"

            artifacts.append({
                "name": item.name,
                "type": "file" if item.is_file() else "app_bundle",
                "size_bytes": size_bytes,
                "sha256": sha,
            })

            if item.is_file():
                checksum_lines.append(f"{sha}  {item.name}\n")
                print(f"  ✓ Found artifact: {item.name} ({size_bytes / (1024 * 1024):.2f} MB)")
                print(f"    SHA-256: {sha}")
            else:
                print(f"  ✓ Found bundle: {item.name} ({size_bytes / (1024 * 1024):.2f} MB)")

    if not artifacts:
        print("❌ FAIL: No release artifacts found in dist/")
        return False

    # Write SHA256SUMS.txt
    if checksum_lines:
        sums_file = dist_dir / "SHA256SUMS.txt"
        sums_file.write_text("".join(checksum_lines), encoding="utf-8")
        print(f"✓ Generated checksums manifest: {sums_file.name}")

    # Generate machine-readable release manifest
    manifest = {
        "application": APP_NAME,
        "version": __version__,
        "build_date": datetime.now(UTC).isoformat(),
        "git_commit": get_git_commit(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": sys.version.split()[0],
        "artifacts": artifacts,
    }

    manifest_file = dist_dir / "release_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"✓ Generated release manifest: {manifest_file.name}")

    print("=" * 60)
    print(" POST-BUILD VERIFICATION: ALL CHECKS PASSED")
    print("=" * 60)
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinAuditPro Release Verification Tool")
    parser.add_argument("--pre-build", action="store_true", help="Run pre-build security & version checks")
    parser.add_argument("--post-build", action="store_true", help="Run post-build artifact verification & checksum generation")
    args = parser.parse_args()

    if not args.pre_build and not args.post_build:
        # Default: run both
        if not run_pre_build_checks():
            sys.exit(1)
        if (PROJECT_ROOT / "dist").exists():
            if not run_post_build_checks():
                sys.exit(1)
    else:
        if args.pre_build and not run_pre_build_checks():
            sys.exit(1)
        if args.post_build and not run_post_build_checks():
            sys.exit(1)
