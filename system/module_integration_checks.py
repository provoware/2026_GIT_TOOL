#!/usr/bin/env python3
"""Modulverbund-Checks: prüft Modul-Konsistenz über mehrere Module hinweg."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

import module_checker
import module_selftests
from config_utils import ensure_path


class ModuleIntegrationError(Exception):
    """Fehler in den Modulverbund-Checks."""


@dataclass(frozen=True)
class IntegrationResult:
    issues: List[str]


def _render_issues(issues: Iterable[str]) -> str:
    issues_list = list(issues)
    if not issues_list:
        return "Modulverbund-Check: Keine Probleme gefunden."
    lines = ["Modulverbund-Check: Probleme gefunden:"]
    lines.extend([f"- {issue}" for issue in issues_list])
    lines.append("Bitte die Hinweise prüfen und die Modul-Configs korrigieren.")
    return "\n".join(lines)


def run_integration_checks(
    modules_config: Path,
    selftests_config: Path,
) -> IntegrationResult:
    ensure_path(modules_config, "modules_config", ModuleIntegrationError)
    ensure_path(selftests_config, "selftests_config", ModuleIntegrationError)

    try:
        entries = module_checker.load_modules(modules_config)
    except module_checker.ModuleCheckError as exc:
        raise ModuleIntegrationError(str(exc)) from exc

    try:
        testcases = module_selftests.load_test_inputs(selftests_config)
    except module_selftests.ModuleSelftestError as exc:
        raise ModuleIntegrationError(str(exc)) from exc

    issues: List[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for entry in entries:
        if entry.module_id in seen_ids:
            duplicate_ids.add(entry.module_id)
        seen_ids.add(entry.module_id)
    if duplicate_ids:
        issues.append(f"Doppelte Modul-IDs gefunden: {', '.join(sorted(duplicate_ids))}.")

    for entry in entries:
        if not entry.enabled:
            continue
        if entry.module_id not in testcases:
            issues.append(f"Kein Selftest hinterlegt: {entry.module_id} ({entry.name}).")
        if not entry.path.exists():
            issues.append(f"Modul-Pfad fehlt: {entry.module_id} ({entry.path}).")
            continue
        try:
            manifest = module_checker.load_manifest(entry.path)
        except module_checker.ModuleCheckError as exc:
            issues.append(str(exc))
            continue
        if manifest.module_id != entry.module_id:
            issues.append(
                "Manifest-ID passt nicht zur Modul-Konfiguration: "
                f"{entry.module_id} erwartet, aber {manifest.module_id} gefunden."
            )

    issues.extend(module_checker.check_modules(entries))
    return IntegrationResult(issues=issues)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Modulverbund-Checks für konsistente Modul-Konfiguration.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=module_checker.CONFIG_DEFAULT,
        help="Pfad zur Modul-Konfiguration (modules.json).",
    )
    parser.add_argument(
        "--selftests",
        type=Path,
        default=module_selftests.SELFTEST_DEFAULT,
        help="Pfad zur Selftest-Konfiguration (module_selftests.json).",
    )
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    try:
        result = run_integration_checks(args.config, args.selftests)
    except ModuleIntegrationError as exc:
        logging.error("Modulverbund-Checks konnten nicht starten: %s", exc)
        return 2

    output = _render_issues(result.issues)
    print(output)
    if result.issues:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
