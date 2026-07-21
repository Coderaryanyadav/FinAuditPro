"""
System Diagnostics & Health Monitor for FinAuditPro.
Performs pre-flight checks on Python runtime, Qt environment, local Ollama LLM daemon, SQLite database, and disk space.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import sys
import os
import shutil
import platform
try:
    import requests
except ImportError:
    requests = None
import logging

logger = logging.getLogger(__name__)

@dataclass
class DiagnosticReport:
    python_version: str
    operating_system: str
    pyside6_status: str
    sqlite_status: str
    ollama_api_status: str
    free_disk_space_gb: float
    all_healthy: bool
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "python_version": self.python_version,
            "operating_system": self.operating_system,
            "pyside6_status": self.pyside6_status,
            "sqlite_status": self.sqlite_status,
            "ollama_api_status": self.ollama_api_status,
            "free_disk_space_gb": round(self.free_disk_space_gb, 2),
            "all_healthy": self.all_healthy,
            "issues": self.issues,
        }


class SystemDiagnostics:
    """Performs full pre-flight health diagnostic checks."""

    @classmethod
    def run_diagnostics(cls, ollama_url: str = "http://localhost:11434") -> DiagnosticReport:
        issues = []

        # 1. OS & Python
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

        # 2. PySide6 Check
        try:
            import PySide6
            pyside6_status = f"Available ({PySide6.__version__})"
        except ImportError:
            pyside6_status = "Missing PySide6"
            issues.append("PySide6 GUI package is not installed.")

        # 3. SQLite Database Check
        try:
            import sqlite3
            con = sqlite3.connect(":memory:")
            con.close()
            sqlite_status = "Healthy (SQLite3)"
        except Exception as e:
            sqlite_status = f"Error: {e}"
            issues.append(f"SQLite database engine error: {e}")

        # 4. Ollama API Connectivity Check
        if requests:
            try:
                res = requests.get(f"{ollama_url}/api/tags", timeout=2)
                if res.status_code == 200:
                    ollama_status = "Online (Local LLM Active)"
                else:
                    ollama_status = f"Ollama HTTP {res.status_code}"
                    issues.append("Ollama API responded with non-200 code.")
            except Exception:
                ollama_status = "Offline (Ollama service not running on localhost:11434)"
                issues.append("Ollama daemon is offline. Run 'ollama serve' for local AI functionality.")
        else:
            ollama_status = "HTTP requests package not installed"

        # 5. Free Disk Space
        stat = shutil.disk_usage(os.getcwd())
        free_gb = stat.free / (1024 ** 3)
        if free_gb < 1.0:
            issues.append(f"Low disk space warning: Only {free_gb:.2f} GB free.")

        all_healthy = len(issues) == 0

        return DiagnosticReport(
            python_version=py_ver,
            operating_system=os_info,
            pyside6_status=pyside6_status,
            sqlite_status=sqlite_status,
            ollama_api_status=ollama_status,
            free_disk_space_gb=free_gb,
            all_healthy=all_healthy,
            issues=issues
        )
