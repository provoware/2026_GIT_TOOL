from __future__ import annotations

import logging
import logging.handlers
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from store import STORE

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "tool.log"


@dataclass
class LoggingState:
    listener: Optional[logging.handlers.QueueListener] = None
    log_queue: Optional[queue.Queue] = None
    configured: bool = False
    log_file: Optional[Path] = None


_STATE = LoggingState()


def resolve_log_path(log_file: Path | str | None = None) -> Path:
    """Liefert einen sicheren Logpfad außerhalb des Projekt-Hauptordners.

    Ohne Angabe wird ``logs/tool.log`` verwendet. Relative Namen werden immer
    unter ``logs/`` abgelegt. Ein absoluter Pfad bleibt möglich, wenn der Nutzer
    für eine Diagnose ausdrücklich ein externes Ziel gewählt hat.
    """

    if log_file is None:
        return DEFAULT_LOG_FILE
    candidate = Path(log_file).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (DEFAULT_LOG_DIR / candidate.name).resolve()


def setup_logging(debug: bool, log_file: Path | str | None = None) -> LoggingState:
    level = logging.DEBUG if debug else logging.INFO
    if _STATE.configured:
        return _STATE

    log_queue: queue.Queue = queue.Queue(-1)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(level)

    log_path = resolve_log_path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    queue_handler = logging.handlers.QueueHandler(log_queue)
    root = logging.getLogger()
    root.handlers = [queue_handler]
    root.setLevel(level)

    listener = logging.handlers.QueueListener(
        log_queue,
        console,
        file_handler,
        respect_handler_level=True,
    )
    listener.start()

    _STATE.listener = listener
    _STATE.log_queue = log_queue
    _STATE.configured = True
    _STATE.log_file = log_path

    STORE.set_logging_state("listener", listener)
    STORE.set_logging_state("level", level)
    STORE.set_logging_state("log_file", str(log_path))
    return _STATE


def shutdown_logging() -> None:
    if _STATE.listener is not None:
        _STATE.listener.stop()
    logging.shutdown()
    _STATE.listener = None
    _STATE.log_queue = None
    _STATE.configured = False
    _STATE.log_file = None
    STORE.set_logging_state("listener", None)
    STORE.set_logging_state("log_file", None)


def get_logger(name: str) -> logging.Logger:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Logger-Name ist leer oder ungültig.")
    return logging.getLogger(name)
