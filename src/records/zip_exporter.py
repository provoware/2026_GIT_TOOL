from __future__ import annotations

import fnmatch
import json
import logging
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List


class ZipExportError(ValueError):
    """Fehler bei ZIP-Exporten."""


@dataclass(frozen=True)
class ZipExportConfig:
    enabled: bool
    step_count: int
    state_path: Path
    output_dir: Path
    excludes: List[str]


def load_zip_config(data: dict) -> ZipExportConfig:
    config = ZipExportConfig(
        enabled=bool(data.get("zip_export_enabled", False)),
        step_count=int(data.get("zip_export_step_count", 5)),
        state_path=Path(data.get("zip_export_state_path", "data/zip_export_state.json")),
        output_dir=Path(data.get("zip_export_dir", "data/exports")),
        excludes=list(data.get("zip_export_excludes", [])),
    )
    validate_zip_config(config)
    return config


def validate_zip_config(config: ZipExportConfig) -> None:
    if config.step_count < 1:
        raise ZipExportError("ZIP-Schrittzahl muss mindestens 1 sein.")
    if not isinstance(config.excludes, list):
        raise ZipExportError("ZIP-Ausschlüsse müssen eine Liste sein.")


def _default_state() -> dict:
    return {"pending_steps": 0, "export_index": 0, "last_export": None}


def load_state(path: Path) -> dict:
    if not path.exists():
        return _default_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ZipExportError("ZIP-Status ist kein gültiges JSON.") from exc
    pending = data.get("pending_steps", 0)
    export_index = data.get("export_index", 0)
    if not isinstance(pending, int) or pending < 0:
        raise ZipExportError("ZIP-Status: pending_steps ist ungültig.")
    if not isinstance(export_index, int) or export_index < 0:
        raise ZipExportError("ZIP-Status: export_index ist ungültig.")
    data.setdefault("last_export", None)
    return data


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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


def _iter_files(root: Path, excludes: Iterable[str]) -> Iterable[Path]:
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if _matches_exclude(rel, excludes):
            continue
        if path.is_file():
            yield path


def create_zip_archive(root: Path, output_path: Path, excludes: Iterable[str]) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in _iter_files(root, excludes):
            rel_path = file_path.relative_to(root)
            archive.write(file_path, rel_path.as_posix())
            count += 1
    return count


def run_zip_export(
    repo_root: Path,
    new_steps: int,
    config: ZipExportConfig,
    logger: logging.Logger,
) -> List[Path]:
    if not config.enabled:
        logger.info("ZIP-Export ist deaktiviert.")
        return []
    if new_steps <= 0:
        logger.info("Keine neuen Schritte für den ZIP-Export.")
        return []

    state_path = repo_root / config.state_path
    output_dir = repo_root / config.output_dir
    state = load_state(state_path)
    pending_steps = state.get("pending_steps", 0) + new_steps
    export_index = state.get("export_index", 0)
    created: List[Path] = []

    while pending_steps >= config.step_count:
        export_index += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"release_export_{export_index:03d}_{timestamp}.zip"
        output_path = output_dir / filename
        file_count = create_zip_archive(repo_root, output_path, config.excludes)
        logger.info("ZIP-Export erstellt (%s Dateien): %s", file_count, output_path)
        created.append(output_path)
        pending_steps -= config.step_count
        state["last_export"] = datetime.now().isoformat(timespec="seconds")

    state["pending_steps"] = pending_steps
    state["export_index"] = export_index
    save_state(state_path, state)
    return created
