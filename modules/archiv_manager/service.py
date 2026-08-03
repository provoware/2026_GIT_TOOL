"""Gemeinsame Geschäftslogik für Archiv-GUI, CLI und Modul-API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from .spelling import SpellingSuggestion, suggest_text
    from .storage import Archive, ArchiveEntry, ArchiveRepository, ArchiveStorageError, text_key
except ImportError:  # Laden als lose Moduldatei
    from spelling import SpellingSuggestion, suggest_text
    from storage import Archive, ArchiveEntry, ArchiveRepository, ArchiveStorageError, text_key


class ArchiveServiceError(ValueError):
    """Ungültiger Archivvorgang."""


@dataclass(frozen=True)
class PreparedItem:
    original: str
    value: str
    key: str
    spelling: SpellingSuggestion | None
    duplicate_in_input: bool
    duplicate_in_archive: bool


@dataclass(frozen=True)
class AddSummary:
    archive: Archive
    category: str
    requested_count: int
    inserted: tuple[ArchiveEntry, ...]
    duplicates: tuple[str, ...]
    spelling_suggestions: tuple[SpellingSuggestion, ...]


class ArchiveService:
    def __init__(self, database_path: Path | str, *, logger: logging.Logger | None = None) -> None:
        self.repository = ArchiveRepository(database_path)
        self.logger = logger or logging.getLogger("archiv_manager")

    @property
    def database_path(self) -> Path:
        return self.repository.database_path

    def list_archives(self) -> list[Archive]:
        return self.repository.list_archives()

    def get_archive(self, identifier: int | str) -> Archive:
        return self.repository.get_archive(identifier)

    def create_archive(
        self,
        name: str,
        description: str,
        *,
        split_on_comma: bool,
        source: str,
    ) -> Archive:
        archive = self.repository.create_archive(
            name,
            description,
            split_on_comma,
            source=source,
        )
        self.logger.info("Archiv angelegt: %s (%s)", archive.name, source)
        return archive

    def update_archive(
        self,
        archive_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        split_on_comma: bool | None = None,
        source: str,
    ) -> Archive:
        archive = self.repository.update_archive(
            archive_id,
            name=name,
            description=description,
            split_on_comma=split_on_comma,
            source=source,
        )
        self.logger.info("Archiv aktualisiert: %s (%s)", archive.name, source)
        return archive

    def delete_archive(self, archive_id: int, *, source: str) -> None:
        archive = self.get_archive(archive_id)
        self.repository.delete_archive(archive_id, source=source)
        self.logger.info("Archiv gelöscht: %s (%s)", archive.name, source)

    def list_categories(self, archive_id: int) -> list[str]:
        return self.repository.list_categories(archive_id)

    def prepare_add(
        self,
        archive_identifier: int | str,
        raw_text: str,
        *,
        apply_spelling: bool = False,
    ) -> tuple[Archive, tuple[PreparedItem, ...]]:
        archive = self.get_archive(archive_identifier)
        if not isinstance(raw_text, str) or not raw_text.strip():
            raise ArchiveServiceError("Die Eingabe ist leer.")
        raw_values = raw_text.split(",") if archive.split_on_comma else [raw_text]
        values = [" ".join(value.strip().split()) for value in raw_values]
        values = [value for value in values if value]
        if not values:
            raise ArchiveServiceError("Die Eingabe enthält keinen speicherbaren Text.")

        suggestions = [suggest_text(value) for value in values]
        final_values = [
            suggestion.suggested if apply_spelling and suggestion is not None else value
            for value, suggestion in zip(values, suggestions)
        ]
        keys = [text_key(value) for value in final_values]
        existing = self.repository.existing_keys(archive.id, keys)
        seen: set[str] = set()
        prepared: list[PreparedItem] = []
        for original, value, key, spelling in zip(values, final_values, keys, suggestions):
            duplicate_in_input = key in seen
            seen.add(key)
            prepared.append(
                PreparedItem(
                    original=original,
                    value=value,
                    key=key,
                    spelling=spelling,
                    duplicate_in_input=duplicate_in_input,
                    duplicate_in_archive=key in existing,
                )
            )
        return archive, tuple(prepared)

    def add_text(
        self,
        archive_identifier: int | str,
        raw_text: str,
        *,
        category: str = "Allgemein",
        source: str,
        apply_spelling: bool = False,
    ) -> AddSummary:
        archive, prepared = self.prepare_add(
            archive_identifier,
            raw_text,
            apply_spelling=apply_spelling,
        )
        accepted: list[str] = []
        duplicates: list[str] = []
        suggestions: list[SpellingSuggestion] = []
        for item in prepared:
            if item.spelling is not None:
                suggestions.append(item.spelling)
            if item.duplicate_in_input or item.duplicate_in_archive:
                duplicates.append(item.value)
                continue
            accepted.append(item.value)
        inserted = self.repository.insert_entries(
            archive.id,
            category or "Allgemein",
            accepted,
            source=source,
        )
        if duplicates:
            self.repository.record_event(
                source=source,
                action="duplicates_ignored",
                archive_id=archive.id,
                details={"values": duplicates, "count": len(duplicates)},
            )
        self.logger.info(
            "Archiveingabe verarbeitet: archiv=%s quelle=%s angefordert=%d gespeichert=%d duplikate=%d",
            archive.slug,
            source,
            len(prepared),
            len(inserted),
            len(duplicates),
        )
        return AddSummary(
            archive=archive,
            category=category or "Allgemein",
            requested_count=len(prepared),
            inserted=tuple(inserted),
            duplicates=tuple(duplicates),
            spelling_suggestions=tuple(suggestions),
        )

    def list_entries(
        self,
        archive_identifier: int | str,
        *,
        category: str | None = None,
        query: str = "",
    ) -> list[ArchiveEntry]:
        archive = self.get_archive(archive_identifier)
        return self.repository.list_entries(archive.id, category=category, query=query)

    def update_entry(
        self,
        entry_id: int,
        *,
        value: str,
        category: str,
        source: str,
    ) -> ArchiveEntry:
        suggestion = suggest_text(value)
        cleaned = suggestion.suggested if suggestion is not None else value
        entry = self.repository.update_entry(
            entry_id,
            value=cleaned,
            category=category,
            source=source,
        )
        self.logger.info("Archiveintrag aktualisiert: id=%d quelle=%s", entry_id, source)
        return entry

    def delete_entry(self, entry_id: int, *, source: str) -> None:
        self.repository.delete_entry(entry_id, source=source)
        self.logger.info("Archiveintrag gelöscht: id=%d quelle=%s", entry_id, source)

    def add_many(
        self,
        archive_identifier: int | str,
        values: Iterable[str],
        *,
        category: str,
        source: str,
    ) -> AddSummary:
        return self.add_text(
            archive_identifier,
            ", ".join(values),
            category=category,
            source=source,
        )


__all__ = [
    "AddSummary",
    "ArchiveService",
    "ArchiveServiceError",
    "ArchiveStorageError",
    "PreparedItem",
]
