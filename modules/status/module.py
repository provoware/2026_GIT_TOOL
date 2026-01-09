"""Status-Check-Modul nach Standard-Schnittstelle."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict


class ModuleError(Exception):
    """Fehler im Status-Check-Modul."""


@dataclass(frozen=True)
class ModuleContext:
    logger: logging.Logger


def validateInput(input_data: Dict[str, Any]) -> None:
    if not isinstance(input_data, dict):
        raise ModuleError("Eingabe muss ein Objekt (dict) sein.")
    if "request" not in input_data:
        raise ModuleError("Eingabe fehlt: Feld 'request'.")
    if not isinstance(input_data["request"], str) or not input_data["request"].strip():
        raise ModuleError("Eingabe-Feld 'request' muss Text enthalten.")


def validateOutput(output_data: Dict[str, Any]) -> None:
    if not isinstance(output_data, dict):
        raise ModuleError("Ausgabe muss ein Objekt (dict) sein.")
    if output_data.get("status") not in {"ok", "fehler"}:
        raise ModuleError("Ausgabe-Feld 'status' ist ungültig.")
    if "message" not in output_data:
        raise ModuleError("Ausgabe fehlt: Feld 'message'.")


def init(context: ModuleContext | None = None) -> ModuleContext:
    logger = logging.getLogger("module.status")
    if context is not None:
        if not isinstance(context, ModuleContext):
            raise ModuleError("Context ist ungültig.")
        logger = context.logger
    logger.debug("Status-Check: Initialisierung abgeschlossen.")
    return ModuleContext(logger=logger)


def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    validateInput(input_data)
    response = {
        "status": "ok",
        "message": f"Status bestätigt: {input_data['request']}",
    }
    validateOutput(response)
    return response


def exit(context: ModuleContext | None = None) -> None:
    logger = context.logger if isinstance(context, ModuleContext) else logging.getLogger("module.status")
    logger.debug("Status-Check: Abschluss durchgeführt.")
