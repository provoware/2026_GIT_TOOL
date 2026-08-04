#!/usr/bin/env python3
"""Safe, data-driven bridge from the Provoware Memo web UI to existing modules."""

from __future__ import annotations

import dataclasses
import importlib
import json
import sys
import threading
from pathlib import Path
from typing import Any, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_DIR = PROJECT_ROOT / "system"
for import_root in (PROJECT_ROOT, SYSTEM_DIR):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))


class WebModuleBridgeError(RuntimeError):
    """Controlled module catalog or invocation error."""


def _field(
    name: str,
    label: str,
    field_type: str = "text",
    *,
    required: bool = False,
    options: list[str] | None = None,
    default: Any = None,
    placeholder: str = "",
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": name,
        "label": label,
        "type": field_type,
        "required": required,
    }
    if options:
        result["options"] = options
    if default is not None:
        result["default"] = default
    if placeholder:
        result["placeholder"] = placeholder
    return result


def _action(
    action_id: str,
    label: str,
    *,
    mode: str = "read",
    fields: list[dict[str, Any]] | None = None,
    confirm: str = "",
    description: str = "",
) -> dict[str, Any]:
    return {
        "id": action_id,
        "label": label,
        "mode": mode,
        "fields": fields or [],
        "confirm": confirm,
        "description": description,
    }


