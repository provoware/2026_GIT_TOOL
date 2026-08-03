"""Dispatcher für zentrale Steuerung, Funktionen und Archiv-Direktaliase."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable, Sequence

try:
    from .alias_control import run_control_center
    from .alias_install import (
        DEFAULT_ALIAS_DIR,
        MANAGED_MARKER,
        install_aliases,
        print_install_result,
        uninstall_aliases,
    )
    from .alias_registry import (
        FUNCTION_ALIASES,
        STANDARD_ARCHIVE_ALIASES,
        AliasSpec,
        alias_table,
        all_alias_specs,
        archive_alias_specs,
        resolve_alias,
    )
    from .cli import (
        DEFAULT_LOG_FILE,
        add_wizard,
        change_mode_wizard,
        configure_logging,
        create_archive_wizard,
        default_database_path,
        main as archive_cli_main,
        print_overview,
    )
    from .service import ArchiveService, ArchiveServiceError, ArchiveStorageError
except ImportError:  # pragma: no cover - direkter Start als lose Datei
    from alias_control import run_control_center
    from alias_install import (
        DEFAULT_ALIAS_DIR,
        MANAGED_MARKER,
        install_aliases,
        print_install_result,
        uninstall_aliases,
    )
    from alias_registry import (
        FUNCTION_ALIASES,
        STANDARD_ARCHIVE_ALIASES,
        AliasSpec,
        alias_table,
        all_alias_specs,
        archive_alias_specs,
        resolve_alias,
    )
    from cli import (
        DEFAULT_LOG_FILE,
        add_wizard,
        change_mode_wizard,
        configure_logging,
        create_archive_wizard,
        default_database_path,
        main as archive_cli_main,
        print_overview,
    )
    from service import ArchiveService, ArchiveServiceError, ArchiveStorageError


def _common_parser(*, prog: str, description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog, description=description)
    parser.add_argument(
        "--database",
        type=Path,
        default=default_database_path(),
        help="Abweichender Pfad zur gemeinsamen SQLite-Datenbank.",
    )
    parser.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    return parser


def _archive_alias_parser(spec: AliasSpec) -> argparse.ArgumentParser:
    parser = _common_parser(prog=spec.name, description=spec.description)
    parser.add_argument("--category", default="Allgemein")
    parser.add_argument("--value", help="Direkter Inhalt; sonst startet die geführte Eingabe.")
    parser.add_argument("--yes", action="store_true", help="Direkte Eingabe ohne Rückfrage speichern.")
    parser.add_argument("--apply-spelling", action="store_true")
    return parser


def _function_parser(spec: AliasSpec) -> argparse.ArgumentParser:
    parser = _common_parser(prog=spec.name, description=spec.description)
    if spec.target == "add":
        parser.add_argument("--archive")
        parser.add_argument("--category", default="Allgemein")
        parser.add_argument("--value")
        parser.add_argument("--yes", action="store_true")
        parser.add_argument("--apply-spelling", action="store_true")
    elif spec.target == "new":
        parser.add_argument("name", nargs="?")
        parser.add_argument("--description", default="")
        parser.add_argument("--split-mode", choices=("comma", "whole"), default="comma")
    elif spec.target == "mode":
        parser.add_argument("archive", nargs="?")
        parser.add_argument("mode", nargs="?", choices=("comma", "whole"))
    elif spec.target == "aliases":
        group = parser.add_mutually_exclusive_group()
        group.add_argument("--install", action="store_true")
        group.add_argument("--uninstall", action="store_true")
        parser.add_argument("--target", type=Path, default=DEFAULT_ALIAS_DIR)
        parser.add_argument("--force", action="store_true")
    return parser


def _forward_direct_add(args, archive: str) -> list[str]:
    forwarded = [
        "--database",
        str(args.database),
        "--log-file",
        str(args.log_file),
        "--archive",
        archive,
        "--category",
        args.category,
        "--value",
        args.value,
    ]
    if args.yes:
        forwarded.append("--yes")
    if args.apply_spelling:
        forwarded.append("--apply-spelling")
    return forwarded


def _dispatch_archive(
    spec: AliasSpec,
    raw_argv: list[str],
    service: ArchiveService,
    input_fn: Callable[[str], str],
) -> int:
    args = _archive_alias_parser(spec).parse_args(raw_argv)
    if args.value is None:
        add_wizard(service, input_fn, archive_identifier=spec.target)
        return 0
    return archive_cli_main(
        _forward_direct_add(args, spec.target),
        input_fn=input_fn,
    )


def _dispatch_function(
    spec: AliasSpec,
    raw_argv: list[str],
    service: ArchiveService,
    input_fn: Callable[[str], str],
) -> int:
    args = _function_parser(spec).parse_args(raw_argv)
    if spec.target == "list":
        print_overview(service)
    elif spec.target == "help":
        print(alias_table(service))
    elif spec.target == "add":
        if args.value is None:
            add_wizard(service, input_fn, archive_identifier=args.archive)
        elif not args.archive:
            raise ArchiveServiceError("Für eine direkte Eingabe ist --archive erforderlich.")
        else:
            return archive_cli_main(
                _forward_direct_add(args, args.archive),
                input_fn=input_fn,
            )
    elif spec.target == "new":
        if args.name is None:
            create_archive_wizard(service, input_fn)
        else:
            archive = service.create_archive(
                args.name,
                args.description,
                split_on_comma=args.split_mode == "comma",
                source="cli-alias",
            )
            print(f"Archiv angelegt: {archive.name} ({archive.slug})")
    elif spec.target == "mode":
        if args.archive is None or args.mode is None:
            change_mode_wizard(service, input_fn, archive_identifier=args.archive)
        else:
            archive = service.get_archive(args.archive)
            updated = service.update_archive(
                archive.id,
                split_on_comma=args.mode == "comma",
                source="cli-alias",
            )
            mode_text = "Komma-Modus" if updated.split_on_comma else "Gesamttext-Modus"
            print(f"{updated.name}: {mode_text}")
    elif spec.target == "aliases":
        if args.uninstall:
            removed = uninstall_aliases(args.target)
            print(f"Verwaltete Aliase entfernt: {len(removed)}")
        elif args.install:
            paths = install_aliases(service, args.target, force=args.force)
            print_install_result(paths, args.target)
        else:
            print(alias_table(service))
    else:
        raise ArchiveServiceError(f"Aliasfunktion ist nicht implementiert: {spec.target}")
    return 0


def dispatch_alias(
    name: str,
    argv: Sequence[str] | None = None,
    *,
    input_fn: Callable[[str], str] = input,
) -> int:
    """Leitet jeden Wrapper über denselben Service und dieselben Prüfpfade."""
    raw_argv = list(argv or [])
    preliminary = argparse.ArgumentParser(add_help=False)
    preliminary.add_argument("--database", type=Path, default=default_database_path())
    preliminary.add_argument("--log-file", type=Path, default=DEFAULT_LOG_FILE)
    known, _ = preliminary.parse_known_args(raw_argv)
    try:
        logger = configure_logging(known.log_file)
        service = ArchiveService(known.database, logger=logger)
    except (ArchiveStorageError, OSError) as exc:
        print(f"Fehler: CLI-Alias konnte nicht initialisiert werden: {exc}", file=sys.stderr)
        return 2

    try:
        spec = resolve_alias(service, name)
        if spec.kind == "control":
            args = _common_parser(prog=spec.name, description=spec.description).parse_args(raw_argv)
            if args.database != service.database_path:
                service = ArchiveService(args.database, logger=configure_logging(args.log_file))
            return run_control_center(service, input_fn)
        if spec.kind == "archive":
            return _dispatch_archive(spec, raw_argv, service, input_fn)
        return _dispatch_function(spec, raw_argv, service, input_fn)
    except (ArchiveServiceError, ArchiveStorageError, OSError, ValueError) as exc:
        logger.error("Aliasvorgang fehlgeschlagen: %s", exc)
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2
    except (EOFError, KeyboardInterrupt):
        logger.info("Aliasvorgang durch Benutzer beendet.")
        print("\nAbgebrochen. Nicht bestätigte Eingaben wurden nicht gespeichert.")
        return 130


def build_entry_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dispatcher für installierte GenreArchiv-CLI-Aliase.",
        add_help=False,
    )
    parser.add_argument("--invoked", required=True, help="Name des aufgerufenen Alias-Wrappers.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args, forwarded = build_entry_parser().parse_known_args(argv)
    return dispatch_alias(args.invoked, forwarded)


__all__ = [
    "FUNCTION_ALIASES",
    "MANAGED_MARKER",
    "STANDARD_ARCHIVE_ALIASES",
    "AliasSpec",
    "alias_table",
    "all_alias_specs",
    "archive_alias_specs",
    "dispatch_alias",
    "install_aliases",
    "run_control_center",
    "uninstall_aliases",
]


if __name__ == "__main__":
    raise SystemExit(main())
