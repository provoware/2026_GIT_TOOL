#!/usr/bin/env python3
"""CLI: To-Do-Zeile prüfen und genau einen Agenten zuordnen."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.core.agent_assignment import (
    assign_agent_from_line,
    describe_agent,
    load_agent_rules,
)
from src.core.errors import AgentAssignmentError, TodoFormatError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Prüft eine To-Do-Zeile und ordnet genau einen Agenten zu "
            "(Regeln aus config/agent_rules.json)."
        )
    )
    parser.add_argument(
        "todo_line",
        help=(
            "To-Do-Zeile im Format: "
            "[ ] JJJJ-MM-TT | Bereich | Beschreibung | fertig wenn: Kriterium"
        ),
    )
    parser.add_argument(
        "--config",
        default="config/agent_rules.json",
        help="Pfad zur Agent-Regeldatei (Standard: config/agent_rules.json)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    ruleset = load_agent_rules(Path(args.config))
    try:
        rule = assign_agent_from_line(args.todo_line, ruleset)
    except (TodoFormatError, AgentAssignmentError) as error:
        print(f"Fehler: {error}")
        return 1

    print(f"Zugeordneter Agent: {describe_agent(rule)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
