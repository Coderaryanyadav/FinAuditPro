"""Automated unit test verifying LM Studio supervisor process management and detection."""

from finauditpro.infrastructure.ai.lmstudio_supervisor import LMStudioSupervisor


def test_lm_studio_supervisor_probe() -> None:
    """Verify LMStudioSupervisor url construction and server health check."""
    url = LMStudioSupervisor.get_base_url()
    assert url == "http://localhost:1234"

    # Server online status check returns boolean without raising exception
    online = LMStudioSupervisor.is_server_online(timeout=0.5)
    assert isinstance(online, bool)


def test_lm_studio_supervisor_auto_ready() -> None:
    """Verify ensure_ai_server_ready returns structured diagnostic state."""
    status = LMStudioSupervisor.ensure_ai_server_ready(auto_start=False)
    assert "is_online" in status
    assert "action_taken" in status
    assert "url" in status
    assert status["url"] == "http://localhost:1234"
