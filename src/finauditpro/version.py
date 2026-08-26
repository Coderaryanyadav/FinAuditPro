"""FinAuditPro application version and build metadata."""

import platform
import sys

__version__ = "1.1.0"
APP_NAME = "FinAuditPro"
BUILD_DATE = "2026-08-26"
MIN_PYTHON_VERSION = (3, 12)


def get_build_info() -> dict[str, str]:
    """Return genuine application build metadata dictionary."""
    return {
        "app_name": APP_NAME,
        "version": __version__,
        "build_date": BUILD_DATE,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "arch": platform.machine(),
        "offline_isolated": "True",
    }
