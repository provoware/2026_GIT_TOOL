"""Sichere Installation und Entfernung der POSIX-Alias-Wrapper."""

from __future__ import annotations

import json
import os
import shlex
import stat
import sys
import tempfile
from pathlib import Path
from typing import Iterable

try:
    from .alias_registry import all_alias_specs
    from .service import ArchiveService, ArchiveServiceError
except ImportError:  # pragma: no cover
    from alias_registry import all_alias_specs
    from service import ArchiveService, ArchiveServiceError

MANAGED_MARKER = "# managed-by: genrearchiv-cli-aliases-v1"
MANAGED_ID = "genrearchiv-cli-aliases-v1"
MANIFEST_NAME = ".garch-aliases.json"
DEFAULT_ALIAS_DIR = Path.home() / ".local" / "bin"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _wrapper_content(alias_name: str, *, project_root: Path, python_executable: str) -> str:
    root = shlex.quote(str(project_root.resolve()))
    python = shlex.quote(str(Path(python_executable).resolve()))
    alias = shlex.quote(alias_name)
    return (
        "#!/bin/sh\n"
        f"{MANAGED_MARKER}\n"
        f"PROJECT_ROOT={root}\n"
        'export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH:+:$PYTHONPATH}"\n'
        f"exec {python} -m modules.archiv_manager.aliases --invoked {alias} \"$@\"\n"
    )


def _is_managed_wrapper(path: Path) -> bool:
    try:
        return path.is_file() and MANAGED_MARKER in path.read_text(encoding="utf-8")[:256]
    except OSError:
        return False


def _is_managed_manifest(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return False
    return isinstance(payload, dict) and payload.get("managed_by") == MANAGED_ID


def _atomic_write(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
        if executable:
            mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        temporary.chmod(mode)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def install_aliases(
    service: ArchiveService,
    target_dir: Path | str = DEFAULT_ALIAS_DIR,
    *,
    force: bool = False,
    project_root: Path = PROJECT_ROOT,
    python_executable: str = sys.executable,
) -> tuple[Path, ...]:
    """Installiert Wrapper atomar und überschreibt keine fremden Dateien still."""
    if os.name != "posix":
        raise ArchiveServiceError(
            "Shell-Aliase werden derzeit nur auf Linux/POSIX-Systemen installiert."
        )
    target = Path(target_dir).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    desired_specs = all_alias_specs(service)
    desired_names = {item.name for item in desired_specs}

    collisions = [
        target / name
        for name in sorted(desired_names)
        if (target / name).exists() and not _is_managed_wrapper(target / name)
    ]
    manifest = target / MANIFEST_NAME
    if manifest.exists() and not _is_managed_manifest(manifest) and not force:
        collisions.append(manifest)
    if collisions and not force:
        joined = ", ".join(str(path) for path in collisions)
        raise ArchiveServiceError(
            "Aliasinstallation abgebrochen, weil vorhandene fremde Dateien "
            f"nicht überschrieben werden: {joined}"
        )

    installed: list[Path] = []
    for spec in desired_specs:
        path = target / spec.name
        _atomic_write(
            path,
            _wrapper_content(
                spec.name,
                project_root=project_root,
                python_executable=python_executable,
            ),
            executable=True,
        )
        installed.append(path)

    for stale in target.glob("garch*"):
        if stale.name not in desired_names and _is_managed_wrapper(stale):
            stale.unlink()

    manifest_payload = json.dumps(
        {
            "version": 1,
            "managed_by": MANAGED_ID,
            "project_root": str(project_root.resolve()),
            "python": str(Path(python_executable).resolve()),
            "aliases": sorted(desired_names),
        },
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    _atomic_write(manifest, manifest_payload)
    return tuple(installed)


def uninstall_aliases(target_dir: Path | str = DEFAULT_ALIAS_DIR) -> tuple[Path, ...]:
    """Entfernt ausschließlich eindeutig markierte, verwaltete Dateien."""
    target = Path(target_dir).expanduser()
    if not target.exists():
        return ()
    removed: list[Path] = []
    for path in target.glob("garch*"):
        if _is_managed_wrapper(path):
            path.unlink()
            removed.append(path)
    manifest = target / MANIFEST_NAME
    if _is_managed_manifest(manifest):
        manifest.unlink()
    return tuple(sorted(removed))


def path_contains(directory: Path) -> bool:
    try:
        resolved = directory.resolve()
    except OSError:
        resolved = directory
    for item in os.environ.get("PATH", "").split(os.pathsep):
        if not item:
            continue
        try:
            if Path(item).expanduser().resolve() == resolved:
                return True
        except OSError:
            continue
    return False


def print_install_result(paths: Iterable[Path], target: Path) -> None:
    paths = tuple(paths)
    print(f"Aliase installiert oder aktualisiert: {len(paths)}")
    print(f"Zielordner: {target}")
    if not path_contains(target):
        print("Hinweis: Der Zielordner ist noch nicht in PATH enthalten.")
        print(f'Für Bash/Zsh ergänzen: export PATH="{target}:$PATH"')
    print("Steueroberfläche starten: garch")
