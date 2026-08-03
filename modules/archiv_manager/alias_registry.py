"""Zentrale, kollisionsfreie Registry aller GenreArchiv-CLI-Aliase."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from .service import ArchiveService, ArchiveStorageError
except ImportError:  # pragma: no cover - direkter Start als lose Datei
    from service import ArchiveService, ArchiveStorageError

CONTROL_ALIAS = "garch"


@dataclass(frozen=True)
class AliasSpec:
    name: str
    kind: str
    target: str
    description: str


FUNCTION_ALIASES: tuple[AliasSpec, ...] = (
    AliasSpec(CONTROL_ALIAS, "control", "control", "Zentrale Steueroberfläche öffnen"),
    AliasSpec("garch-add", "function", "add", "Geführte Eingabe mit freier Archivwahl"),
    AliasSpec("garch-list", "function", "list", "Archive und Eingabemodi anzeigen"),
    AliasSpec("garch-new", "function", "new", "Neues Archiv anlegen"),
    AliasSpec("garch-mode", "function", "mode", "Komma- oder Gesamttext-Modus ändern"),
    AliasSpec("garch-aliases", "function", "aliases", "Aliasübersicht oder Installation"),
    AliasSpec("garch-help", "function", "help", "Ausführliche CLI-Hilfe anzeigen"),
)

STANDARD_ARCHIVE_ALIASES: tuple[AliasSpec, ...] = (
    AliasSpec("garch-gen", "archive", "genres", "Einträge im Archiv Genres erfassen"),
    AliasSpec("garch-stim", "archive", "stimmungen", "Einträge im Archiv Stimmungen erfassen"),
    AliasSpec("garch-fx", "archive", "besondere-effekte", "Einträge im Archiv Besondere Effekte erfassen"),
    AliasSpec("garch-fav", "archive", "favoriten", "Einträge im Archiv Favoriten erfassen"),
    AliasSpec(
        "garch-basis",
        "archive",
        "basis-entwicklungs-strukturen",
        "Einträge in Basis-Entwicklungs-Strukturen erfassen",
    ),
    AliasSpec("garch-brain", "archive", "brainstorm", "Einträge im Archiv Brainstorm erfassen"),
    AliasSpec("garch-linux", "archive", "linux", "Einträge im Archiv Linux erfassen"),
)


def dynamic_archive_alias(slug: str) -> str:
    """Bildet einen kollisionsfreien Alias für benutzerdefinierte Archive."""
    if not isinstance(slug, str) or not slug.strip():
        raise ValueError("Archivkennung für Alias ist leer.")
    return f"garch-a-{slug.strip().lower()}"


def archive_alias_specs(service: ArchiveService) -> tuple[AliasSpec, ...]:
    standard_targets = {item.target for item in STANDARD_ARCHIVE_ALIASES}
    dynamic = [
        AliasSpec(
            dynamic_archive_alias(archive.slug),
            "archive",
            archive.slug,
            f"Einträge im Archiv {archive.name} erfassen",
        )
        for archive in service.list_archives()
        if archive.slug not in standard_targets
    ]
    return STANDARD_ARCHIVE_ALIASES + tuple(dynamic)


def all_alias_specs(service: ArchiveService) -> tuple[AliasSpec, ...]:
    specs = FUNCTION_ALIASES + archive_alias_specs(service)
    names = [item.name for item in specs]
    if len(names) != len(set(names)):
        raise RuntimeError("Interne Aliasdefinition enthält doppelte Befehlsnamen.")
    return specs


def resolve_alias(service: ArchiveService, name: str) -> AliasSpec:
    clean_name = Path(name).name.strip()
    for spec in all_alias_specs(service):
        if spec.name == clean_name:
            return spec
    if clean_name.startswith("garch-a-"):
        slug = clean_name.removeprefix("garch-a-")
        archive = service.get_archive(slug)
        return AliasSpec(
            clean_name,
            "archive",
            archive.slug,
            f"Einträge im Archiv {archive.name} erfassen",
        )
    raise ArchiveStorageError(f"Unbekannter CLI-Alias: {clean_name}")


def alias_table(service: ArchiveService) -> str:
    specs = all_alias_specs(service)
    width = max(len(item.name) for item in specs)
    rows = ["GENREARCHIV CLI-ALIASE", "", "Steuerung und Funktionen:"]
    rows.extend(
        f"  {item.name:<{width}}  {item.description}"
        for item in FUNCTION_ALIASES
    )
    rows.extend(("", "Direktzugriff auf Archive:"))
    rows.extend(
        f"  {item.name:<{width}}  {item.description}"
        for item in archive_alias_specs(service)
    )
    rows.extend(
        (
            "",
            "Direkte Eingabe über einen Archiv-Alias:",
            '  garch-gen --value "Fantasy, Horror" --category Allgemein --yes',
            "",
            "Benutzerdefinierte Archive erhalten beim Aktualisieren der Aliase",
            "automatisch den eindeutigen Namen garch-a-<archivkennung>.",
        )
    )
    return "\n".join(rows)
