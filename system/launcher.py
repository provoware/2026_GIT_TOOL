#!/usr/bin/env python3
"""Launcher: zeigt alle Tools übersichtlich an."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import config_utils

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"


class LauncherError(Exception):
    """Fehler im Launcher."""


@dataclass(frozen=True)
class ModuleEntry:
    module_id: str
    name: str
    path: str
    enabled: bool
    description: str


def resolve_module_path(root: Path, module_path: str) -> Path:
    candidate = Path(module_path)
    return candidate if candidate.is_absolute() else root / candidate


def validate_module_entry(entry: dict) -> ModuleEntry:
    if not isinstance(entry, dict):
        raise LauncherError("Modul-Eintrag ist kein Objekt.")

    module_id = str(entry.get("id", "")).strip()
    name = str(entry.get("name", "")).strip()
    path = str(entry.get("path", "")).strip()
    description = str(entry.get("description", "")).strip()
    enabled = entry.get("enabled")

    if not module_id:
        raise LauncherError("Modul-Eintrag: id fehlt.")
    if not name:
        raise LauncherError("Modul-Eintrag: name fehlt.")
    if not path:
        raise LauncherError("Modul-Eintrag: path fehlt.")
    if not description:
        raise LauncherError("Modul-Eintrag: description fehlt.")
    if not isinstance(enabled, bool):
        raise LauncherError("Modul-Eintrag: enabled muss true/false sein.")

    return ModuleEntry(
        module_id=module_id,
        name=name,
        path=path,
        enabled=enabled,
        description=description,
    )


def validate_module_paths(modules: Iterable[ModuleEntry], root: Path) -> None:
    for module in modules:
        module_path = resolve_module_path(root, module.path)
        if module.enabled and not module_path.exists():
            raise LauncherError(f"Moduldatei fehlt: {module_path}")


def load_modules(config_path: Path, root: Path | None = None) -> List[ModuleEntry]:
    config_utils.ensure_path(config_path, "config_path", LauncherError)
    data = config_utils.load_json(
        config_path,
        LauncherError,
        "Konfiguration fehlt",
        "Konfiguration ist kein gültiges JSON",
    )
    raw_modules = data.get("modules")
    if not isinstance(raw_modules, list) or not raw_modules:
        raise LauncherError("Keine Module in der Konfiguration gefunden.")

    modules: List[ModuleEntry] = []
    seen_ids: set[str] = set()
    for entry in raw_modules:
        module = validate_module_entry(entry)
        if module.module_id in seen_ids:
            raise LauncherError(f"Modul-ID doppelt vorhanden: {module.module_id}")
        seen_ids.add(module.module_id)
        modules.append(module)

    root_dir = root or config_path.resolve().parents[1]
    validate_module_paths(modules, root_dir)
    return modules


def filter_modules(modules: Iterable[ModuleEntry], show_all: bool) -> List[ModuleEntry]:
    filtered = [module for module in modules if show_all or module.enabled]
    return filtered


def render_module_overview(modules: Iterable[ModuleEntry], root: Path) -> str:
    modules = list(modules)
    if not modules:
        return "Launcher: Keine Module verfügbar.\n"

    lines = ["Launcher: Module im Überblick", ""]
    for index, module in enumerate(modules, start=1):
        status = "aktiv" if module.enabled else "deaktiviert"
        module_path = resolve_module_path(root, module.path)
        lines.extend(
            [
                f"{index}) {module.name} ({module.module_id})",
                f"   Beschreibung: {module.description}",
                f"   Pfad: {module_path}",
                f"   Status: {status}",
                "",
            ]
        )

    output = "\n".join(lines).rstrip() + "\n"
    if not output.strip():
        raise LauncherError("Launcher-Ausgabe ist leer.")
    return output


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Launcher: Zeigt alle Tools übersichtlich an.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Pfad zur Modul-Liste (JSON).",
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Zeigt auch deaktivierte Module an.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Debug-Modus aktivieren.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging(args.debug)

    try:
        modules = load_modules(args.config)
        modules = filter_modules(modules, args.show_all)
        output = render_module_overview(modules, args.config.resolve().parents[1])
    except LauncherError as exc:
        logging.error("Launcher konnte nicht starten: %s", exc)
        return 2

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
