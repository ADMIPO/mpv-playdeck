"""Simple logging configuration used across the project."""

from __future__ import annotations

import logging
from typing import Optional


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger for the application.

    Parameters
    ----------
    level:
        Logging level to configure for the root logger. Defaults to ``logging.INFO``.
    """

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger instance.

    Parameters
    ----------
    name:
        Optional logger name. Defaults to the root logger when ``None``.
    """

    return logging.getLogger(name)
