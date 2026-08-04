#!/usr/bin/env python3
"""Modul-API-Validator: Prüft Pflicht-Exports ohne Modul-Import."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

from config_utils import ensure_path


class ModuleApiError(ValueError):
    """Fehler im Modul-API-Validator."""


REQUIRED_FUNCTIONS: Dict[str, str] = {
    "run": "Pflichtfunktion 'run' fehlt.",
    "validateInput": "Pflichtfunktion 'validateInput' fehlt.",
    "validateOutput": "Pflichtfunktion 'validateOutput' fehlt.",
}


def _assigned_names(node: ast.Assign | ast.AnnAssign) -> set[str]:
    names: set[str] = set()
    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
    for target in targets:
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            names.update(
                item.id for item in target.elts if isinstance(item, ast.Name)
            )
    return names


def _exported_names(tree: ast.Module) -> set[str]:
    exports: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            exports.update(_assigned_names(node))
        elif isinstance(node, ast.ImportFrom):
            exports.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            exports.update(alias.asname or alias.name.split(".", 1)[0] for alias in node.names)
    return exports


def validate_module_api(entry_path: Path) -> List[str]:
    ensure_path(entry_path, "entry_path", ModuleApiError)

    if not entry_path.exists():
        return [f"Modul-API-Check: Modul-Datei fehlt: {entry_path}."]
    if entry_path.suffix.lower() != ".py":
        return [
            "Modul-API-Check: Entry-Datei ist keine Python-Datei: "
            f"{entry_path.name}."
        ]
    try:
        source = entry_path.read_text(encoding="utf-8")
    except OSError:
        return [
            f"Modul-API-Check: Modul-Datei kann nicht gelesen werden: {entry_path}."
        ]
    try:
        tree = ast.parse(source, filename=str(entry_path))
    except SyntaxError:
        return [f"Modul-API-Check: Syntaxfehler in {entry_path}. Bitte Datei prüfen."]

    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    exports = _exported_names(tree)
    issues: List[str] = []
    for name, message in REQUIRED_FUNCTIONS.items():
        if name not in exports:
            issues.append(f"Modul-API-Check: {message}")

    run_func = functions.get("run")
    if run_func is not None:
        has_args = bool(run_func.args.args)
        has_varargs = run_func.args.vararg is not None
        if not has_args and not has_varargs:
            issues.append(
                "Modul-API-Check: Funktion 'run' braucht mindestens ein Argument "
                "(input_data = Eingabe)."
            )

    return issues