MODULE_ACTIONS: dict[str, list[dict[str, Any]]] = {
    "status": [
        _action(
            "status",
            "Status prüfen",
            fields=[_field("request", "Prüftext", default="Weboberfläche")],
        )
    ],
    "beispiel_modul": [
        _action(
            "echo",
            "Beispiel ausführen",
            fields=[_field("text", "Text", default="Hallo")],
        )
    ],
    "todo_kalender": [
        _action("list", "Aufgaben laden"),
        _action(
            "calendar",
            "Kalender laden",
            fields=[
                _field(
                    "view",
                    "Ansicht",
                    "select",
                    options=["jahr", "monat", "woche"],
                    default="monat",
                ),
                _field("reference_date", "Bezugsdatum", "date"),
            ],
        ),
        _action(
            "add",
            "Aufgabe anlegen",
            mode="write",
            fields=[
                _field("title", "Titel", required=True),
                _field("planned_date", "Geplantes Datum", "date", required=True),
                _field("notes", "Hinweise", "textarea"),
            ],
        ),
        _action(
            "complete",
            "Aufgabe erledigen",
            mode="write",
            fields=[
                _field("id", "Aufgaben-ID", required=True),
                _field("done_date", "Erledigt am", "date"),
            ],
        ),
        _action("sync_todo_txt", "todo.txt synchronisieren", mode="write"),
    ],
    "notiz_editor": [
        _action("list_notes", "Notizen laden"),
        _action("list_templates", "Vorlagen laden"),
        _action("dashboard", "Notiz-Statistik"),
        _action(
            "create_note",
            "Notiz anlegen",
            mode="write",
            fields=[
                _field("title", "Titel", required=True),
                _field("body", "Inhalt", "textarea", required=True),
                _field("tags", "Tags", "list", placeholder="Idee, Recherche"),
                _field("template_id", "Vorlagen-ID"),
            ],
        ),
        _action(
            "update_note",
            "Notiz bearbeiten",
            mode="write",
            fields=[
                _field("id", "Notiz-ID", required=True),
                _field("title", "Titel"),
                _field("body", "Inhalt", "textarea"),
                _field("tags", "Tags", "list"),
            ],
        ),
        _action(
            "toggle_favorite",
            "Favorit umschalten",
            mode="write",
            fields=[_field("id", "Notiz-ID", required=True)],
        ),
    ],
    "charakter_modul": [
        _action("list_characters", "Charaktere laden"),
        _action("list_templates", "Charaktervorlagen laden"),
        _action("dashboard", "Charakter-Statistik"),
        _action(
            "create_character",
            "Charakter anlegen",
            mode="write",
            fields=[
                _field("name", "Name", required=True),
                _field("role", "Rolle", required=True),
                _field("archetype", "Archetyp", required=True),
                _field("biography", "Biografie", "textarea"),
                _field("appearance", "Aussehen", "textarea"),
                _field("traits", "Eigenschaften", "list"),
                _field("goals", "Ziele", "list"),
                _field("conflicts", "Konflikte", "list"),
                _field("relationships", "Beziehungen", "list"),
                _field("voice_notes", "Stimme/Notizen", "textarea"),
                _field("tags", "Tags", "list"),
                _field("template_id", "Vorlagen-ID"),
            ],
        ),
        _action(
            "update_character",
            "Charakter bearbeiten",
            mode="write",
            fields=[
                _field("id", "Charakter-ID", required=True),
                _field("name", "Name"),
                _field("role", "Rolle"),
                _field("archetype", "Archetyp"),
            ],
        ),
        _action(
            "toggle_favorite",
            "Favorit umschalten",
            mode="write",
            fields=[_field("id", "Charakter-ID", required=True)],
        ),
    ],
    "download_aufraeumen": [
        _action(
            "scan",
            "Downloads scannen",
            fields=[
                _field("download_path", "Download-Ordner", "path", default="~/Downloads"),
                _field("include_hidden", "Versteckte Dateien", "checkbox", default=False),
                _field("max_files", "Maximale Dateien", "number", default=5000),
            ],
        ),
        _action(
            "build_plan",
            "Aufräumplan erstellen",
            fields=[
                _field("items", "Scan-Ergebnis (JSON)", "json", required=True),
                _field("selected", "Ausgewählte Pfade", "list"),
            ],
        ),
        _action(
            "apply_plan",
            "Aufräumplan anwenden",
            mode="write",
            fields=[
                _field("operations", "Operationen (JSON)", "json", required=True),
                _field("dry_run", "Nur simulieren", "checkbox", default=True),
            ],
            confirm="Der Aufräumplan kann Dateien verschieben. Fortfahren?",
        ),
        _action(
            "undo",
            "Letzte Aktion rückgängig",
            mode="write",
            confirm="Letzte Aufräumaktion wirklich rückgängig machen?",
        ),
        _action("history", "Historie laden"),
    ],
    "datei_suche": [
        _action(
            "search",
            "Dateien suchen",
            fields=[
                _field("query", "Suchfilter (JSON)", "json", default={"name_contains": ""}),
            ],
        ),
        _action(
            "organize",
            "Dateien organisieren",
            mode="write",
            fields=[
                _field("items", "Dateien (JSON-Liste)", "json", required=True),
                _field("target_dir", "Zielordner", "path", required=True),
                _field("mode", "Modus", "select", options=["move", "copy"], default="move"),
            ],
            confirm="Ausgewählte Dateien wirklich organisieren?",
        ),
        _action(
            "undo",
            "Letzte Organisation rückgängig",
            mode="write",
            confirm="Letzte Dateiaktion rückgängig machen?",
        ),
        _action("history", "Historie laden"),
    ],
    "datei_manager": [
        _action("list_favorites", "Favoriten laden"),
        _action("list_tags", "Tags laden"),
        _action(
            "quick_rename",
            "Datei schnell umbenennen",
            mode="write",
            fields=[
                _field("path", "Dateipfad", "path", required=True),
                _field("new_name", "Neuer Name", required=True),
                _field("dry_run", "Nur simulieren", "checkbox", default=True),
            ],
            confirm="Datei wirklich umbenennen?",
        ),
        _action(
            "tag_items",
            "Dateien taggen",
            mode="write",
            fields=[
                _field("paths", "Dateipfade", "list", required=True),
                _field("tags", "Tags", "list", required=True),
            ],
        ),
        _action(
            "toggle_favorite",
            "Favorit umschalten",
            mode="write",
            fields=[_field("path", "Dateipfad", "path", required=True)],
        ),
    ],
    "archiv_manager": [
        _action("list_archives", "Archive laden"),
        _action(
            "list_entries",
            "Einträge laden",
            fields=[
                _field("archive", "Archivkennung", required=True),
                _field("query", "Suche"),
                _field("category", "Kategorie"),
            ],
        ),
        _action(
            "add_entries",
            "Einträge hinzufügen",
            mode="write",
            fields=[
                _field("archive", "Archivkennung", required=True),
                _field("value", "Inhalt", "textarea", required=True),
                _field("category", "Kategorie", default="Allgemein"),
                _field(
                    "apply_spelling",
                    "Rechtschreibvorschläge anwenden",
                    "checkbox",
                    default=False,
                ),
            ],
        ),
        _action(
            "create_archive",
            "Archiv anlegen",
            mode="write",
            fields=[
                _field("name", "Name", required=True),
                _field("description", "Beschreibung", "textarea"),
                _field(
                    "split_on_comma",
                    "Kommas trennen Einträge",
                    "checkbox",
                    default=True,
                ),
            ],
        ),
        _action(
            "update_entry",
            "Eintrag bearbeiten",
            mode="write",
            fields=[
                _field("entry_id", "Eintrags-ID", "number", required=True),
                _field("value", "Inhalt", "textarea", required=True),
                _field("category", "Kategorie", default="Allgemein"),
            ],
        ),
        _action(
            "delete_entry",
            "Eintrag löschen",
            mode="write",
            fields=[_field("entry_id", "Eintrags-ID", "number", required=True)],
            confirm="Archiveintrag wirklich löschen?",
        ),
    ],
    "media_wavesurfer": [
        _action("list_features", "Funktionen laden"),
        _action("list_markers", "Marker laden"),
        _action("list_regions", "Regionen laden"),
        _action(
            "add_marker",
            "Marker setzen",
            mode="write",
            fields=[
                _field("time", "Zeit in Sekunden", "number", required=True),
                _field("label", "Bezeichnung"),
                _field("color", "Farbe", "color", default="#38bdf8"),
            ],
        ),
        _action(
            "add_region",
            "Region anlegen",
            mode="write",
            fields=[
                _field("start", "Start", "number", required=True),
                _field("end", "Ende", "number", required=True),
                _field("label", "Bezeichnung"),
                _field("color", "Farbe", "color", default="#22c55e"),
            ],
        ),
        _action(
            "set_minimap",
            "Minimap anpassen",
            mode="write",
            fields=[
                _field("height", "Höhe", "number", default=48),
                _field("zoom", "Zoom", "number", default=1),
                _field("color", "Farbe", "color", default="#38bdf8"),
            ],
        ),
        _action(
            "export_profile",
            "Exportprofil wählen",
            mode="write",
            fields=[
                _field(
                    "profile_id",
                    "Profil",
                    "select",
                    options=["wav_44100", "mp3_high"],
                    required=True,
                )
            ],
        ),
    ],
    "media_ffmpeg_wrapper": [
        _action("list_presets", "Presets laden"),
        _action(
            "build_command",
            "FFmpeg-Befehl erzeugen",
            mode="write",
            fields=[
                _field("input_path", "Eingabedatei", "path", required=True),
                _field(
                    "preset_id",
                    "Preset",
                    "select",
                    options=["mp3_standard", "wav_master"],
                    required=True,
                ),
                _field("output_name", "Ausgabename"),
            ],
        ),
        _action(
            "simulate_progress",
            "Fortschritt simulieren",
            mode="write",
            fields=[_field("job_id", "Job-ID", required=True)],
        ),
        _action("get_job", "Job laden", fields=[_field("job_id", "Job-ID", required=True)]),
    ],
    "profil_manager": [
        _action("list_profiles", "Profile laden"),
        _action("get_active", "Aktives Profil laden"),
        _action(
            "create_profile",
            "Profil anlegen",
            mode="write",
            fields=[_field("name", "Profilname", required=True)],
        ),
        _action(
            "set_active",
            "Profil aktivieren",
            mode="write",
            fields=[_field("name", "Profilname", required=True)],
        ),
        _action(
            "rename_profile",
            "Profil umbenennen",
            mode="write",
            fields=[
                _field("from", "Bisheriger Name", required=True),
                _field("to", "Neuer Name", required=True),
            ],
        ),
        _action(
            "delete_profile",
            "Profil löschen",
            mode="write",
            fields=[_field("name", "Profilname", required=True)],
            confirm="Profil und zugehörigen Projektordner wirklich löschen?",
        ),
    ],
}

