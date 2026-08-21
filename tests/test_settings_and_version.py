"""Unit tests for SettingsService persistence and cloud AI opt-out defaults."""

from finauditpro.application.services.settings_service import AppSettings, SettingsService


def test_settings_service_defaults(tmp_path) -> None:
    """Verify SettingsService returns default configuration when JSON file does not exist."""
    config_file = tmp_path / "settings.json"
    service = SettingsService(config_file)
    settings = service.get_settings()

    assert settings.lm_studio_endpoint == "http://localhost:1234"
    assert settings.llm_model == "deepseek-r1-distill-qwen-14b"
    assert settings.allow_cloud_ai is False  # Air-gapped default


def test_settings_service_update_and_persistence(tmp_path) -> None:
    """Verify SettingsService persists updated configuration to JSON file."""
    config_file = tmp_path / "settings.json"
    service = SettingsService(config_file)

    updated = AppSettings(
        lm_studio_endpoint="http://localhost:5678",
        llm_model="custom-llm",
        embedding_model="custom-embed",
        allow_cloud_ai=False,
    )
    service.update_settings(updated)

    reloaded_service = SettingsService(config_file)
    reloaded = reloaded_service.get_settings()
    assert reloaded.lm_studio_endpoint == "http://localhost:5678"
    assert reloaded.llm_model == "custom-llm"
