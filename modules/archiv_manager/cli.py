"""Laienfreundlicher Konsolenassistent für dieselbe Archivdatenbank wie die GUI."""

from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Callable, Sequence

try:
    from .service import ArchiveService, ArchiveServiceError, ArchiveStorageError
except ImportError:
    from service import ArchiveService, ArchiveServiceError, ArchiveStorageError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "archiv_manager.sqlite3"
DEFAULT_LOG_FILE = PROJECT_ROOT / "logs" / "archiv_manager.log"


def default_database_path() -> Path:
    configured = os.environ.get("GENREARCHIV_ARCHIVE_DB")
    return Path(configured).expanduser() if configured else DEFAULT_DATABASE


def configure_logging(log_file: Path | str) -> logging.Logger:
    """Konfiguriert das Archiv-Log erneut, wenn sich der Zielpfad ändert."""
    logger = logging.getLogger("archiv_manager")
    path = Path(log_file).expanduser().resolve()
    if getattr(logger, "_archiv_manager_log_path", None) == path:
        return logger

    for handler in tuple(logger.handlers):
        logger.removeHandler(handler)
        try:
            handler.close()
        except Exception:  # pragma: no cover - defensiver Handler-Abbau
            pass

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.handlers = [console, file_handler]
    setattr(logger, "_archiv_manager_log_path", path)
    return logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m modules.archiv_manager",
        description=(
            "Archiv-Assistent: fügt Einträge über die Konsole in exakt dieselbe "
            "Datenbank ein, die das grafische Archiv-Modul verwendet."
        ),
    )
    parser.add_argument(
        "--database",
        type=Path,
        default=default_database_path(),
        help="Abweichender Pfad zur gemeinsamen SQLite-Datenbank.",
    )
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument("--list", action="store_true", help="Archive und Einstellungen anzeigen.")
    parser.add_argument("--archive", help="Archivkennung oder Archivname für eine direkte Eingabe.")
    parser.add_argument("--category", default="Allgemein", help="Kategorie der direkten Eingabe.")
    parser.add_argument("--value", help="Direkt zu speichernder Text; ohne diese Option startet der Assistent.")
    parser.add_argument("--yes", action="store_true", help="Direkte Eingabe ohne Rückfrage bestätigen.")
    parser.add_argument(
        "--apply-spelling",
        action="store_true",
        help="Konservative Rechtschreibvorschläge bei direkter Eingabe übernehmen.",
    )
    operation.add_argument("--create-archive", help="Neues Archiv mit diesem Namen anlegen.")
    parser.add_argument("--description", default="", help="Beschreibung für ein neues Archiv.")
    parser.add_argument(
        "--split-mode",
        choices=("comma", "whole"),
        default="comma",
        help="Kommas trennen Einträge oder die gesamte Eingabe bleibt zusammen.",
    )
    operation.add_argument(
        "--set-mode",
        choices=("comma", "whole"),
        help="Setzt den Eingabemodus des mit --archive angegebenen Archivs.",
    )
    operation.add_argument("--show-aliases", action="store_true", help="Alle kurzen CLI-Aliase anzeigen.")
    operation.add_argument("--install-aliases", action="store_true", help="CLI-Aliase installieren oder aktualisieren.")
    operation.add_argument("--uninstall-aliases", action="store_true", help="Verwaltete CLI-Aliase entfernen.")
    parser.add_argument(
        "--alias-dir",
        type=Path,
        default=Path.home() / ".local" / "bin",
        help="Zielordner der Alias-Befehle.",
    )
    parser.add_argument("--force", action="store_true", help="Namenskollisionen bei der Aliasinstallation ersetzen.")
    return parser


def _section(title: str) -> None:
    border = "=" * 72
    print(f"\n{border}\n{title}\n{border}")


def _mode_text(split_on_comma: bool) -> str:
    return (
        "Komma-Modus: Jedes Komma trennt einen eigenen Archiveintrag."
        if split_on_comma
        else "Gesamttext-Modus: Die vollständige Eingabe wird als ein Eintrag gespeichert."
    )


def print_overview(service: ArchiveService) -> None:
    _section("ARCHIVÜBERSICHT")
    print(f"Gemeinsame Datenbank: {service.database_path}")
    print("GUI, CLI und Modul-API lesen und schreiben denselben Datenbestand.\n")
    for index, archive in enumerate(service.list_archives(), start=1):
        marker = "Standard" if archive.is_default else "Benutzerdefiniert"
        print(f"[{index}] {archive.name} ({archive.slug}) — {marker}")
        print(f"    {archive.description}")
        print(f"    {_mode_text(archive.split_on_comma)}")


