#!/usr/bin/env python3
"""Zeigt interne Standards in einfacher Sprache an."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

DEFAULT_ROOT = Path(__file__).resolve().parents[1]


class StandardsViewerError(Exception):
    """Allgemeiner Fehler für die Standards-Anzeige."""


@dataclass(frozen=True)
class StandardsSection:
    key: str
    title: str
    path: Path


def _ensure_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StandardsViewerError(f"{label} ist leer oder ungültig.")
    return value.strip()


def _build_sections(root: Path) -> List[StandardsSection]:
    if not isinstance(root, Path):
        raise StandardsViewerError("root ist kein Pfad (Path).")
    return [
        StandardsSection("standards", "Interne Standards", root / "standards.md"),
        StandardsSection("styleguide", "Styleguide (PEP8 + Projektregeln)", root / "STYLEGUIDE.md"),
    ]


def _load_section(section: StandardsSection) -> str:
    if not section.path.exists():
        raise StandardsViewerError(f"Datei fehlt: {section.path}")
    content = section.path.read_text(encoding="utf-8").strip()
    if not content:
        raise StandardsViewerError(f"Datei ist leer: {section.path}")
    return content


def _render_section(section: StandardsSection) -> str:
    body = _load_section(section)
    header = f"{section.title}\n" + ("=" * len(section.title))
    return "\n".join([header, "", body, ""])


def list_sections(sections: Iterable[StandardsSection]) -> str:
    items = [f"- {section.key}: {section.title}" for section in sections]
    return "Verfügbare Bereiche:\n" + "\n".join(items)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zeigt interne Standards (Standards + Styleguide) an.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Projekt-Root (Standard: Repository-Wurzel).",
    )
    parser.add_argument(
        "--section",
        default="all",
        help="Bereich anzeigen: standards, styleguide oder all (Standard: all).",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Nur die verfügbaren Bereiche anzeigen.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    sections = _build_sections(args.root)

    if args.list:
        print(list_sections(sections))
        return 0

    selection = _ensure_text(args.section, "section").lower()
    if selection == "all":
        output = "\n".join(_render_section(section) for section in sections)
        print(output.rstrip())
        return 0

    for section in sections:
        if section.key == selection:
            print(_render_section(section).rstrip())
            return 0

    available = ", ".join(section.key for section in sections)
    raise StandardsViewerError(f"Unbekannter Bereich: {selection}. Verfügbar: {available}.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except StandardsViewerError as exc:
        print(f"Fehler: {exc}")
        raise SystemExit(2)
