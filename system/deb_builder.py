#!/usr/bin/env python3
"""Deb-Paket Builder für das Tool."""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path
from desktop_entry import build_desktop_entry
from desktop_entry import load_config as load_desktop_config

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = DEFAULT_ROOT / "config" / "deb_package.json"


class DebBuilderError(ValueError):
    """Fehler beim Deb-Build."""


@dataclass(frozen=True)
class DebPackageConfig:
    package_name: str
    version: str
    maintainer: str
    description: str
    architecture: str
    depends: List[str]
    install_root: str
    desktop_entry_config: Path
    icon_source: Path
    exclude_paths: List[str]
    output_dir: Path


def load_config(path: Path) -> DebPackageConfig:
    ensure_path(path, "config_path", DebBuilderError)
    if not path.exists():
        raise DebBuilderError(f"Konfiguration fehlt: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    config = DebPackageConfig(
        package_name=data.get("package_name", "").strip(),
        version=data.get("version", "").strip(),
        maintainer=data.get("maintainer", "").strip(),
        description=data.get("description", "").strip(),
        architecture=data.get("architecture", "").strip(),
        depends=list(data.get("depends", [])),
        install_root=data.get("install_root", "").strip(),
        desktop_entry_config=Path(data.get("desktop_entry_config", "")),
        icon_source=Path(data.get("icon_source", "")),
        exclude_paths=list(data.get("exclude_paths", [])),
        output_dir=Path(data.get("output_dir", "dist")),
    )
    validate_config(config)
    return config


def validate_config(config: DebPackageConfig) -> None:
    if not config.package_name:
        raise DebBuilderError("Paketname fehlt in der Deb-Konfiguration.")
    if not config.version:
        raise DebBuilderError("Version fehlt in der Deb-Konfiguration.")
    if not config.maintainer:
        raise DebBuilderError("Maintainer fehlt in der Deb-Konfiguration.")
    if not config.description:
        raise DebBuilderError("Beschreibung fehlt in der Deb-Konfiguration.")
    if not config.architecture:
        raise DebBuilderError("Architektur fehlt in der Deb-Konfiguration.")
    if not config.install_root:
        raise DebBuilderError("Installationsziel fehlt in der Deb-Konfiguration.")
    if not config.desktop_entry_config:
        raise DebBuilderError("Desktop-Entry-Konfiguration fehlt.")
    if not config.icon_source:
        raise DebBuilderError("Icon-Quelle fehlt.")


def build_control_content(config: DebPackageConfig) -> str:
    depends = ", ".join(config.depends) if config.depends else ""
    lines = [
        f"Package: {config.package_name}",
        f"Version: {config.version}",
        "Section: utils",
        "Priority: optional",
        f"Architecture: {config.architecture}",
        f"Maintainer: {config.maintainer}",
    ]
    if depends:
        lines.append(f"Depends: {depends}")
    lines.append(f"Description: {config.description}")
    return "\n".join(lines) + "\n"


def should_exclude(relative_path: Path, exclude_paths: Iterable[str]) -> bool:
    rel_posix = relative_path.as_posix()
    for exclude in exclude_paths:
        if rel_posix == exclude or rel_posix.startswith(f"{exclude}/"):
            return True
    return False


def copy_repo_tree(repo_root: Path, target_root: Path, exclude_paths: Iterable[str]) -> int:
    file_count = 0
    for path in repo_root.rglob("*"):
        rel = path.relative_to(repo_root)
        if should_exclude(rel, exclude_paths):
            continue
        dest = target_root / rel
        if path.is_dir():
            dest.mkdir(parents=True, exist_ok=True)
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        file_count += 1
    return file_count


def prepare_deb_structure(repo_root: Path, config: DebPackageConfig, staging_root: Path) -> Path:
    ensure_path(repo_root, "repo_root", DebBuilderError)
    ensure_path(staging_root, "staging_root", DebBuilderError)

    debian_dir = staging_root / "DEBIAN"
    debian_dir.mkdir(parents=True, exist_ok=True)
    control_path = debian_dir / "control"
    control_path.write_text(build_control_content(config), encoding="utf-8")

    install_root = staging_root / config.install_root.lstrip("/")
    file_count = copy_repo_tree(repo_root, install_root, config.exclude_paths)

    desktop_config = load_desktop_config(repo_root / config.desktop_entry_config)
    desktop_content = build_desktop_entry(desktop_config, repo_root).replace(
        str(repo_root), config.install_root
    )

    desktop_target = (
        staging_root / "usr" / "share" / "applications" / f"{desktop_config.app_id}.desktop"
    )
    desktop_target.parent.mkdir(parents=True, exist_ok=True)
    desktop_target.write_text(desktop_content, encoding="utf-8")

    icon_target = (
        staging_root
        / "usr"
        / "share"
        / "icons"
        / "hicolor"
        / "scalable"
        / "apps"
        / f"{desktop_config.icon_name}.svg"
    )
    icon_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(repo_root / config.icon_source, icon_target)

    if file_count == 0:
        raise DebBuilderError("Keine Dateien für das Paket gefunden.")

    return staging_root


def build_deb_package(repo_root: Path, config: DebPackageConfig, logger: logging.Logger) -> Path:
    dpkg = shutil.which("dpkg-deb")
    if not dpkg:
        raise DebBuilderError("dpkg-deb fehlt. Bitte Paket 'dpkg-deb' installieren.")

    output_dir = repo_root / config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deb_name = f"{config.package_name}_{config.version}_{config.architecture}_{timestamp}.deb"
    deb_path = output_dir / deb_name

    with tempfile.TemporaryDirectory() as tmpdir:
        staging_root = Path(tmpdir) / f"{config.package_name}_staging"
        prepare_deb_structure(repo_root, config, staging_root)
        logger.info("Staging erstellt: %s", staging_root)
        subprocess.run([dpkg, "--build", str(staging_root), str(deb_path)], check=True)

    return deb_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Erstellt ein .deb-Paket für das Tool.",
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
    logger = logging.getLogger("deb_builder")

    try:
        config = load_config(args.config)
        deb_path = build_deb_package(args.root, config, logger)
        logger.info("Deb-Paket erstellt: %s", deb_path)
    except (DebBuilderError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        logger.error("Deb-Build fehlgeschlagen: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
