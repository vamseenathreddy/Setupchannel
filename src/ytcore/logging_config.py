"""
Logging configuration.

Sets up a root logger that writes to:
- console (human-readable, for docker logs / interactive runs)
- a rotating daily log file under settings.log_dir (for post-mortem debugging
  of the 5 AM run, since nobody is watching a terminal at that hour)

Call `configure_logging()` once at process startup (pipeline.py entrypoint,
and at the top of test fixtures). Every other module just does:

    import logging
    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

_CONFIGURED = False

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(log_dir: Path, level: int = logging.INFO) -> None:
    """Idempotently configure the root logger. Safe to call multiple times."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "ytcore.log"

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Force UTF-8 on stdout before attaching the console handler. Without
    # this, a real run showed "--- Logging error ---" (Python logging's
    # own failure notice) when stdout was redirected to a file on
    # Windows (e.g. `python ... *> out.log` in a PowerShell wrapper) --
    # sys.stdout silently falls back to the legacy system codepage in
    # that case, which can't encode Telugu text or emoji. errors="replace"
    # is a safety net so an unexpected character can never crash logging
    # again, even if reconfigure() itself isn't available for some reason.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, ValueError):
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=str(log_file),
        when="midnight",
        backupCount=30,   # keep 30 days of logs
        encoding="utf-8",
        utc=False,
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Quiet down noisy third-party loggers.
    for noisy in ("urllib3", "httpx", "asyncio", "playwright"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True
