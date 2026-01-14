from __future__ import annotations

"""Typen für die Modul-API (Input/Output/GUI-Daten)."""

from typing import Any, Dict, NotRequired, TypedDict


class ModuleUI(TypedDict, total=False):
    """Optionale UI-Daten für die Ausgabe eines Moduls."""

    title: str
    subtitle: NotRequired[str]
    description: NotRequired[str]
    hint: NotRequired[str]


ModuleInput = Dict[str, Any]


class ModuleOutput(TypedDict, total=False):
    """Standardisierte Ausgabe eines Moduls."""

    status: str
    message: str
    data: Dict[str, Any]
    ui: ModuleUI
