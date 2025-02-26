"""
Logging configuration for the project.

This module provides a standardized logging setup for all project scripts.
It configures console and file logging with different levels and formatting.

Usage:
    from src.logger import get_logger

    # Get a logger for the current module
    logger = get_logger(__name__)

    # Use the logger
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


# Create logs directory if it doesn't exist
def ensure_logs_directory():
    """Create logs directory if it doesn't exist"""
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


# Configure logging
def get_logger(name, level=logging.INFO):
    """
    Get a logger configured with standardized settings.

    Args:
        name (str): Name for the logger, typically __name__
        level (int): Logging level (default: logging.INFO)

    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Only configure handlers if not already configured
    if not logger.handlers:
        logger.setLevel(level)

        # Create formatter
        timestamp_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt=timestamp_format,
        )

        # Console handler (INFO and above)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # File handler (DEBUG and above)
        logs_dir = ensure_logs_directory()
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            logs_dir / f"{current_date}.log", encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger


# Root logger configuration
def configure_root_logger(level=logging.INFO):
    """Configure the root logger with standardized settings"""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                ensure_logs_directory() / f"{datetime.now().strftime('%Y-%m-%d')}.log",
                encoding="utf-8",
            ),
        ],
    )
