"""
logging/logger.py

Aegis Logger.

Structured JSON logger for all pipeline events.
Writes to:
    logs/aegis.log     — all events (INFO+)
    logs/attacks.log   — BLOCK + WARN only

Usage:
    from logging.logger import get_logger, log_event

    logger = get_logger(__name__)
    log_event(log_record)
"""

import json
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from config import LOGS_DIR, LOG_LEVEL

# ── Log file paths ────────────────────────────────────────
AEGIS_LOG_PATH   = LOGS_DIR / "aegis.log"
ATTACKS_LOG_PATH = LOGS_DIR / "attacks.log"

# ── Setup flag ────────────────────────────────────────────
_setup_done = False


# ── JSON formatter ────────────────────────────────────────
class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


# ── Setup ─────────────────────────────────────────────────
def setup_logging() -> None:
    """
    Configure root logger with:
        - Console handler (INFO+)
        - aegis.log rotating file handler (INFO+)
        - attacks.log rotating file handler (WARNING+ only)
    Safe to call multiple times.
    """
    global _setup_done
    if _setup_done:
        return

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    root    = logging.getLogger()
    level   = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    root.setLevel(level)

    # ── Console ───────────────────────────────────────────
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(console)

    # ── aegis.log — all events ────────────────────────────
    aegis_handler = logging.handlers.RotatingFileHandler(
        AEGIS_LOG_PATH,
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    aegis_handler.setLevel(level)
    aegis_handler.setFormatter(JSONFormatter())
    root.addHandler(aegis_handler)

    # ── attacks.log — BLOCK + WARN only ──────────────────
    attacks_handler = logging.handlers.RotatingFileHandler(
        ATTACKS_LOG_PATH,
        maxBytes=10 * 1024 * 1024,   # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    attacks_handler.setLevel(logging.WARNING)
    attacks_handler.setFormatter(JSONFormatter())
    root.addHandler(attacks_handler)

    _setup_done = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.
    Ensures logging is set up before returning.

    Usage:
        logger = get_logger(__name__)
        logger.info("message")
    """
    setup_logging()
    return logging.getLogger(name)


# ── Structured event logging ──────────────────────────────
def log_event(record: dict) -> None:
    """
    Write a structured pipeline event to aegis.log.
    BLOCK/WARN events also go to attacks.log via WARNING level.

    Args:
        record: log_record dict from Layer 3 or Layer 4.
    """
    if not record:
        return

    setup_logging()
    logger  = logging.getLogger("aegis.events")
    verdict = record.get("verdict", "")
    layer   = record.get("layer", "")
    message = json.dumps(record, ensure_ascii=False)

    if verdict == "BLOCK":
        logger.warning(f"[{layer}] BLOCK | {message}")
    elif verdict == "WARN":
        logger.warning(f"[{layer}] WARN  | {message}")
    else:
        logger.info(f"[{layer}] {message}")