def select_archive(service: ArchiveService, input_fn: Callable[[str], str]):
    archives = service.list_archives()
    print_overview(service)
    while True:
        raw = input_fn("\nArchivnummer oder Archivkennung eingeben: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(archives):
            return archives[int(raw) - 1]
        try:
            return service.get_archive(raw)
        except ArchiveStorageError as exc:
            print(f"Eingabe nicht erkannt: {exc}")


def _confirm(input_fn: Callable[[str], str], prompt: str) -> bool:
    return input_fn(f"{prompt} [j/N]: ").strip().casefold() in {"j", "ja", "y", "yes"}


def _print_prepared(archive, prepared) -> None:
    _section(f"PRÜFUNG — {archive.name}")
    print(_mode_text(archive.split_on_comma))
    for index, item in enumerate(prepared, start=1):
        flags: list[str] = []
        if item.spelling is not None:
            flags.append(f"Vorschlag: {item.spelling.suggested}")
        if item.duplicate_in_input:
            flags.append("Duplikat innerhalb dieser Eingabe")
        if item.duplicate_in_archive:
            flags.append("bereits im Archiv vorhanden")
        suffix = f" — {'; '.join(flags)}" if flags else ""
        print(f"{index}. {item.value}{suffix}")


def add_wizard(
    service: ArchiveService,
    input_fn: Callable[[str], str],
    *,
    archive_identifier: int | str | None = None,
) -> None:
    archive = (
        service.get_archive(archive_identifier)
        if archive_identifier is not None
        else select_archive(service, input_fn)
    )
    _section(f"EINGABE — {archive.name}")
    print(archive.description)
    print(_mode_text(archive.split_on_comma))
    print("Duplikate werden archivweit ohne Beachtung von Groß- und Kleinschreibung ignoriert.")
    categories = service.list_categories(archive.id)
    print("Vorhandene Kategorien: " + ", ".join(categories))
    category = input_fn("Kategorie eingeben oder Enter für 'Allgemein': ").strip() or "Allgemein"
    raw_text = input_fn("Archiveingabe: ")
    archive, prepared = service.prepare_add(archive.id, raw_text, apply_spelling=False)
    _print_prepared(archive, prepared)
    apply_spelling = any(item.spelling for item in prepared) and _confirm(
        input_fn,
        "Angezeigte Rechtschreibvorschläge übernehmen?",
    )
    archive, final_prepared = service.prepare_add(
        archive.id,
        raw_text,
        apply_spelling=apply_spelling,
    )
    _print_prepared(archive, final_prepared)
    if not _confirm(input_fn, "Geprüfte Einträge jetzt speichern?"):
        print("Abgebrochen. Es wurde nichts gespeichert.")
        return
    result = service.add_text(
        archive.id,
        raw_text,
        category=category,
        source="cli",
        apply_spelling=apply_spelling,
    )
    print(f"Gespeichert: {len(result.inserted)}")
    print(f"Ignorierte Duplikate: {len(result.duplicates)}")


def create_archive_wizard(service: ArchiveService, input_fn: Callable[[str], str]) -> None:
    _section("NEUES ARCHIV")
    print("Ein Archiv bündelt zusammengehörige Einträge und besitzt einen eigenen Komma-Modus.")
    name = input_fn("Eindeutiger Archivname: ").strip()
    description = input_fn("Kurze, konkrete Beschreibung: ").strip()
    split = _confirm(input_fn, "Soll ein Komma einzelne Einträge trennen?")
    archive = service.create_archive(
        name,
        description,
        split_on_comma=split,
        source="cli",
    )
    print(f"Archiv angelegt: {archive.name} ({archive.slug})")


def change_mode_wizard(
    service: ArchiveService,
    input_fn: Callable[[str], str],
    *,
    archive_identifier: int | str | None = None,
) -> None:
    archive = (
        service.get_archive(archive_identifier)
        if archive_identifier is not None
        else select_archive(service, input_fn)
    )
    _section(f"EINGABEMODUS — {archive.name}")
    print(_mode_text(archive.split_on_comma))
    new_mode = _confirm(input_fn, "Soll künftig jedes Komma einen eigenen Eintrag trennen?")
    updated = service.update_archive(
        archive.id,
        split_on_comma=new_mode,
        source="cli",
    )
    print(_mode_text(updated.split_on_comma))


# Rückwärtskompatibilität für bereits importierte interne Hilfsfunktionen.
_select_archive = select_archive
_add_wizard = add_wizard
_create_archive_wizard = create_archive_wizard
_change_mode_wizard = change_mode_wizard


def run_interactive(service: ArchiveService, input_fn: Callable[[str], str] = input) -> int:
    _section("ARCHIV-ASSISTENT")
    print("Dieser Assistent führt Schritt für Schritt durch alle nötigen Angaben.")
    print("Alle bestätigten Änderungen werden zusätzlich in der Datenbank protokolliert.")
    while True:
        print("\n[1] Einträge hinzufügen")
        print("[2] Neues Archiv anlegen")
        print("[3] Komma-Modus eines Archivs ändern")
        print("[4] Archivübersicht anzeigen")
        print("[0] Beenden")
        choice = input_fn("Auswahl: ").strip()
        if choice == "1":
            add_wizard(service, input_fn)
        elif choice == "2":
            create_archive_wizard(service, input_fn)
        elif choice == "3":
            change_mode_wizard(service, input_fn)
        elif choice == "4":
            print_overview(service)
        elif choice == "0":
            print("Archiv-Assistent beendet.")
            return 0
        else:
            print("Bitte 0, 1, 2, 3 oder 4 eingeben.")


def _handle_alias_management(args, service: ArchiveService) -> int | None:
    if not (args.show_aliases or args.install_aliases or args.uninstall_aliases):
        return None
    try:
        from .aliases import alias_table, install_aliases, uninstall_aliases
    except ImportError:
        from aliases import alias_table, install_aliases, uninstall_aliases

    if args.show_aliases:
        print(alias_table(service))
        return 0
    if args.uninstall_aliases:
        removed = uninstall_aliases(args.alias_dir)
        print(f"Verwaltete Aliase entfernt: {len(removed)}")
        return 0
    installed = install_aliases(service, args.alias_dir, force=args.force)
    print(f"Aliase installiert oder aktualisiert: {len(installed)}")
    print(f"Zielordner: {args.alias_dir.expanduser()}")
    print("Steueroberfläche starten: garch")
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        logger = configure_logging(args.log_file)
        service = ArchiveService(args.database, logger=logger)
    except (ArchiveStorageError, OSError) as exc:
        print(f"Fehler: CLI konnte nicht initialisiert werden: {exc}", file=sys.stderr)
        return 2
    try:
        alias_result = _handle_alias_management(args, service)
        if alias_result is not None:
            return alias_result
        if args.list:
            print_overview(service)
            return 0
        if args.create_archive:
            archive = service.create_archive(
                args.create_archive,
                args.description,
                split_on_comma=args.split_mode == "comma",
                source="cli",
            )
            print(f"Archiv angelegt: {archive.name} ({archive.slug})")
            return 0
        if args.set_mode:
            if not args.archive:
                raise ArchiveServiceError("--set-mode benötigt zusätzlich --archive.")
            archive = service.get_archive(args.archive)
            updated = service.update_archive(
                archive.id,
                split_on_comma=args.set_mode == "comma",
                source="cli",
            )
            print(f"{updated.name}: {_mode_text(updated.split_on_comma)}")
            return 0
        if args.value is not None and not args.archive:
            raise ArchiveServiceError("--value benötigt zusätzlich --archive.")
        if args.archive and args.value is not None:
            archive, prepared = service.prepare_add(
                args.archive,
                args.value,
                apply_spelling=args.apply_spelling,
            )
            _print_prepared(archive, prepared)
            if not args.yes and not _confirm(input_fn, "Geprüfte Einträge speichern?"):
                print("Abgebrochen. Es wurde nichts gespeichert.")
                return 1
            result = service.add_text(
                archive.id,
                args.value,
                category=args.category,
                source="cli",
                apply_spelling=args.apply_spelling,
            )
            print(f"Gespeichert: {len(result.inserted)}; Duplikate ignoriert: {len(result.duplicates)}")
            return 0
        if args.archive:
            add_wizard(service, input_fn, archive_identifier=args.archive)
            return 0
        return run_interactive(service, input_fn)
    except (ArchiveServiceError, ArchiveStorageError, OSError) as exc:
        logger.error("Archivvorgang fehlgeschlagen: %s", exc)
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        logger.info("Archiv-Assistent durch Benutzer beendet.")
        print("\nAbgebrochen. Nicht bestätigte Eingaben wurden nicht gespeichert.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
