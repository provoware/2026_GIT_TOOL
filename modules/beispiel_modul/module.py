"""Beispiel-Modul nach Projektstandard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class ModuleResult:
    ok: bool
    message: str


def validateInput(input_data: Any) -> Dict[str, str]:
    if input_data is None:
        return {"text": "Hallo"}
    if not isinstance(input_data, dict):
        raise ValueError("Eingabe ist ungültig. Erwartet: ein Wörterbuch (dict).")
    text = input_data.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Eingabe fehlt: 'text' muss ein nicht-leerer Text sein.")
    return {"text": text.strip()}


def validateOutput(output: Any) -> ModuleResult:
    if not isinstance(output, ModuleResult):
        raise ValueError("Ausgabe ist ungültig. Erwartet: ModuleResult.")
    if not output.message.strip():
        raise ValueError("Ausgabe ist ungültig. 'message' darf nicht leer sein.")
    return output


def init(context: Any | None = None) -> bool:
    if context is not None and not isinstance(context, dict):
        raise ValueError("Kontext ist ungültig. Erwartet: Wörterbuch (dict) oder None.")
    return True


def run(input_data: Any) -> ModuleResult:
    sanitized = validateInput(input_data)
    result = ModuleResult(ok=True, message=f"Beispiel: {sanitized['text']}")
    return validateOutput(result)


def exit() -> bool:
    return True
