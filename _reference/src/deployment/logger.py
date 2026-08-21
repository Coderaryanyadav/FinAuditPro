"""
Enterprise Application Logging System for FinAuditPro.
Configures file and console logging with automatic log rotation and formatting.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
import sys

LOG_DIR = "logs"
LOG_FILE_NAME = "finauditpro.log"

def get_log_file_path() -> str:
    """Returns absolute path to the main application log file."""
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.abspath(os.path.join(LOG_DIR, LOG_FILE_NAME))

def setup_application_logging(level: int = logging.INFO) -> str:
    """Configures application-wide logging with file rotation."""
    log_path = get_log_file_path()

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # 2. Rotating File Handler (10 MB max, 5 backups)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info(f"Initialized application logging -> {log_path}")
    return log_path
