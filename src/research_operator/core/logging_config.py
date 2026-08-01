"""Configuración central de logging para Yatiri.

Nivel controlado por la variable de entorno YATIRI_LOG_LEVEL (default
WARNING). Los logs van a stderr, así que no interfieren con la salida
normal del CLI (stdout) ni con `rich`.
"""
from __future__ import annotations

import logging
import os

_ROOT_NAME = "research_operator"
_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    _configured = True
    level_name = os.environ.get("YATIRI_LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    root = logging.getLogger(_ROOT_NAME)
    root.setLevel(level)
    root.propagate = False
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(name)
