from __future__ import annotations

import logging
import logging.handlers
import queue
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from store import STORE


@dataclass
class LoggingState:
    listener: Optional[logging.handlers.QueueListener] = None
    log_queue: Optional[queue.Queue] = None
    configured: bool = False


_STATE = LoggingState()


def setup_logging(debug: bool, log_file: Path | None = None) -> LoggingState:
    level = logging.DEBUG if debug else logging.INFO
    if _STATE.configured:
        return _STATE

    log_queue: queue.Queue = queue.Queue(-1)
    formatter = logging.Formatter("%(levelname)s: %(message)s")

    handlers: list[logging.Handler] = []
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console.setLevel(level)
    handlers.append(console)

    if log_file is not None:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(level)
        handlers.append(file_handler)

    queue_handler = logging.handlers.QueueHandler(log_queue)
    root = logging.getLogger()
    root.handlers = [queue_handler]
    root.setLevel(level)

    listener = logging.handlers.QueueListener(log_queue, *handlers, respect_handler_level=True)
    listener.start()

    _STATE.listener = listener
    _STATE.log_queue = log_queue
    _STATE.configured = True

    STORE.set_logging_state("listener", listener)
    STORE.set_logging_state("level", level)
    return _STATE


def shutdown_logging() -> None:
    if _STATE.listener is not None:
        _STATE.listener.stop()
    _STATE.listener = None
    _STATE.log_queue = None
    _STATE.configured = False
    STORE.set_logging_state("listener", None)


def get_logger(name: str) -> logging.Logger:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Logger-Name ist leer oder ungültig.")
    return logging.getLogger(name)
