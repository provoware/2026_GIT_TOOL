#!/usr/bin/env python3
"""Test-Sperre: Führt Tests erst nach einer vollständigen Runde aus."""

from __future__ import annotations

import argparse
import json
import logging
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List

from config_utils import ensure_path
from logging_center import get_logger
from logging_center import setup_logging as setup_logging_center

CONFIG_DEFAULT = Path(__file__).resolve().parents[1] / "config" / "test_gate.json"
TASK_PATTERN = re.compile(r"^\[(x|X| )\]\s+")
DONE_PATTERN = re.compile(r"^\[(x|X)\]\s+")


class TestGateError(Exception):
    """Allgemeiner Fehler für die Test-Sperre."""


@dataclass(frozen=True)
class TestGateConfig:
    threshold: int
    todo_path: Path
    state_path: Path
    tests_command: List[str]


@dataclass(frozen=True)
class TestState:
    last_done: int
    last_run: str | None
    last_result: str | None


def _load_json(path: Path) -> dict:
    if not path.exists():
        raise TestGateError(f"Konfiguration fehlt: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TestGateError(f"Konfiguration ist kein gültiges JSON: {path}") from exc


def _resolve_path(root: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else root / candidate


def load_config(config_path: Path | None = None) -> TestGateConfig:
    config_file = config_path or CONFIG_DEFAULT
    ensure_path(config_file, "config_path", TestGateError)
    data = _load_json(config_file)

    threshold = data.get("threshold", 9)
    if not isinstance(threshold, int) or threshold <= 0:
        raise TestGateError("Schwelle (threshold) muss eine positive Zahl sein.")

    todo_path = data.get("todo_path", "todo.txt")
    state_path = data.get("state_path", "data/test_state.json")
    tests_command = data.get(
        "tests_command",
        ["python", "-m", "unittest", "discover", "-s", "tests"],
    )
    if not isinstance(tests_command, list) or not tests_command:
        raise TestGateError("tests_command muss eine nicht-leere Liste sein.")
    if not all(isinstance(item, str) and item for item in tests_command):
        raise TestGateError("tests_command darf nur aus Texten bestehen.")

    root = Path(__file__).resolve().parents[1]
    return TestGateConfig(
        threshold=threshold,
        todo_path=_resolve_path(root, str(todo_path)),
        state_path=_resolve_path(root, str(state_path)),
        tests_command=list(tests_command),
    )


def load_state(state_path: Path) -> TestState:
    ensure_path(state_path, "state_path", TestGateError)
    if not state_path.exists():
        return TestState(last_done=0, last_run=None, last_result=None)
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise TestGateError(f"Statusdatei ist kein gültiges JSON: {state_path}") from exc
    last_done = data.get("last_done", 0)
    if not isinstance(last_done, int) or last_done < 0:
        raise TestGateError("Statusdatei: last_done ist ungültig.")
    last_run = data.get("last_run")
    if last_run is not None and not isinstance(last_run, str):
        raise TestGateError("Statusdatei: last_run ist ungültig.")
    last_result = data.get("last_result")
    if last_result is not None and not isinstance(last_result, str):
        raise TestGateError("Statusdatei: last_result ist ungültig.")
    return TestState(last_done=last_done, last_run=last_run, last_result=last_result)


def save_state(state_path: Path, last_done: int, result: str) -> None:
    ensure_path(state_path, "state_path", TestGateError)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_done": last_done,
        "last_run": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "last_result": result,
    }
    state_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def count_tasks(lines: Iterable[str]) -> tuple[int, int]:
    total = 0
    done = 0
    for line in lines:
        stripped = line.strip()
        if not TASK_PATTERN.match(stripped):
            continue
        total += 1
        if DONE_PATTERN.match(stripped):
            done += 1
    return total, done


def evaluate_gate(done_count: int, last_done: int, threshold: int) -> tuple[bool, int]:
    if done_count < last_done:
        logging.warning(
            "Hinweis: Erledigt-Zähler ist kleiner als letzter Teststand (%s < %s).",
            done_count,
            last_done,
        )
        last_done = 0
    diff = done_count - last_done
    return diff >= threshold, diff


def run_tests(command: List[str]) -> int:
    logging.info("Tests werden gestartet: %s", " ".join(command))
    result = subprocess.run(command, check=False)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test-Sperre: Tests erst nach kompletter Runde ausführen.",
    )
    parser.add_argument("--config", type=Path, default=None, help="Pfad zur Konfiguration (JSON)")
    parser.add_argument("--debug", action="store_true", help="Debug-Modus aktivieren")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    setup_logging_center(args.debug)
    logger = get_logger("test_gate")

    try:
        config = load_config(args.config)
        state = load_state(config.state_path)
    except TestGateError as exc:
        logger.error("Test-Sperre konnte nicht gestartet werden: %s", exc)
        return 2

    if not config.todo_path.exists():
        logger.error("To-Do-Datei nicht gefunden: %s", config.todo_path)
        return 2

    todo_lines = config.todo_path.read_text(encoding="utf-8").splitlines()
    total, done = count_tasks(todo_lines)
    should_run, diff = evaluate_gate(done, state.last_done, config.threshold)

    logger.info("Stand: %s erledigt von %s Aufgaben.", done, total)
    if not should_run:
        logger.info(
            "Tests werden erst nach kompletter Runde ausgeführt: %s von %s erledigt.",
            diff,
            config.threshold,
        )
        return 0

    exit_code = run_tests(config.tests_command)
    if exit_code != 0:
        logger.error("Tests fehlgeschlagen (Exit-Code: %s).", exit_code)
        save_state(config.state_path, state.last_done, "fehlgeschlagen")
        return exit_code

    save_state(config.state_path, done, "ok")
    logger.info("Tests erfolgreich. Status aktualisiert.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
