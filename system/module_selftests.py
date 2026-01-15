#!/usr/bin/env python3
"""Modul-Selbsttests mit klaren Statusmeldungen."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List

import module_checker
from event_bus import EVENT_BUS
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center
from module_loader import MODULE_LOADER, ModuleLoaderError

CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "modules.json"
SELFTEST_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "module_selftests.json"


class ModuleSelftestError(Exception):
    """Fehler beim Modul-Selbsttest."""


@dataclass(frozen=True)
class SelftestResult:
    module_id: str
    name: str
    status: str
    message: str


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise ModuleSelftestError(f"Selbsttest-Konfiguration fehlt: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModuleSelftestError(f"Selbsttest-Konfiguration ist ungültig: {path}") from exc
    if not isinstance(data, dict):
        raise ModuleSelftestError("Selbsttest-Konfiguration ist kein Objekt (dict).")
    return data


def load_test_inputs(path: Path) -> Dict[str, Any]:
    data = _load_json(path)
    testcases = data.get("testcases")
    if not isinstance(testcases, dict):
        raise ModuleSelftestError("testcases fehlen oder sind ungültig.")
    return testcases


def _load_module(entry_path: Path, module_id: str):
    try:
        return MODULE_LOADER.load(module_id, entry_path)
    except ModuleLoaderError as exc:
        raise ModuleSelftestError(str(exc)) from exc


def _run_module_test(entry_path: Path, module_id: str, input_data: Any) -> None:
    module = _load_module(entry_path, module_id)
    if hasattr(module, "init"):
        module.init()
    if not hasattr(module, "run"):
        raise ModuleSelftestError("Modul hat keine run-Funktion.")
    result = module.run(input_data)
    if result is None:
        raise ModuleSelftestError("Modul-Test lieferte keine Ausgabe.")
    if hasattr(module, "exit"):
        module.exit()


def run_selftests(
    modules_config: Path = CONFIG_DEFAULT,
    selftest_config: Path = SELFTEST_DEFAULT,
) -> List[SelftestResult]:
    testcases = load_test_inputs(selftest_config)
    entries = module_checker.load_modules(modules_config)
    results: List[SelftestResult] = []
    for entry in entries:
        EVENT_BUS.emit("module_selftest_start", {"module_id": entry.module_id})
        if not entry.enabled:
            results.append(
                SelftestResult(
                    module_id=entry.module_id,
                    name=entry.name,
                    status="übersprungen",
                    message="Modul ist deaktiviert.",
                )
            )
            continue
        testcase = testcases.get(entry.module_id)
        if testcase is None:
            results.append(
                SelftestResult(
                    module_id=entry.module_id,
                    name=entry.name,
                    status="übersprungen",
                    message="Kein Testfall hinterlegt.",
                )
            )
            continue
        try:
            manifest = module_checker.load_manifest(entry.path)
            entry_path = module_checker.resolve_entry_path(entry.path, manifest.entry)
            _run_module_test(entry_path, entry.module_id, testcase)
        except Exception as exc:
            results.append(
                SelftestResult(
                    module_id=entry.module_id,
                    name=entry.name,
                    status="fehler",
                    message=str(exc),
                )
            )
            EVENT_BUS.emit(
                "module_selftest_result",
                {"module_id": entry.module_id, "status": "fehler", "message": str(exc)},
            )
        else:
            results.append(
                SelftestResult(
                    module_id=entry.module_id,
                    name=entry.name,
                    status="ok",
                    message="Selbsttest erfolgreich.",
                )
            )
            EVENT_BUS.emit(
                "module_selftest_result",
                {
                    "module_id": entry.module_id,
                    "status": "ok",
                    "message": "Selbsttest erfolgreich.",
                },
            )
    return results


def render_results(results: Iterable[SelftestResult]) -> str:
    lines = ["Modul-Selbsttests:"]
    for result in results:
        lines.append(f"- {result.name} ({result.module_id}): {result.status} – {result.message}")
    return "\n".join(lines).rstrip() + "\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Modul-Selbsttests mit klarer Ausgabe.",
    )
    parser.add_argument("--config", type=Path, default=CONFIG_DEFAULT)
    parser.add_argument("--selftests", type=Path, default=SELFTEST_DEFAULT)
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging_center(args.debug)
    logger = get_logger("module_selftests")
    try:
        results = run_selftests(args.config, args.selftests)
    except (ModuleSelftestError, module_checker.ModuleCheckError) as exc:
        logger.error("Modul-Selbsttests konnten nicht starten: %s", exc)
        return 2

    print(render_results(results), end="")
    if any(result.status == "fehler" for result in results):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
