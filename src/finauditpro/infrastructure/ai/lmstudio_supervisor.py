"""LM Studio background server supervisor and process management for FinAuditPro local AI."""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any


class LMStudioSupervisor:
    """Supervisor managing local LM Studio HTTP REST server daemon detection, background auto-start, and health monitoring."""

    DEFAULT_PORT = 1234
    DEFAULT_HOST = "localhost"

    @classmethod
    def get_base_url(cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
        return f"http://{host}:{port}"

    @classmethod
    def is_server_online(
        cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 1.5
    ) -> bool:
        """Probe local LM Studio HTTP REST API endpoint /v1/models."""
        url = f"{cls.get_base_url(host, port)}/v1/models"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinAuditPro-Supervisor/1.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status == 200
        except Exception:
            return False

    @classmethod
    def get_available_models(cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> list[str]:
        """Fetch list of loaded or available local AI model identifiers."""
        url = f"{cls.get_base_url(host, port)}/v1/models"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "FinAuditPro-Supervisor/1.0"})
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    models = data.get("data", [])
                    return [m.get("id", "unknown") for m in models if isinstance(m, dict)]
        except Exception:
            pass
        return []

    @classmethod
    def find_lms_cli(cls) -> Path | None:
        """Search system PATH and standard macOS / Linux locations for `lms` CLI tool."""
        # 1. Search PATH
        lms_path = shutil.which("lms")
        if lms_path:
            return Path(lms_path)

        # 2. Search common user local bin directories
        home = Path.home()
        candidates = [
            home / ".cache" / "lm-studio" / "bin" / "lms",
            home / ".lmstudio" / "bin" / "lms",
            Path("/usr/local/bin/lms"),
            Path("/opt/homebrew/bin/lms"),
            home / ".local" / "bin" / "lms",
        ]
        for candidate in candidates:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return candidate

        return None

    @classmethod
    def start_server_background(
        cls, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, wait_timeout: float = 6.0
    ) -> bool:
        """Attempt to spawn `lms server start` background process daemon."""
        if cls.is_server_online(host, port):
            return True

        cli_bin = cls.find_lms_cli()
        if not cli_bin:
            # Fallback: check macOS /Applications/LM Studio.app
            mac_app = Path("/Applications/LM Studio.app")
            if mac_app.exists() and sys.platform == "darwin":
                try:
                    subprocess.Popen(
                        ["open", "-a", "LM Studio"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    return False
            else:
                return False
        else:
            try:
                subprocess.Popen(
                    [str(cli_bin), "server", "start", "--port", str(port)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                return False

        # Wait for server readiness with polling
        start_time = time.time()
        while time.time() - start_time < wait_timeout:
            if cls.is_server_online(host, port, timeout=1.0):
                return True
            time.sleep(0.5)

        return cls.is_server_online(host, port)

    @classmethod
    def load_model_via_cli(cls, model_query: str = "deepseek", wait_timeout: float = 30.0) -> bool:
        """Automatically load model into LM Studio memory using `lms load <query>`."""
        cli_bin = cls.find_lms_cli()
        if not cli_bin:
            return False

        try:
            res = subprocess.run(
                [str(cli_bin), "load", model_query],
                capture_output=True,
                text=True,
                timeout=wait_timeout,
            )
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def ensure_ai_server_ready(cls, auto_start: bool = True) -> dict[str, Any]:
        """Check status and auto-activate local LM Studio server background process & load default model."""
        online = cls.is_server_online()
        action_taken = "already_running" if online else "none"

        if not online and auto_start:
            started = cls.start_server_background()
            if started:
                online = True
                action_taken = "auto_started"
            else:
                action_taken = "failed_or_not_installed"

        models = cls.get_available_models() if online else []
        if online and not models and auto_start:
            cls.load_model_via_cli("deepseek")
            models = cls.get_available_models()
            if models:
                action_taken += "_model_loaded"

        return {
            "is_online": online,
            "action_taken": action_taken,
            "host": cls.DEFAULT_HOST,
            "port": cls.DEFAULT_PORT,
            "url": cls.get_base_url(),
            "models_loaded": models,
            "cli_found": str(cls.find_lms_cli()) if cls.find_lms_cli() else None,
        }
