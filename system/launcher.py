#!/usr/bin/env python3
"""Launcher: zeigt alle Tools übersichtlich an."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center
from module_registry import ModuleEntry, ModuleRegistryError, load_registry

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "modules.json"


class LauncherError(Exception):
    """Fehler im Launcher."""


def validate_module_paths(modules: Iterable[ModuleEntry], root: Path) -> None:
    for module in modules:
        if module.enabled and not module.path.exists():
            raise LauncherError(f"Moduldatei fehlt: {module.path}")


def load_modules(config_path: Path, root: Path | None = None) -> List[ModuleEntry]:
    try:
        registry = load_registry(config_path)
    except ModuleRegistryError as exc:
        raise LauncherError(str(exc)) from exc
    modules = registry.entries
    root_dir = root or config_path.resolve().parents[1]
    validate_module_paths(modules, root_dir)
    return modules


def filter_modules(modules: Iterable[ModuleEntry], show_all: bool) -> List[ModuleEntry]:
    filtered = [module for module in modules if show_all or module.enabled]
    return filtered


def render_module_overview(modules: Iterable[ModuleEntry], _root: Path) -> str:
    modules = list(modules)
    if not modules:
        return "Launcher: Keine Module verfügbar.\n"

    lines = ["Launcher: Module im Überblick", ""]
    for index, module in enumerate(modules, start=1):
        status = "aktiv" if module.enabled else "deaktiviert"
        lines.extend(
            [
                f"{index}) {module.name} ({module.module_id})",
                f"   Beschreibung: {module.description}",
                f"   Pfad: {module.path}",
                f"   Status: {status}",
                "",
            ]
        )

    output = "\n".join(lines).rstrip() + "\n"
    if not output.strip():
        raise LauncherError("Launcher-Ausgabe ist leer.")
    return output


def setup_logging(debug: bool) -> None:
    setup_logging_center(debug)


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
    logger = get_logger("launcher")

    try:
        modules = load_modules(args.config)
        modules = filter_modules(modules, args.show_all)
        output = render_module_overview(modules, args.config.resolve().parents[1])
    except LauncherError as exc:
        logger.error("Launcher konnte nicht starten: %s", exc)
        return 2

    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
