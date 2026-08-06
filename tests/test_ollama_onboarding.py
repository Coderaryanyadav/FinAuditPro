import sys
import os
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath('src'))
from PySide6.QtWidgets import QApplication, QLabel
from ai.ollama_client import OllamaClient

app = QApplication.instance() or QApplication(sys.argv)

def test_ollama_status_offline():
    with patch("requests.get", side_effect=Exception("Connection refused")):
        status, headline, instructions, active_model = OllamaClient.check_status_details()
        assert status == "offline"
        assert "Not Installed" in headline or "Stopped" in headline
        assert "https://ollama.com" in instructions
        assert "ollama pull" in instructions

def test_ollama_status_no_models():
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"models": []}
    with patch("requests.get", return_value=mock_res):
        status, headline, instructions, active_model = OllamaClient.check_status_details()
        assert status == "no_models"
        assert "No AI Models Downloaded" in headline
        assert "ollama pull" in instructions

def test_ollama_status_online():
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"models": [{"name": "llama3.2:latest"}]}
    with patch("requests.get", return_value=mock_res):
        status, headline, instructions, active_model = OllamaClient.check_status_details()
        assert status == "online"
        assert "Active" in headline

def test_ai_audit_widget_onboarding_banner():
    with patch("requests.get", side_effect=Exception("Connection refused")):
        from ui.ai_analysis import AIAuditWidget
        widget = AIAuditWidget()
        assert widget._ollama_online is False
        assert widget.findChild(QLabel, "chatSenderLabel") is not None or widget.chat_layout.count() > 0
