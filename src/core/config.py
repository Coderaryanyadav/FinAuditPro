"""
Application Configuration Module for FinAuditPro.
Defines AppConfig model using Pydantic, handling environment variable overrides and sensible defaults.
"""

import os
import platform
from pydantic import BaseModel, Field


def get_default_data_dir() -> str:
    """Resolve default data directory per platform or fallback."""
    if env_dir := (os.environ.get("FINAUDIT_DATA_DIR") or os.environ.get("DATA_DIR")):
        return env_dir
    
    system = platform.system()
    if system == "Windows":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    elif system == "Darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    app_dir = os.path.join(base, "FinAuditPro")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


class AppConfig(BaseModel):
    """Application configuration model with environment variable fallbacks."""

    data_dir: str = Field(
        default_factory=get_default_data_dir,
        description="Path to user-writable data directory"
    )
    ollama_host: str = Field(
        default_factory=lambda: os.environ.get("FINAUDIT_OLLAMA_HOST") or os.environ.get("OLLAMA_HOST") or "http://localhost:11434",
        description="Base URL for Ollama local LLM service"
    )
    session_timeout_minutes: int = Field(
        default_factory=lambda: int(os.environ.get("FINAUDIT_SESSION_TIMEOUT") or os.environ.get("SESSION_TIMEOUT_MINUTES") or "30"),
        description="User session timeout in minutes"
    )
    pbkdf2_iterations: int = Field(
        default_factory=lambda: int(os.environ.get("FINAUDIT_PBKDF2_ITERATIONS") or os.environ.get("PBKDF2_ITERATION_COUNT") or "600000"),
        description="PBKDF2 HMAC-SHA256 key derivation iteration count"
    )

    @classmethod
    def load(cls) -> "AppConfig":
        """Instantiate AppConfig reading current environment state."""
        return cls()


# Singleton config instance
config = AppConfig.load()
