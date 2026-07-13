"""
Centralized logging configuration helper.

Exists so every module logs through `logging.getLogger("plasmaforge.<x>")`
consistently, and so log formatting only needs to be defined once. Modules
should call `get_logger(__name__)` rather than configuring logging
themselves.
"""

import logging

from plasmaforge.config.settings import settings

_CONFIGURED = False


def _configure_once() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_once()
    return logging.getLogger(name)
