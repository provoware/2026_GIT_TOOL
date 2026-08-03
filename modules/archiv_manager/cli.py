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


def configure_logging(log_file: Path | str) -> logging.Logger:
    logger = logging.getLogger("archiv_manager")
    if getattr(logger, "_archiv_manager_configured", False):
        return logger
    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    path = Path(log_file).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.handlers = [console, file_handler]
    setattr(logger, "_archiv_manager_configured", True)
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
        default=Path(os.environ.get("GENREARCHIV_ARCHIVE_DB", DEFAULT_DATABASE)),
        help="Abweichender Pfad zur gemeinsamen SQLite-Datenbank.",
    )
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    parser.add_argument("--list", action="store_true", help="Archive und Einstellungen anzeigen.")
    parser.add_argument("--archive", help="Archivkennung oder Archivname für eine direkte Eingabe.")
    parser.add_argument("--category", default="Allgemein", help="Kategorie der direkten Eingabe.")
    parser.add_argument("--value", help="Direkt zu speichernder Text; ohne diese Option startet der Assistent.")
    parser.add_argument("--yes", action="store_true", help="Direkte Eingabe ohne Rückfrage bestätigen.")
    parser.add_argument(
        "--apply-spelling",
        action="store_true",
        help="Konservative Rechtschreibvorschläge bei direkter Eingabe übernehmen.",
    )
    parser.add_argument("--create-archive", help="Neues Archiv mit diesem Namen anlegen.")
    parser.add_argument("--description", default="", help="Beschreibung für ein neues Archiv.")
    parser.add_argument(
        "--split-mode",
        choices=("comma", "whole"),
        default="comma",
        help="Kommas trennen Einträge oder die gesamte Eingabe bleibt zusammen.",
    )
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


def _select_archive(service: ArchiveService, input_fn: Callable[[str], str]):
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


def _add_wizard(service: ArchiveService, input_fn: Callable[[str], str]) -> None:
    archive = _select_archive(service, input_fn)
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


def _create_archive_wizard(service: ArchiveService, input_fn: Callable[[str], str]) -> None:
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


def _change_mode_wizard(service: ArchiveService, input_fn: Callable[[str], str]) -> None:
    archive = _select_archive(service, input_fn)
    _section(f"EINGABEMODUS — {archive.name}")
    print(_mode_text(archive.split_on_comma))
    new_mode = _confirm(input_fn, "Soll künftig jedes Komma einen eigenen Eintrag trennen?")
    updated = service.update_archive(
        archive.id,
        split_on_comma=new_mode,
        source="cli",
    )
    print(_mode_text(updated.split_on_comma))


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
            _add_wizard(service, input_fn)
        elif choice == "2":
            _create_archive_wizard(service, input_fn)
        elif choice == "3":
            _change_mode_wizard(service, input_fn)
        elif choice == "4":
            print_overview(service)
        elif choice == "0":
            print("Archiv-Assistent beendet.")
            return 0
        else:
            print("Bitte 0, 1, 2, 3 oder 4 eingeben.")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logger = configure_logging(args.log_file)
    service = ArchiveService(args.database, logger=logger)
    try:
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
        if args.archive and args.value is not None:
            archive, prepared = service.prepare_add(
                args.archive,
                args.value,
                apply_spelling=args.apply_spelling,
            )
            _print_prepared(archive, prepared)
            if not args.yes and not _confirm(input, "Geprüfte Einträge speichern?"):
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
        return run_interactive(service)
    except (ArchiveServiceError, ArchiveStorageError) as exc:
        logger.error("Archivvorgang fehlgeschlagen: %s", exc)
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        logger.info("Archiv-Assistent durch Benutzer beendet.")
        print("\nAbgebrochen. Nicht bestätigte Eingaben wurden nicht gespeichert.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
