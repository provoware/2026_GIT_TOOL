"""Laienfreundliche zentrale Steueroberfläche für alle Archiv-CLI-Funktionen."""

from __future__ import annotations

from typing import Callable

try:
    from .alias_install import DEFAULT_ALIAS_DIR, install_aliases, print_install_result
    from .alias_registry import alias_table, archive_alias_specs
    from .cli import add_wizard, change_mode_wizard, create_archive_wizard, print_overview
    from .service import ArchiveService
except ImportError:  # pragma: no cover
    from alias_install import DEFAULT_ALIAS_DIR, install_aliases, print_install_result
    from alias_registry import alias_table, archive_alias_specs
    from cli import add_wizard, change_mode_wizard, create_archive_wizard, print_overview
    from service import ArchiveService


def run_control_center(
    service: ArchiveService,
    input_fn: Callable[[str], str] = input,
) -> int:
    """Zeigt Funktionen und Archiv-Direktzugriffe in einer gemeinsamen Oberfläche."""
    while True:
        print("\n" + "=" * 76)
        print("GENREARCHIV CLI-STEUERUNG — garch")
        print("=" * 76)
        print(f"Gemeinsame Datenbank: {service.database_path}")
        print("\nFunktionen:")
        print("  [1] Einträge hinzufügen                 garch-add")
        print("  [2] Archive und Modi anzeigen           garch-list")
        print("  [3] Neues Archiv anlegen                garch-new")
        print("  [4] Eingabemodus ändern                 garch-mode")
        print("  [5] Alle Aliase anzeigen                garch-aliases")
        print("  [6] Aliase installieren/aktualisieren   garch-aliases --install")
        print("\nArchiv-Direktzugriffe:")
        archive_specs = archive_alias_specs(service)
        for index, spec in enumerate(archive_specs, start=10):
            archive = service.get_archive(spec.target)
            print(f"  [{index}] {archive.name:<34} {spec.name}")
        print("  [0] Beenden")

        choice = input_fn("\nAuswahl: ").strip()
        if choice == "0":
            print("CLI-Steuerung beendet.")
            return 0
        if choice == "1":
            add_wizard(service, input_fn)
        elif choice == "2":
            print_overview(service)
        elif choice == "3":
            create_archive_wizard(service, input_fn)
        elif choice == "4":
            change_mode_wizard(service, input_fn)
        elif choice == "5":
            print(alias_table(service))
        elif choice == "6":
            paths = install_aliases(service)
            print_install_result(paths, DEFAULT_ALIAS_DIR)
        elif choice.isdigit() and 10 <= int(choice) < 10 + len(archive_specs):
            target = archive_specs[int(choice) - 10].target
            add_wizard(service, input_fn, archive_identifier=target)
        else:
            print("Auswahl nicht erkannt. Bitte eine angezeigte Nummer eingeben.")
