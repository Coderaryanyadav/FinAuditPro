"""Launch-time and on-demand environment self-check probe for system prerequisites and dependencies."""

import importlib.util
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from finauditpro.infrastructure.first_run import get_app_data_dir


@dataclass
class CheckItem:
    name: str
    status: str  # "PASS", "WARN", "FAIL"
    message: str
    remediation: str = ""


@dataclass
class EnvironmentStatusDTO:
    is_healthy: bool
    items: list[CheckItem] = field(default_factory=list)


class EnvironmentChecker:
    """Probes system prerequisites honestly and returns environment status."""

    def __init__(self, lm_studio_base_url: str = "http://localhost:1234") -> None:
        self.lm_studio_base_url = lm_studio_base_url

    def run_full_check(self) -> EnvironmentStatusDTO:
        return self.run_all_checks()

    def check_python_version(self) -> CheckItem:
        major, minor = sys.version_info[:2]
        if (major, minor) >= (3, 12):
            return CheckItem(
                name="Python Runtime",
                status="PASS",
                message=f"Python {sys.version.split()[0]} is compatible (>= 3.12).",
            )
        return CheckItem(
            name="Python Runtime",
            status="FAIL",
            message=f"Python {sys.version.split()[0]} detected. Python 3.12+ is required.",
            remediation="Upgrade Python installation to version 3.12 or higher.",
        )

    def check_data_directories(self) -> CheckItem:
        app_dir = get_app_data_dir()
        try:
            app_dir.mkdir(parents=True, exist_ok=True)
            test_file = app_dir / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return CheckItem(
                name="Application Data Directory",
                status="PASS",
                message=f"Data directory '{app_dir}' is writable.",
            )
        except Exception as ex:
            return CheckItem(
                name="Application Data Directory",
                status="FAIL",
                message=f"Data directory '{app_dir}' is not writable: {ex}",
                remediation="Ensure write permissions exist for the application data folder.",
            )

    def check_tesseract_ocr(self) -> CheckItem:
        tess_path = shutil.which("tesseract")
        if not tess_path and Path("/opt/homebrew/bin/tesseract").exists():
            tess_path = "/opt/homebrew/bin/tesseract"

        if tess_path:
            return CheckItem(
                name="Tesseract OCR Engine",
                status="PASS",
                message=f"Tesseract OCR binary found at '{tess_path}'.",
            )
        return CheckItem(
            name="Tesseract OCR Engine",
            status="WARN",
            message="Tesseract OCR binary not found on PATH or /opt/homebrew/bin.",
            remediation="Install Tesseract OCR via Homebrew (`brew install tesseract`) to enable image/scanned PDF text extraction.",
        )

    def check_pyinstaller_availability(self) -> CheckItem:
        spec = importlib.util.find_spec("PyInstaller")
        if spec:
            return CheckItem(
                name="PyInstaller Build Tool",
                status="PASS",
                message="PyInstaller package is installed.",
            )
        return CheckItem(
            name="PyInstaller Build Tool",
            status="WARN",
            message="PyInstaller is not installed in this environment.",
            remediation="PyInstaller build script exists (`scripts/build_app.sh`). Install via pip when network access is available.",
        )

    def check_lm_studio_reachability(self) -> CheckItem:
        url = f"{self.lm_studio_base_url}/v1/models"
        try:
            resp = httpx.get(url, timeout=2.0)
            if resp.status_code == 200:
                models_data = resp.json().get("data", [])
                model_names = [m.get("id", "") for m in models_data]
                return CheckItem(
                    name="LM Studio API Server",
                    status="PASS",
                    message=f"LM Studio reachable at '{self.lm_studio_base_url}'. Loaded models: {', '.join(model_names) if model_names else 'None'}",
                )
            return CheckItem(
                name="LM Studio API Server",
                status="WARN",
                message=f"LM Studio responded with HTTP status {resp.status_code}.",
                remediation="Launch LM Studio, load models, and enable the local server at port 1234.",
            )
        except Exception:
            return CheckItem(
                name="LM Studio API Server",
                status="WARN",
                message=f"LM Studio API server at '{self.lm_studio_base_url}' is unreachable.",
                remediation="Start LM Studio local server (`http://localhost:1234`). AI capabilities will degrade gracefully to deterministic analytics.",
            )

    def run_all_checks(self) -> EnvironmentStatusDTO:
        items = [
            self.check_python_version(),
            self.check_data_directories(),
            self.check_tesseract_ocr(),
            self.check_lm_studio_reachability(),
            self.check_pyinstaller_availability(),
        ]
        is_healthy = not any(item.status == "FAIL" for item in items)
        return EnvironmentStatusDTO(is_healthy=is_healthy, items=items)
