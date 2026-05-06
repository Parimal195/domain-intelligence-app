"""
Structured logging for the Domain Intelligence App.
Provides consistent log formatting across all modules.
"""

import logging
import sys
from datetime import datetime
from utils.config import LOG_DIR


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Create a named logger with console and file handlers.
    
    Args:
        name: Logger name (typically __name__ of calling module).
        level: Logging level.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (OSError, PermissionError):
        # Graceful fallback — log only to console if file not writable
        logger.warning(f"Could not write to log file: {log_file}")

    return logger
