"""Application settings and configuration service managing LM Studio endpoints and privacy opt-outs."""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from finauditpro.infrastructure.first_run import get_app_data_dir


class AppSettings(BaseModel):
    lm_studio_endpoint: str = Field(default="http://localhost:1234")
    llm_model: str = Field(default="deepseek-r1-distill-qwen-14b")
    embedding_model: str = Field(default="nomic-embed-text")
    allow_cloud_ai: bool = Field(default=False)


class SettingsService:
    """Service managing application settings persistence to JSON file."""

    def __init__(self, config_file: Path | None = None) -> None:
        if config_file is None:
            self.config_path = get_app_data_dir() / "settings.json"
        else:
            self.config_path = config_file

    def get_settings(self) -> AppSettings:
        """Load settings from JSON file or return defaults."""
        if not self.config_path.exists():
            return AppSettings()
        try:
            content = self.config_path.read_text(encoding="utf-8")
            data = json.loads(content)
            return AppSettings(**data)
        except Exception:
            return AppSettings()

    def update_settings(self, settings: AppSettings) -> AppSettings:
        """Save settings to JSON file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
        return settings
