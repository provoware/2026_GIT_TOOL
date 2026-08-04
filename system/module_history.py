"""Kleine, UI-unabhängige Änderungshistorie für Module."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class ModuleHistoryEntry:
    version: str
    status: str
    message: str
    changed_at: str


def create_history_entry(version: str, status: str, message: str) -> ModuleHistoryEntry:
    values = {"version": version, "status": status, "message": message}
    if any(not isinstance(value, str) or not value.strip() for value in values.values()):
        raise ValueError("Versionsverlauf enthält leere oder ungültige Angaben.")
    return ModuleHistoryEntry(
        version=version.strip(),
        status=status.strip(),
        message=message.strip(),
        changed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )


def format_history(entries: list[ModuleHistoryEntry]) -> str:
    if not entries:
        return "Noch keine Änderungen in dieser Sitzung."
    return "\n".join(
        f"{entry.changed_at} · Version {entry.version} · {entry.status}: {entry.message}"
        for entry in reversed(entries)
    )
