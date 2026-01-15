#!/usr/bin/env python3
"""Selektiver Export: Teilmengen der Projektdateien als ZIP exportieren."""

from __future__ import annotations

import argparse
import fnmatch
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path, load_json

DEFAULT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = DEFAULT_ROOT / "config" / "selective_export.json"


class SelectiveExportError(ValueError):
    """Fehler bei selektiven Exporten."""


@dataclass(frozen=True)
class ExportPreset:
    name: str
    label: str
    includes: List[str]
    excludes: List[str]


@dataclass(frozen=True)
class ExportConfig:
    presets: List[ExportPreset]
    default_preset: str
    output_dir: Path
    base_name: str


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SelectiveExportError(f"{label} ist leer oder ungültig.")
    return value.strip()


def _require_list(value: object, label: str) -> List[str]:
    if not isinstance(value, list):
        raise SelectiveExportError(f"{label} ist keine Liste.")
    items: List[str] = []
    for entry in value:
        if not isinstance(entry, str) or not entry.strip():
            raise SelectiveExportError(f"{label} enthält ungültige Einträge.")
        items.append(entry.strip())
    return items


def load_config(config_path: Path) -> ExportConfig:
    data = load_json(
        config_path,
        SelectiveExportError,
        "Export-Konfiguration fehlt",
        "Export-Konfiguration ist ungültig",
    )
    presets_raw = data.get("presets", {})
    if not isinstance(presets_raw, dict) or not presets_raw:
        raise SelectiveExportError("presets fehlen oder sind leer.")
    presets: List[ExportPreset] = []
    for name, payload in presets_raw.items():
        preset_name = _require_text(name, "preset_name")
        if not isinstance(payload, dict):
            raise SelectiveExportError(f"Preset {preset_name} ist kein Objekt.")
        presets.append(
            ExportPreset(
                name=preset_name,
                label=_require_text(payload.get("label", preset_name), "preset.label"),
                includes=_require_list(payload.get("includes", []), "preset.includes"),
                excludes=_require_list(payload.get("excludes", []), "preset.excludes"),
            )
        )
    default_preset = _require_text(data.get("default_preset", presets[0].name), "default_preset")
    output_dir = Path(_require_text(data.get("output_dir", "data/exports"), "output_dir"))
    base_name = _require_text(data.get("base_name", "selective_export"), "base_name")
    return ExportConfig(
        presets=presets,
        default_preset=default_preset,
        output_dir=output_dir,
        base_name=base_name,
    )


def _matches_exclude(relative_path: Path, excludes: Iterable[str]) -> bool:
    rel_posix = relative_path.as_posix()
    for exclude in excludes:
        if not exclude:
            continue
        if "*" in exclude or "?" in exclude:
            if fnmatch.fnmatch(rel_posix, exclude):
                return True
        if rel_posix == exclude or rel_posix.startswith(f"{exclude}/"):
            return True
    return False


def _iter_files(root: Path, includes: Iterable[Path], excludes: Iterable[str]) -> Iterable[Path]:
    for include_path in includes:
        if include_path.is_dir():
            for path in include_path.rglob("*"):
                rel = path.relative_to(root)
                if _matches_exclude(rel, excludes):
                    continue
                if path.is_file():
                    yield path
        elif include_path.is_file():
            rel = include_path.relative_to(root)
            if not _matches_exclude(rel, excludes):
                yield include_path


def _unique_path(output_dir: Path, filename: str) -> Path:
    candidate = output_dir / filename
    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{candidate.stem}_{counter}{candidate.suffix}"
        counter += 1
    return candidate


def resolve_preset(config: ExportConfig, preset_name: str) -> ExportPreset:
    clean_name = _require_text(preset_name, "preset_name")
    for preset in config.presets:
        if preset.name == clean_name:
            return preset
    raise SelectiveExportError(f"Preset nicht gefunden: {clean_name}")


def build_export(
    root: Path,
    preset: ExportPreset,
    output_dir: Path,
    base_name: str,
    dry_run: bool = False,
) -> Path:
    ensure_path(root, "root", SelectiveExportError)
    root_dir = root.resolve()
    output_dir = (root_dir / output_dir).resolve()
    if not preset.includes:
        raise SelectiveExportError("Preset enthält keine include-Pfade.")
    include_paths: List[Path] = []
    for include in preset.includes:
        candidate = (root_dir / include).resolve()
        if root_dir not in candidate.parents and candidate != root_dir:
            raise SelectiveExportError(f"Include liegt außerhalb des Projekts: {include}")
        if not candidate.exists():
            raise SelectiveExportError(f"Include fehlt: {include}")
        include_paths.append(candidate)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}_{preset.name}_{timestamp}.zip"
    output_path = _unique_path(output_dir, filename)
    if dry_run:
        return output_path
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in _iter_files(root_dir, include_paths, preset.excludes):
            rel_path = file_path.relative_to(root_dir)
            archive.write(file_path, rel_path.as_posix())
    if not output_path.exists():
        raise SelectiveExportError("Export konnte nicht geschrieben werden.")
    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Selektiver Export: Teilmengen der Projektdateien als ZIP exportieren.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument(
        "--preset",
        type=str,
        default="",
        help="Preset aus config/selective_export.json (Standard: default_preset).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Nur prüfen, nichts schreiben.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
        preset_name = args.preset.strip() or config.default_preset
        preset = resolve_preset(config, preset_name)
        output_path = build_export(
            args.root,
            preset,
            config.output_dir,
            config.base_name,
            dry_run=args.dry_run,
        )
    except SelectiveExportError as exc:
        print(f"Selektiver Export fehlgeschlagen: {exc}")
        return 2
    status = "Vorschau" if args.dry_run else "Export"
    print(f"{status} erstellt: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
