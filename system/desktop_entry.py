#!/usr/bin/env python3
"""Desktop-Entry-Generator für Linux."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from config_utils import ensure_path

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = DEFAULT_ROOT / "config" / "desktop_entry.json"
DEFAULT_ICON_SOURCE = DEFAULT_ROOT / "assets" / "icons" / "provoware.svg"
DEFAULT_OUTPUT = DEFAULT_ROOT / "data" / "desktop_entries" / "2026_git_tool.desktop"


class DesktopEntryError(ValueError):
    """Fehler beim Desktop-Entry."""


@dataclass(frozen=True)
class DesktopEntryConfig:
    app_name: str
    app_id: str
    comment: str
    exec_path: str
    icon_name: str
    categories: List[str]
    keywords: List[str]
    terminal: bool


def load_config(path: Path) -> DesktopEntryConfig:
    ensure_path(path, "config_path", DesktopEntryError)
    if not path.exists():
        raise DesktopEntryError(f"Konfiguration fehlt: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    config = DesktopEntryConfig(
        app_name=data.get("app_name", "").strip(),
        app_id=data.get("app_id", "").strip(),
        comment=data.get("comment", "").strip(),
        exec_path=data.get("exec", "").strip(),
        icon_name=data.get("icon_name", "").strip(),
        categories=list(data.get("categories", [])),
        keywords=list(data.get("keywords", [])),
        terminal=bool(data.get("terminal", False)),
    )
    validate_config(config)
    return config


def validate_config(config: DesktopEntryConfig) -> None:
    if not config.app_name:
        raise DesktopEntryError("App-Name fehlt in der Desktop-Entry-Konfiguration.")
    if not config.app_id:
        raise DesktopEntryError("App-ID fehlt in der Desktop-Entry-Konfiguration.")
    if not config.comment:
        raise DesktopEntryError("Kommentar fehlt in der Desktop-Entry-Konfiguration.")
    if not config.exec_path:
        raise DesktopEntryError("Exec-Pfad fehlt in der Desktop-Entry-Konfiguration.")
    if not config.icon_name:
        raise DesktopEntryError("Icon-Name fehlt in der Desktop-Entry-Konfiguration.")
    if not isinstance(config.categories, list) or not config.categories:
        raise DesktopEntryError("Kategorien fehlen oder sind ungültig.")
    if not isinstance(config.keywords, list):
        raise DesktopEntryError("Keywords sind ungültig.")


def resolve_exec_path(root: Path, exec_path: str) -> str:
    path = Path(exec_path)
    if not path.is_absolute():
        path = root / path
    return str(path)


def build_desktop_entry(config: DesktopEntryConfig, root: Path) -> str:
    exec_value = resolve_exec_path(root, config.exec_path)
    categories = ";".join(config.categories) + ";"
    keywords = ";".join(config.keywords) + ";" if config.keywords else ""
    terminal = "true" if config.terminal else "false"
    lines = [
        "[Desktop Entry]",
        "Type=Application",
        f"Name={config.app_name}",
        f"Comment={config.comment}",
        f"Exec={exec_value}",
        f"Icon={config.icon_name}",
        f"Terminal={terminal}",
        f"Categories={categories}",
        f"Keywords={keywords}",
        f"StartupWMClass={config.app_id}",
    ]
    return "\n".join(lines) + "\n"


def write_desktop_entry(output_path: Path, content: str) -> None:
    ensure_path(output_path, "output_path", DesktopEntryError)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")


def install_desktop_entry(output_path: Path, install_path: Path) -> None:
    ensure_path(output_path, "output_path", DesktopEntryError)
    ensure_path(install_path, "install_path", DesktopEntryError)
    if not output_path.exists():
        raise DesktopEntryError("Desktop-Entry-Datei fehlt. Bitte zuerst erstellen.")
    install_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_path, install_path)


def install_icon(icon_source: Path, icon_name: str, icon_dir: Path) -> Path:
    ensure_path(icon_source, "icon_source", DesktopEntryError)
    ensure_path(icon_dir, "icon_dir", DesktopEntryError)
    if not icon_source.exists():
        raise DesktopEntryError("Icon-Datei fehlt. Bitte Icon bereitstellen.")
    if icon_source.suffix.lower() != ".svg":
        raise DesktopEntryError("Icon-Datei muss eine SVG-Datei sein.")
    icon_dir.mkdir(parents=True, exist_ok=True)
    target = icon_dir / f"{icon_name}.svg"
    shutil.copy2(icon_source, target)
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erstellt einen Linux-Desktop-Entry für das Tool.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Projekt-Root")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Konfig-Datei")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Zielpfad")
    parser.add_argument(
        "--install",
        action="store_true",
        help="Desktop-Entry nach ~/.local/share/applications kopieren",
    )
    parser.add_argument(
        "--install-icon",
        action="store_true",
        help="Icon nach ~/.local/share/icons/hicolor/scalable/apps kopieren",
    )
    parser.add_argument(
        "--icon-source",
        type=Path,
        default=DEFAULT_ICON_SOURCE,
        help="Pfad zur Icon-Datei (SVG)",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("desktop_entry")

    try:
        config = load_config(args.config)
        content = build_desktop_entry(config, args.root)
        write_desktop_entry(args.output, content)
        logger.info("Desktop-Entry erstellt: %s", args.output)

        if args.install:
            install_path = (
                Path.home() / ".local" / "share" / "applications" / (f"{config.app_id}.desktop")
            )
            install_desktop_entry(args.output, install_path)
            logger.info("Desktop-Entry installiert: %s", install_path)

        if args.install_icon:
            icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "scalable" / "apps"
            target = install_icon(args.icon_source, config.icon_name, icon_dir)
            logger.info("Icon installiert: %s", target)
    except (DesktopEntryError, json.JSONDecodeError) as exc:
        logger.error("Desktop-Entry fehlgeschlagen: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
