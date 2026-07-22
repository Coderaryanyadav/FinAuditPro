#!/usr/bin/env python3
"""
FinAuditPro Universal Environment Bootstrapper & Dependency Auto-Installer
Detects OS (Windows, macOS, Linux), verifies runtime requirements (Python 3.11+, Tesseract, Ollama),
automatically installs missing dependencies, creates virtual environments, and prepares execution.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def print_banner():
    print("=" * 70)
    print(" 🚀 FinAuditPro Environment Bootstrapper & Auto-Installer")
    print("=" * 70)
    print(f" Detected OS : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f" Python Exec : {sys.executable} (v{platform.python_version()})")
    print("=" * 70 + "\n")

def check_python_version():
    print("🔍 [1/5] Verifying Python Version...")
    major, minor = sys.version_info[:2]
    if major < 3 or (major == 3 and minor < 10):
        print(f"❌ Error: Python 3.10+ required. Found Python {major}.{minor}")
        sys.exit(1)
    print(f"✅ Python {major}.{minor} meets system requirements.\n")

def check_virtual_environment():
    print("🔍 [2/5] Checking Virtual Environment...")
    venv_dir = ROOT_DIR / ".venv"
    in_venv = sys.prefix != sys.base_prefix
    
    if in_venv:
        print(f"✅ Active virtual environment detected: {sys.prefix}\n")
        return sys.executable
    elif venv_dir.exists():
        print(f"✅ Existing .venv directory found at {venv_dir}")
        if platform.system() == "Windows":
            return str(venv_dir / "Scripts" / "python.exe")
        return str(venv_dir / "bin" / "python")
    else:
        print("💡 Creating new virtual environment at .venv...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            print("✅ Virtual environment created successfully.\n")
            if platform.system() == "Windows":
                return str(venv_dir / "Scripts" / "python.exe")
            return str(venv_dir / "bin" / "python")
        except Exception as e:
            print(f"⚠️ Could not create venv automatically: {e}. Proceeding with global python.\n")
            return sys.executable

def install_python_dependencies(python_bin):
    print("📦 [3/5] Installing Python Dependencies from requirements.txt...")
    req_file = ROOT_DIR / "requirements.txt"
    if not req_file.exists():
        print("❌ requirements.txt not found!")
        return
    
    try:
        # Upgrade pip
        subprocess.run([python_bin, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        # Install requirements
        subprocess.run([python_bin, "-m", "pip", "install", "-r", str(req_file)], check=True)
        print("✅ Python dependencies installed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Package installation encountered warnings/errors: {e}\n")

def check_system_tools():
    print("⚙️ [4/5] Checking System Dependencies (Tesseract OCR & Ollama)...")
    
    # Check Tesseract
    tesseract_path = shutil.which("tesseract")
    if tesseract_path:
        print(f"  ✅ Tesseract OCR found at: {tesseract_path}")
    else:
        print("  ⚠️ Tesseract OCR not detected in PATH.")
        os_sys = platform.system()
        if os_sys == "Windows":
            print("     -> Download installer: https://github.com/UB-Mannheim/tesseract/wiki")
        elif os_sys == "Darwin":
            print("     -> Install via Homebrew: brew install tesseract")
        elif os_sys == "Linux":
            print("     -> Install via APT: sudo apt install tesseract-ocr")

    # Check Ollama
    ollama_path = shutil.which("ollama")
    if ollama_path:
        print(f"  ✅ Ollama Local AI daemon found at: {ollama_path}")
    else:
        print("  💡 Ollama AI daemon optional for local LLM features.")
        print("     -> Download: https://ollama.ai/")
    print()

def launch_application(python_bin):
    print("🚀 [5/5] Launching FinAuditPro Application...")
    main_py = ROOT_DIR / "src" / "main.py"
    if not main_py.exists():
        print(f"❌ Main application file not found at {main_py}")
        return
    
    print("=" * 70)
    print(" FinAuditPro is starting. Press Ctrl+C in terminal to stop.")
    print("=" * 70 + "\n")
    try:
        subprocess.run([python_bin, str(main_py)])
    except KeyboardInterrupt:
        print("\n👋 FinAuditPro shut down cleanly.")

def main():
    print_banner()
    check_python_version()
    python_bin = check_virtual_environment()
    install_python_dependencies(python_bin)
    check_system_tools()
    
    if "--no-launch" not in sys.argv:
        launch_application(python_bin)

if __name__ == "__main__":
    main()
