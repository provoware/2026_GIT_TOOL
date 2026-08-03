"""Modulvertrag und GUI-Einstieg für die gemeinsame Archiv-Verwaltung."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

MODULE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = MODULE_DIR.parents[1]
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))

try:
    from .service import ArchiveService, ArchiveServiceError, ArchiveStorageError
    from .window import open_window as _open_window
except ImportError:
    from service import ArchiveService, ArchiveServiceError, ArchiveStorageError
    from window import open_window as _open_window

DEFAULT_DATABASE = PROJECT_ROOT / "data" / "archiv_manager.sqlite3"
_window_instance = None
_service_instance: ArchiveService | None = None


def _database_path(context: dict[str, Any] | None = None) -> Path:
    explicit = (context or {}).get("database_path")
    return Path(explicit or os.environ.get("GENREARCHIV_ARCHIVE_DB", DEFAULT_DATABASE)).expanduser()


def _service(context: dict[str, Any] | None = None) -> ArchiveService:
    global _service_instance
    path = _database_path(context)
    if _service_instance is None or _service_instance.database_path != path:
        _service_instance = ArchiveService(path, logger=logging.getLogger("archiv_manager"))
    return _service_instance


def validateInput(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return False
    return payload.get("action", "list_archives") in {
        "list_archives", "list_entries", "add_entries", "create_archive",
        "update_archive", "update_entry", "delete_entry",
    }


def validateOutput(payload: Any) -> bool:
    return (
        isinstance(payload, dict)
        and payload.get("status") in {"ok", "warn", "error"}
        and isinstance(payload.get("message"), str)
        and isinstance(payload.get("payload"), dict)
    )


def _archive_payload(archive) -> dict[str, Any]:
    return {
        "id": archive.id,
        "slug": archive.slug,
        "name": archive.name,
        "description": archive.description,
        "split_on_comma": archive.split_on_comma,
        "is_default": archive.is_default,
    }


def _entry_payload(entry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "archive_id": entry.archive_id,
        "category": entry.category,
        "value": entry.value,
        "source": entry.source,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
    }


def run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    request = dict(payload or {"action": "list_archives"})
    if not validateInput(request):
        return {"status": "error", "message": "Ungültige Modul-Eingabe.", "payload": {}}
    service = _service(request)
    action = request.get("action", "list_archives")
    try:
        if action == "list_archives":
            result = {
                "status": "ok", "message": "Archive geladen.",
                "payload": {"archives": [_archive_payload(item) for item in service.list_archives()]},
            }
        elif action == "list_entries":
            entries = service.list_entries(
                request["archive"], category=request.get("category"), query=str(request.get("query", ""))
            )
            result = {
                "status": "ok", "message": "Archiveinträge geladen.",
                "payload": {"entries": [_entry_payload(item) for item in entries]},
            }
        elif action == "add_entries":
            summary = service.add_text(
                request["archive"], str(request.get("value", "")),
                category=str(request.get("category", "Allgemein")),
                source=str(request.get("source", "module")),
                apply_spelling=bool(request.get("apply_spelling", False)),
            )
            result = {
                "status": "ok", "message": "Archiveingabe verarbeitet.",
                "payload": {
                    "archive": _archive_payload(summary.archive),
                    "inserted": [_entry_payload(item) for item in summary.inserted],
                    "duplicates": list(summary.duplicates),
                },
            }
        elif action == "create_archive":
            archive = service.create_archive(
                str(request.get("name", "")), str(request.get("description", "")),
                split_on_comma=bool(request.get("split_on_comma", True)),
                source=str(request.get("source", "module")),
            )
            result = {"status": "ok", "message": "Archiv angelegt.", "payload": {"archive": _archive_payload(archive)}}
        elif action == "update_archive":
            archive = service.update_archive(
                int(request["archive_id"]), name=request.get("name"),
                description=request.get("description"), split_on_comma=request.get("split_on_comma"),
                source=str(request.get("source", "module")),
            )
            result = {"status": "ok", "message": "Archiv aktualisiert.", "payload": {"archive": _archive_payload(archive)}}
        elif action == "update_entry":
            entry = service.update_entry(
                int(request["entry_id"]), value=str(request.get("value", "")),
                category=str(request.get("category", "Allgemein")),
                source=str(request.get("source", "module")),
            )
            result = {"status": "ok", "message": "Archiveintrag aktualisiert.", "payload": {"entry": _entry_payload(entry)}}
        else:
            service.delete_entry(int(request["entry_id"]), source=str(request.get("source", "module")))
            result = {"status": "ok", "message": "Archiveintrag gelöscht.", "payload": {}}
    except (KeyError, TypeError, ValueError, ArchiveServiceError, ArchiveStorageError) as exc:
        result = {"status": "error", "message": str(exc), "payload": {}}
    if not validateOutput(result):
        raise ValueError("Interner Ausgabevertrag des Archiv-Moduls ist ungültig.")
    return result


def _default_parent():
    try:
        import tkinter as tk
    except ImportError:
        return None
    parent = getattr(tk, "_default_root", None)
    if parent is None:
        return None
    try:
        return parent if parent.winfo_exists() else None
    except Exception:
        return None


def open_ui(parent=None, *, database_path: Path | str | None = None):
    global _window_instance
    if _window_instance is not None:
        try:
            if _window_instance.root.winfo_exists():
                _window_instance.root.deiconify()
                _window_instance.root.lift()
                _window_instance.root.focus_force()
                return _window_instance
        except Exception:
            _window_instance = None
    _window_instance = _open_window(
        parent or _default_parent(),
        database_path=database_path or _database_path(),
        logger=logging.getLogger("archiv_manager"),
    )
    return _window_instance


def init(context: dict[str, Any] | None = None) -> dict[str, Any]:
    service = _service(context)
    headless = bool((context or {}).get("headless", False))
    if not headless:
        parent = (context or {}).get("ui_parent") or _default_parent()
        if parent is not None:
            parent.after_idle(lambda: open_ui(parent, database_path=service.database_path))
    return {
        "status": "ok", "message": "Archiv-Modul initialisiert.",
        "payload": {"database_path": str(service.database_path), "headless": headless},
    }


def exit(_context: Any = None) -> dict[str, Any]:
    global _window_instance
    if _window_instance is not None:
        try:
            if _window_instance.root.winfo_exists():
                _window_instance.root.destroy()
        except Exception:
            pass
        _window_instance = None
    return {"status": "ok", "message": "Archiv-Modul beendet.", "payload": {}}
