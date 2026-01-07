"""Eigene Fehlertypen für klare, laienverständliche Meldungen."""


class TodoFormatError(ValueError):
    """Fehler beim To-Do-Format (Formatprüfung fehlgeschlagen)."""


class AgentAssignmentError(ValueError):
    """Allgemeiner Fehler bei der Agent-Zuordnung."""


class AgentConflictError(AgentAssignmentError):
    """Mehrere Agenten passen, Zuordnung ist mehrdeutig."""


class AgentNotFoundError(AgentAssignmentError):
    """Kein Agent passt zu diesem To-Do."""
