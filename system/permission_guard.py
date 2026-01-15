"""Rechte- und Schreibschutzsystem für Modulzugriffe."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from module_registry import load_manifest


class PermissionGuardError(ValueError):
    """Fehler im Rechte- und Schreibschutzsystem."""


@dataclass(frozen=True)
class PermissionContext:
    module_id: str
    permissions: tuple[str, ...]
    write_mode: str


def _require_path(value: object, label: str) -> Path:
    if not isinstance(value, Path):
        raise PermissionGuardError(f"{label} ist kein Pfad (Path).")
    return value


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PermissionGuardError(f"{label} ist leer oder ungültig.")
    return value.strip()


def _find_repo_root(start: Path) -> Path:
    for parent in start.resolve().parents:
        if (parent / "config").exists() and (parent / "modules").exists():
            return parent
    return start.resolve().parents[2]


def _normalize_permissions(entries: Iterable[str]) -> tuple[str, ...]:
    cleaned: List[str] = []
    for entry in entries:
        text = _require_text(entry, "permission_entry").lower()
        if not re.fullmatch(r"(read|write)(:[a-z0-9_]+)?", text):
            raise PermissionGuardError(f"permission_entry ist ungültig: {text}")
        cleaned.append(text)
    return tuple(dict.fromkeys(cleaned))


def load_permission_context(module_file: Path) -> PermissionContext:
    module_file = _require_path(module_file, "module_file")
    module_dir = module_file.resolve().parent
    manifest = load_manifest(module_dir)
    permissions = _normalize_permissions(manifest.permissions)
    write_mode = os.environ.get("GENREARCHIV_WRITE_MODE", "normal").strip().lower() or "normal"
    if write_mode not in {"normal", "read-only"}:
        raise PermissionGuardError("GENREARCHIV_WRITE_MODE ist ungültig.")
    return PermissionContext(
        module_id=manifest.module_id,
        permissions=permissions,
        write_mode=write_mode,
    )


def _path_category(root: Path, target: Path) -> Optional[str]:
    root = root.resolve()
    target = target.resolve()
    categories = {
        "data": root / "data",
        "config": root / "config",
        "logs": root / "logs",
    }
    for name, base in categories.items():
        try:
            target.relative_to(base)
        except ValueError:
            continue
        else:
            return name
    try:
        target.relative_to(root)
    except ValueError:
        return "external"
    return None


def _required_permission(category: Optional[str]) -> str:
    if category in {"data", "config", "logs"}:
        return f"write:{category}"
    if category == "external":
        return "write:data"
    return "write"


def require_write_access(module_file: Path, target_path: Path, action: str) -> None:
    module_file = _require_path(module_file, "module_file")
    target_path = _require_path(target_path, "target_path")
    action = _require_text(action, "action")
    context = load_permission_context(module_file)
    if context.write_mode == "read-only":
        raise PermissionGuardError(
            "Schreibschutz aktiv: Schreibzugriff ist im Safe-Mode deaktiviert. "
            f"Aktion '{action}' wurde blockiert."
        )
    repo_root = _find_repo_root(module_file)
    category = _path_category(repo_root, target_path)
    needed = _required_permission(category)
    if needed not in context.permissions and "write" not in context.permissions:
        raise PermissionGuardError(
            "Schreibrechte fehlen: "
            f"Modul '{context.module_id}' darf '{needed}' nicht nutzen. "
            f"Aktion '{action}' wurde blockiert."
        )
