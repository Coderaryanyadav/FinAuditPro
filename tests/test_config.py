"""
Unit tests for AppConfig in src/core/config.py.
Verifies default values and environment variable overrides.
"""

import os
from unittest.mock import patch
from core.config import AppConfig


import core.config


def teardown_module(module):
    """Restore default global config and crypto keys after environment override tests."""
    try:
        import security.crypto
        security.crypto._PROCESS_INSTALLATION_KEY = None
        security.crypto._PROCESS_INSTALLATION_SALT = None
    except Exception:
        pass
    core.config.config = core.config.AppConfig.load()



def test_app_config_defaults():
    """Verify default config values when environment variables are unset."""
    with patch.dict(os.environ, {}, clear=True):
        cfg = AppConfig.load()
        assert cfg.ollama_host == "http://localhost:11434"
        assert cfg.session_timeout_minutes == 30
        assert cfg.pbkdf2_iterations == 600000
        assert cfg.data_dir is not None


def test_app_config_env_overrides():
    """Verify environment variable overrides for all 4 parameters."""
    custom_env = {
        "FINAUDIT_DATA_DIR": "/tmp/custom_finaudit_data",
        "FINAUDIT_OLLAMA_HOST": "http://192.168.1.100:11434",
        "FINAUDIT_SESSION_TIMEOUT": "45",
        "FINAUDIT_PBKDF2_ITERATIONS": "700000"
    }
    with patch.dict(os.environ, custom_env, clear=True):
        cfg = AppConfig.load()
        assert cfg.data_dir == "/tmp/custom_finaudit_data"
        assert cfg.ollama_host == "http://192.168.1.100:11434"
        assert cfg.session_timeout_minutes == 45
        assert cfg.pbkdf2_iterations == 700000


def test_app_config_fallback_env_keys():
    """Verify secondary environment variable key overrides (OLLAMA_HOST, SESSION_TIMEOUT_MINUTES, PBKDF2_ITERATIONS)."""
    custom_env = {
        "DATA_DIR": "/tmp/data_dir_fallback",
        "OLLAMA_HOST": "http://ollama-server:11434",
        "SESSION_TIMEOUT_MINUTES": "15",
        "PBKDF2_ITERATION_COUNT": "500000"
    }
    with patch.dict(os.environ, custom_env, clear=True):
        cfg = AppConfig.load()
        assert cfg.data_dir == "/tmp/data_dir_fallback"
        assert cfg.ollama_host == "http://ollama-server:11434"
        assert cfg.session_timeout_minutes == 15
        assert cfg.pbkdf2_iterations == 500000

