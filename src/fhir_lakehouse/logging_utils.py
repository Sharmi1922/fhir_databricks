"""Structured logging utilities for the FHIR Lakehouse."""

from __future__ import annotations

import logging
import sys
from typing import Optional


_LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str = "fhir_lakehouse", level: int = logging.INFO) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name.
        level: Logging level.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def set_log_level(level: int, name: Optional[str] = None) -> None:
    """Update the log level of a logger at runtime."""
    logger = logging.getLogger(name or "fhir_lakehouse")
    logger.setLevel(level)