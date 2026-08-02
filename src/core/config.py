"""
Application Configuration Module for FinAuditPro.
Defines AppConfig model using Pydantic, handling environment variable overrides and sensible defaults.
"""

import os
import platform
from pydantic import BaseModel, Field, field_validator


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
        description="PBKDF2 HMAC-SHA256 key derivation iteration count (minimum 100,000 enforced)"
    )
    ca_firm_name: str = Field(
        default_factory=lambda: os.environ.get("FINAUDIT_CA_FIRM_NAME") or "Default CA Firm",
        description="Name of the CA Firm"
    )
    ca_frn: str = Field(
        default_factory=lambda: os.environ.get("FINAUDIT_CA_FRN") or "000000W",
        description="Firm Registration Number"
    )
    ca_name: str = Field(
        default_factory=lambda: os.environ.get("FINAUDIT_CA_NAME") or "Default CA Name",
        description="Name of the signing CA"
    )
    ca_membership_no: str = Field(
        default_factory=lambda: os.environ.get("FINAUDIT_CA_MEMBERSHIP_NO") or "000000",
        description="CA Membership Number"
    )
    database_url: str = Field(
        default_factory=lambda: os.environ.get("FINAUDITPRO_DATABASE_URL") or os.environ.get("FINAUDIT_DATABASE_URL") or os.environ.get("DATABASE_URL") or "",
        description="Optional custom database URL override (e.g. PostgreSQL)"
    )
    jwt_secret: str = Field(
        default_factory=lambda: os.environ.get("FINAUDITPRO_JWT_SECRET") or os.environ.get("FINAUDIT_JWT_SECRET") or os.environ.get("JWT_SECRET") or "finauditpro_production_jwt_secret_key_change_in_prod_2026",
        description="JWT secret key for FastAPI authentication"
    )

    @field_validator("pbkdf2_iterations", mode="before")
    @classmethod
    def clamp_pbkdf2_iterations(cls, v: int) -> int:
        """Enforce a minimum of 100,000 PBKDF2 iterations regardless of env var setting."""
        _MINIMUM = 100_000
        try:
            v = int(v)
        except (TypeError, ValueError):
            return _MINIMUM
        return max(v, _MINIMUM)

    @classmethod
    def load(cls) -> "AppConfig":
        """Instantiate AppConfig reading current environment state."""
        return cls()


# Singleton config instance
config = AppConfig.load()
