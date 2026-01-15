"""Globales Event-/Signal-System für Module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from logging_center import get_logger


class EventBusError(ValueError):
    """Fehler im Event-Bus."""


Subscriber = Callable[["Event"], None]


@dataclass(frozen=True)
class Event:
    name: str
    payload: Dict[str, Any]
    source: Optional[str]
    created_at: str


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EventBusError(f"{label} ist leer oder ungültig.")
    return value.strip()


def _require_payload(value: object) -> Dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise EventBusError("payload ist kein Objekt (dict).")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Subscriber]] = {}
        self._logger = get_logger("event_bus")

    def subscribe(self, event_name: str, handler: Subscriber) -> None:
        clean_name = _require_text(event_name, "event_name")
        if not callable(handler):
            raise EventBusError("handler ist nicht aufrufbar.")
        self._subscribers.setdefault(clean_name, []).append(handler)

    def unsubscribe(self, event_name: str, handler: Subscriber) -> None:
        clean_name = _require_text(event_name, "event_name")
        if not callable(handler):
            raise EventBusError("handler ist nicht aufrufbar.")
        handlers = self._subscribers.get(clean_name, [])
        if handler in handlers:
            handlers.remove(handler)
        if not handlers and clean_name in self._subscribers:
            self._subscribers.pop(clean_name, None)

    def emit(
        self,
        event_name: str,
        payload: object = None,
        source: Optional[str] = None,
    ) -> Event:
        clean_name = _require_text(event_name, "event_name")
        clean_payload = _require_payload(payload)
        clean_source = source.strip() if isinstance(source, str) and source.strip() else None
        event = Event(
            name=clean_name,
            payload=clean_payload,
            source=clean_source,
            created_at=_utc_now(),
        )
        handlers = list(self._subscribers.get(clean_name, []))
        handlers.extend(self._subscribers.get("*", []))
        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                self._logger.error("Event-Bus: Handler-Fehler bei '%s': %s", clean_name, exc)
        return event


EVENT_BUS = EventBus()
