"""Bewusst einfache, konservative Rechtschreibhinweise ohne externe Abhängigkeit."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SpellingSuggestion:
    original: str
    suggested: str
    reasons: tuple[str, ...]


WORD_CORRECTIONS = {
    "efekt": "Effekt",
    "efekte": "Effekte",
    "effecte": "Effekte",
    "favoritten": "Favoriten",
    "stimmungn": "Stimmungen",
    "entwiklung": "Entwicklung",
    "entwiklungsstruktur": "Entwicklungsstruktur",
    "strucktur": "Struktur",
    "struckturen": "Strukturen",
    "linus": "Linux",
    "brainstormm": "Brainstorm",
    "genere": "Genre",
}


def _match_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement.lower()


def suggest_text(value: str) -> SpellingSuggestion | None:
    original = str(value)
    normalized = " ".join(original.strip().split())
    reasons: list[str] = []
    if normalized != original:
        reasons.append("überflüssige Leerzeichen")

    punctuation_fixed = re.sub(r"([!?.,;:])\1{1,}", r"\1", normalized)
    if punctuation_fixed != normalized:
        reasons.append("mehrfache Satzzeichen")
    normalized = punctuation_fixed

    def replace_word(match: re.Match[str]) -> str:
        word = match.group(0)
        correction = WORD_CORRECTIONS.get(word.casefold())
        if correction is None:
            return word
        reasons.append(f"möglicher Tippfehler: {word}")
        return _match_case(word, correction)

    corrected = re.sub(r"[A-Za-zÄÖÜäöüß]+", replace_word, normalized)
    if corrected == original or not reasons:
        return None
    return SpellingSuggestion(original=original, suggested=corrected, reasons=tuple(dict.fromkeys(reasons)))
