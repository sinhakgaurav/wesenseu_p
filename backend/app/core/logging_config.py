"""Central logging configuration for Monitour API."""
from __future__ import annotations

import logging
import sys
from typing import Optional


def setup_logging(level: str = "INFO", app_env: str = "development") -> None:
    log_level = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if root.handlers:
        root.setLevel(log_level)
        return

    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | "
        + ("%(message)s" if app_env == "production" else "%(funcName)s:%(lineno)d | %(message)s")
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))
    root.addHandler(handler)
    root.setLevel(log_level)

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level <= logging.DEBUG else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or "monitour")
