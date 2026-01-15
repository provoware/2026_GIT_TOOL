#!/usr/bin/env python3
"""Globales Undo-/Redo-System für Aktionen im Tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


class UndoRedoError(Exception):
    """Fehler im Undo-/Redo-System."""


ActionCallback = Callable[[], None]


@dataclass(frozen=True)
class UndoRedoAction:
    name: str
    undo: ActionCallback
    redo: ActionCallback
    metadata: dict = field(default_factory=dict)


class UndoRedoManager:
    def __init__(self, limit: int = 100) -> None:
        if not isinstance(limit, int) or limit < 1:
            raise UndoRedoError("limit ist ungültig.")
        self._limit = limit
        self._undo_stack: List[UndoRedoAction] = []
        self._redo_stack: List[UndoRedoAction] = []

    @property
    def limit(self) -> int:
        return self._limit

    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def record(self, action: UndoRedoAction) -> None:
        if not isinstance(action, UndoRedoAction):
            raise UndoRedoError("action ist keine UndoRedoAction.")
        if not callable(action.undo) or not callable(action.redo):
            raise UndoRedoError("Undo/Redo-Funktion fehlt.")
        self._undo_stack.append(action)
        self._redo_stack.clear()
        if len(self._undo_stack) > self._limit:
            self._undo_stack.pop(0)

    def undo(self) -> UndoRedoAction:
        if not self._undo_stack:
            raise UndoRedoError("Kein Undo verfügbar.")
        action = self._undo_stack.pop()
        action.undo()
        self._redo_stack.append(action)
        return action

    def redo(self) -> UndoRedoAction:
        if not self._redo_stack:
            raise UndoRedoError("Kein Redo verfügbar.")
        action = self._redo_stack.pop()
        action.redo()
        self._undo_stack.append(action)
        return action

    def peek_undo(self) -> Optional[UndoRedoAction]:
        return self._undo_stack[-1] if self._undo_stack else None

    def peek_redo(self) -> Optional[UndoRedoAction]:
        return self._redo_stack[-1] if self._redo_stack else None