GROUPS = {
    "status": "System",
    "beispiel_modul": "System",
    "notiz_editor": "Kreativ & Organisation",
    "todo_kalender": "Kreativ & Organisation",
    "charakter_modul": "Kreativ & Organisation",
    "archiv_manager": "Kreativ & Organisation",
    "datei_manager": "Dateien",
    "datei_suche": "Dateien",
    "download_aufraeumen": "Dateien",
    "media_wavesurfer": "Medien",
    "media_ffmpeg_wrapper": "Medien",
    "profil_manager": "Projekte",
}

DEFAULT_ACTIONS = {
    "status": "status",
    "beispiel_modul": "echo",
    "todo_kalender": "list",
    "notiz_editor": "list_notes",
    "charakter_modul": "list_characters",
    "download_aufraeumen": "history",
    "datei_suche": "history",
    "datei_manager": "list_favorites",
    "archiv_manager": "list_archives",
    "media_wavesurfer": "list_features",
    "media_ffmpeg_wrapper": "list_presets",
    "profil_manager": "list_profiles",
}


class WebModuleBridge:
    """Loads and invokes only registered, explicitly allowlisted module actions."""

    def __init__(self, root: Path = PROJECT_ROOT) -> None:
        self.root = root.resolve()
        self._lock = threading.RLock()
        self._registry = self._load_registry()
        self._loaded: dict[str, Any] = {}

    def _load_registry(self) -> dict[str, dict[str, Any]]:
        path = self.root / "config" / "modules.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WebModuleBridgeError(f"Modulregister kann nicht gelesen werden: {exc}") from exc
        modules = payload.get("modules")
        if not isinstance(modules, list):
            raise WebModuleBridgeError("Modulregister enthält keine Modulliste.")
        registry: dict[str, dict[str, Any]] = {}
        for raw in modules:
            if not isinstance(raw, Mapping):
                continue
            module_id = str(raw.get("id", "")).strip()
            if not module_id or module_id not in MODULE_ACTIONS:
                continue
            registry[module_id] = dict(raw)
        return registry

    def catalog(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for module_id, descriptor in self._registry.items():
            manifest_path = self.root / descriptor["path"] / "manifest.json"
            manifest: dict[str, Any] = {}
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
            result.append(
                {
                    "id": module_id,
                    "name": descriptor.get("name", module_id),
                    "description": descriptor.get("description", ""),
                    "enabled": bool(descriptor.get("enabled", True)),
                    "group": GROUPS.get(module_id, "Weitere"),
                    "version": manifest.get("version", ""),
                    "permissions": manifest.get("permissions", []),
                    "actions": MODULE_ACTIONS[module_id],
                    "default_action": DEFAULT_ACTIONS[module_id],
                }
            )
        return result

    def invoke(
        self, module_id: str, action_id: str, payload: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        with self._lock:
            descriptor = self._registry.get(module_id)
            if descriptor is None or not descriptor.get("enabled", True):
                raise WebModuleBridgeError(f"Modul ist nicht verfügbar: {module_id}")
            allowed = {action["id"] for action in MODULE_ACTIONS[module_id]}
            if action_id not in allowed:
                raise WebModuleBridgeError(
                    f"Aktion ist für {module_id} nicht freigegeben: {action_id}"
                )
            request = dict(payload or {})
            if module_id == "status":
                request.setdefault("request", "Weboberfläche")
            elif module_id == "beispiel_modul":
                request.setdefault("text", "Weboberfläche")
            else:
                request["action"] = action_id
            module = self._load_module(module_id, descriptor)
            try:
                response = module.run(request)
            except Exception as exc:  # noqa: BLE001
                raise WebModuleBridgeError(f"{descriptor.get('name', module_id)}: {exc}") from exc
            return self._normalize_response(response)

    def snapshots(self) -> dict[str, Any]:
        snapshots: dict[str, Any] = {}
        for module_id, action_id in DEFAULT_ACTIONS.items():
            if module_id not in self._registry:
                continue
            try:
                snapshots[module_id] = self.invoke(module_id, action_id, {})
            except WebModuleBridgeError as exc:
                snapshots[module_id] = {
                    "status": "error",
                    "message": str(exc),
                    "data": {},
                }
        return snapshots

    def _load_module(self, module_id: str, descriptor: Mapping[str, Any]) -> Any:
        cached = self._loaded.get(module_id)
        if cached is not None:
            return cached
        manifest_path = self.root / str(descriptor["path"]) / "manifest.json"
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WebModuleBridgeError(f"Manifest ist nicht lesbar: {manifest_path}") from exc
        entry_name = str(manifest.get("entry", "module.py"))
        module_name = f"modules.{module_id}.{Path(entry_name).stem}"
        try:
            loaded = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001
            raise WebModuleBridgeError(
                f"Modul kann nicht geladen werden: {module_id}: {exc}"
            ) from exc
        if not callable(getattr(loaded, "run", None)):
            raise WebModuleBridgeError(f"Modul besitzt keine ausführbare run-Funktion: {module_id}")
        self._loaded[module_id] = loaded
        return loaded

    @staticmethod
    def _normalize_response(response: Any) -> dict[str, Any]:
        if dataclasses.is_dataclass(response):
            response = dataclasses.asdict(response)
        if isinstance(response, Mapping):
            normalized = dict(response)
            status = str(normalized.get("status", "ok"))
            if status not in {"ok", "fehler", "error"}:
                status = "ok"
            normalized["status"] = "ok" if status == "ok" else "error"
            normalized.setdefault("message", "Aktion ausgeführt.")
            if "data" not in normalized:
                if "payload" in normalized:
                    normalized["data"] = normalized.get("payload")
                else:
                    normalized["data"] = {
                        key: value
                        for key, value in normalized.items()
                        if key not in {"status", "message", "ui"}
                    }
            return normalized
        return {"status": "ok", "message": "Aktion ausgeführt.", "data": response}
