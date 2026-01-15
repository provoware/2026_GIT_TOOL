#!/usr/bin/env python3
"""One-File-Build (PyInstaller) für das Tool."""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path, load_json

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = DEFAULT_ROOT / "config" / "onefile_package.json"


class OnefileBuildError(ValueError):
    """Fehler beim One-File-Build."""


@dataclass(frozen=True)
class OnefileDataItem:
    source: str
    target: str


@dataclass(frozen=True)
class OnefileConfig:
    name: str
    entry_script: Path
    output_dir: Path
    add_data: List[OnefileDataItem]
    hidden_imports: List[str]
    icon: Path | None


def load_config(path: Path) -> OnefileConfig:
    data = load_json(
        path,
        OnefileBuildError,
        "One-File-Konfiguration fehlt",
        "One-File-Konfiguration ungültig",
    )
    add_data_raw = data.get("add_data", [])
    add_data: List[OnefileDataItem] = []
    if not isinstance(add_data_raw, list):
        raise OnefileBuildError("add_data ist keine Liste.")
    for item in add_data_raw:
        if not isinstance(item, dict):
            raise OnefileBuildError("add_data enthält ungültige Einträge.")
        source = str(item.get("source", "")).strip()
        target = str(item.get("target", "")).strip()
        if not source or not target:
            raise OnefileBuildError("add_data benötigt source und target.")
        add_data.append(OnefileDataItem(source=source, target=target))

    hidden_imports = data.get("hidden_imports", [])
    if not isinstance(hidden_imports, list):
        raise OnefileBuildError("hidden_imports ist keine Liste.")

    icon_value = str(data.get("icon", "")).strip()
    icon_path = Path(icon_value) if icon_value else None

    config = OnefileConfig(
        name=str(data.get("name", "")).strip(),
        entry_script=Path(str(data.get("entry_script", "")).strip()),
        output_dir=Path(str(data.get("output_dir", "dist")).strip()),
        add_data=add_data,
        hidden_imports=[str(item).strip() for item in hidden_imports if str(item).strip()],
        icon=icon_path,
    )
    validate_config(config)
    return config


def validate_config(config: OnefileConfig) -> None:
    if not config.name:
        raise OnefileBuildError("Name für den One-File-Build fehlt.")
    if not config.entry_script:
        raise OnefileBuildError("Entry-Script fehlt.")


def _resolve_repo_path(repo_root: Path, relative: Path) -> Path:
    ensure_path(repo_root, "repo_root", OnefileBuildError)
    ensure_path(relative, "relative", OnefileBuildError)
    if relative.is_absolute():
        return relative
    return repo_root / relative


def _build_add_data_args(repo_root: Path, items: Iterable[OnefileDataItem]) -> List[str]:
    args: List[str] = []
    for item in items:
        source_path = _resolve_repo_path(repo_root, Path(item.source))
        if not source_path.exists():
            raise OnefileBuildError(f"add_data-Quelle fehlt: {source_path}")
        payload = f"{source_path}{os.pathsep}{item.target}"
        args.extend(["--add-data", payload])
    return args


def build_onefile(repo_root: Path, config: OnefileConfig, logger: logging.Logger) -> Path:
    pyinstaller = shutil.which("pyinstaller")
    if not pyinstaller:
        raise OnefileBuildError("PyInstaller fehlt. Bitte 'pyinstaller' installieren.")

    entry_script = _resolve_repo_path(repo_root, config.entry_script)
    if not entry_script.exists():
        raise OnefileBuildError(f"Entry-Script fehlt: {entry_script}")

    output_dir = repo_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    args = [
        pyinstaller,
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        config.name,
        "--distpath",
        str(output_dir),
    ]

    args.extend(_build_add_data_args(repo_root, config.add_data))

    for hidden in config.hidden_imports:
        args.extend(["--hidden-import", hidden])

    if config.icon is not None:
        icon_path = _resolve_repo_path(repo_root, config.icon)
        if icon_path.exists():
            args.extend(["--icon", str(icon_path)])
        else:
            raise OnefileBuildError(f"Icon fehlt: {icon_path}")

    args.append(str(entry_script))

    logger.info("One-File-Build startet: %s", " ".join(args))
    result = subprocess.run(args, check=False)
    if result.returncode != 0:
        raise OnefileBuildError(
            "PyInstaller-Run fehlgeschlagen. Bitte Abhängigkeiten prüfen und erneut starten."
        )

    output_path = output_dir / config.name
    if not output_path.exists():
        raise OnefileBuildError("One-File-Ausgabe fehlt nach dem Build.")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erstellt einen One-File-Build (PyInstaller).",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Projekt-Root")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Konfig-Datei")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger("onefile_builder")

    try:
        config = load_config(args.config)
        output_path = build_onefile(args.root, config, logger)
        logger.info("One-File-Build erstellt: %s", output_path)
    except (OnefileBuildError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        logger.error("One-File-Build fehlgeschlagen: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
