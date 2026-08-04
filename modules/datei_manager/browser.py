"""Reine Browser-, Sortier- und Bildvorschau-Logik für den Datei-Manager."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Literal, Sequence


class BrowserError(ValueError):
    """Ungültige oder nicht lesbare Dateibrowser-Eingabe."""


SortKey = Literal["name", "type", "size", "modified"]
IMAGE_SUFFIXES = frozenset(
    {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff"}
)


@dataclass(frozen=True)
class FileEntry:
    path: Path
    name: str
    is_directory: bool
    suffix: str
    size: int
    modified: float
    hidden: bool

    @property
    def type_label(self) -> str:
        if self.is_directory:
            return "Ordner"
        return self.suffix[1:].upper() if self.suffix else "Datei"

    @property
    def modified_label(self) -> str:
        return datetime.fromtimestamp(self.modified).strftime("%d.%m.%Y %H:%M")

    @property
    def size_label(self) -> str:
        if self.is_directory:
            return "—"
        return format_size(self.size)

    @property
    def is_image(self) -> bool:
        return not self.is_directory and self.suffix.lower() in IMAGE_SUFFIXES


@dataclass(frozen=True)
class PreviewPlan:
    path: Path
    supported: bool
    target_width: int
    target_height: int
    message: str


def _require_directory(path: Path | str) -> Path:
    if not isinstance(path, (Path, str)) or isinstance(path, str) and not path.strip():
        raise BrowserError("Ordnerpfad fehlt oder ist ungültig.")
    candidate = Path(path).expanduser()
    try:
        candidate = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise BrowserError(f"Ordner ist nicht erreichbar: {candidate}") from exc
    if not candidate.is_dir():
        raise BrowserError(f"Pfad ist kein Ordner: {candidate}")
    return candidate


def list_directory(path: Path | str, *, show_hidden: bool = False) -> list[FileEntry]:
    if not isinstance(show_hidden, bool):
        raise BrowserError("show_hidden muss bool sein.")
    directory = _require_directory(path)
    entries: list[FileEntry] = []
    try:
        children = sorted(directory.iterdir(), key=lambda child: child.name.casefold())
    except OSError as exc:
        raise BrowserError(f"Ordner kann nicht gelesen werden: {directory}") from exc
    for child in children:
        hidden = child.name.startswith(".")
        if hidden and not show_hidden:
            continue
        try:
            stat = child.stat()
            is_directory = child.is_dir()
        except OSError:
            # Nicht lesbare Einzelobjekte werden ausgelassen, statt die gesamte Liste
            # unbrauchbar zu machen.
            continue
        entries.append(
            FileEntry(
                path=child,
                name=child.name,
                is_directory=is_directory,
                suffix="" if is_directory else child.suffix.lower(),
                size=0 if is_directory else int(stat.st_size),
                modified=float(stat.st_mtime),
                hidden=hidden,
            )
        )
    return entries


def sort_entries(
    entries: Iterable[FileEntry],
    *,
    sort_by: SortKey = "name",
    descending: bool = False,
    directories_first: bool = True,
) -> list[FileEntry]:
    if sort_by not in {"name", "type", "size", "modified"}:
        raise BrowserError(f"Unbekannte Sortierspalte: {sort_by}")
    if not isinstance(descending, bool) or not isinstance(directories_first, bool):
        raise BrowserError("Sortieroptionen müssen bool sein.")
    values = list(entries)
    if any(not isinstance(entry, FileEntry) for entry in values):
        raise BrowserError("entries enthält ungültige Elemente.")

    def value(entry: FileEntry):
        if sort_by == "name":
            return entry.name.casefold()
        if sort_by == "type":
            return (entry.type_label.casefold(), entry.name.casefold())
        if sort_by == "size":
            return (entry.size, entry.name.casefold())
        return (entry.modified, entry.name.casefold())

    if directories_first:
        directories = [entry for entry in values if entry.is_directory]
        files = [entry for entry in values if not entry.is_directory]
        return sorted(directories, key=value, reverse=descending) + sorted(
            files, key=value, reverse=descending
        )
    return sorted(values, key=value, reverse=descending)


def fit_inside(
    source_width: int,
    source_height: int,
    available_width: int,
    available_height: int,
    *,
    allow_upscale: bool = False,
) -> tuple[int, int]:
    dimensions = (source_width, source_height, available_width, available_height)
    if any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in dimensions):
        raise BrowserError("Bild- und Vorschaugrößen müssen positive Ganzzahlen sein.")
    scale = min(available_width / source_width, available_height / source_height)
    if not allow_upscale:
        scale = min(scale, 1.0)
    return max(1, round(source_width * scale)), max(1, round(source_height * scale))


def build_preview_plan(
    path: Path | str,
    *,
    source_size: Sequence[int] | None,
    available_width: int,
    available_height: int,
) -> PreviewPlan:
    candidate = Path(path).expanduser()
    if not candidate.exists() or not candidate.is_file():
        raise BrowserError(f"Datei wurde nicht gefunden: {candidate}")
    if candidate.suffix.lower() not in IMAGE_SUFFIXES:
        return PreviewPlan(
            path=candidate,
            supported=False,
            target_width=0,
            target_height=0,
            message="Für diesen Dateityp ist keine Bildvorschau verfügbar.",
        )
    if (
        source_size is None
        or len(source_size) != 2
        or any(not isinstance(value, int) or isinstance(value, bool) or value <= 0 for value in source_size)
    ):
        raise BrowserError("source_size ist für ein Bild ungültig.")
    width, height = fit_inside(
        source_size[0],
        source_size[1],
        available_width,
        available_height,
        allow_upscale=False,
    )
    return PreviewPlan(
        path=candidate,
        supported=True,
        target_width=width,
        target_height=height,
        message=f"Bildvorschau {width} × {height} Pixel.",
    )


def format_size(size: int) -> str:
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise BrowserError("size muss eine nichtnegative Ganzzahl sein.")
    value = float(size)
    units = ("B", "KB", "MB", "GB", "TB")
    for unit in units:
        if value < 1024.0 or unit == units[-1]:
            return f"{int(value)} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024.0
    raise AssertionError("Unerreichbarer Größenformatpfad.")
