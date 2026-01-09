"""Zuordnung von To-Do-Aufgaben zu genau einem Agenten."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .errors import AgentConflictError, AgentNotFoundError
from .todo_parser import TodoItem


@dataclass(frozen=True)
class AgentRule:
    agent_id: str
    label: str
    keywords: tuple[str, ...]

    def matches(self, text: str) -> bool:
        if not isinstance(text, str) or not text.strip():
            return False
        lower_text = text.lower()
        return any(keyword in lower_text for keyword in self.keywords)


@dataclass(frozen=True)
class AgentRuleset:
    version: str
    rules: tuple[AgentRule, ...]

    def match_agents(self, todo_item: TodoItem) -> list[AgentRule]:
        text = todo_item.normalized_text()
        return [rule for rule in self.rules if rule.matches(text)]


def load_agent_rules(config_path: Path) -> AgentRuleset:
    if not isinstance(config_path, Path):
        raise TypeError("config_path muss ein Path-Objekt sein.")
    if not config_path.exists():
        raise FileNotFoundError(f"Konfigurationsdatei fehlt: {config_path.as_posix()}")

    data = json.loads(config_path.read_text(encoding="utf-8"))
    version = data.get("version", "1.0")
    raw_rules = data.get("agents", [])
    if not raw_rules:
        raise ValueError("Keine Agent-Regeln in der Konfiguration gefunden.")

    rules: list[AgentRule] = []
    for entry in raw_rules:
        agent_id = str(entry.get("id", "")).strip()
        label = str(entry.get("label", "")).strip()
        keywords = tuple(str(word).lower().strip() for word in entry.get("keywords", []))
        if not agent_id or not label or not keywords:
            raise ValueError("Agent-Regel unvollständig. Bitte id, label und keywords setzen.")
        rules.append(AgentRule(agent_id=agent_id, label=label, keywords=keywords))

    return AgentRuleset(version=version, rules=tuple(rules))


def assign_agent(todo_item: TodoItem, ruleset: AgentRuleset) -> AgentRule:
    if not isinstance(todo_item, TodoItem):
        raise TypeError("todo_item muss ein TodoItem sein.")
    if not isinstance(ruleset, AgentRuleset):
        raise TypeError("ruleset muss ein AgentRuleset sein.")

    matches = ruleset.match_agents(todo_item)
    if not matches:
        raise AgentNotFoundError(
            "Kein passender Agent gefunden. Bitte To-Do präzisieren oder Regeln erweitern."
        )
    if len(matches) > 1:
        match_ids = ", ".join(rule.agent_id for rule in matches)
        raise AgentConflictError(
            "Mehrdeutige Zuordnung: Mehrere Agenten passen ("
            f"{match_ids}). Bitte To-Do eindeutiger formulieren."
        )
    return matches[0]


def assign_agent_from_line(line: str, ruleset: AgentRuleset) -> AgentRule:
    from .todo_parser import parse_todo_line

    todo_item = parse_todo_line(line)
    return assign_agent(todo_item, ruleset)


def describe_agent(rule: AgentRule) -> str:
    """Laienverständliche Kurzbeschreibung für die Ausgabe."""
    return f"{rule.label} ({rule.agent_id})"
