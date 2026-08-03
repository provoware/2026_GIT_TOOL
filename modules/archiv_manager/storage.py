"""Persistenz für gemeinsam genutzte Archive von GUI, CLI und Modul-API."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator, Sequence


class ArchiveStorageError(ValueError):
    """Ungültige Archivdaten oder fehlgeschlagene Datenbankoperation."""


@dataclass(frozen=True)
class Archive:
    id: int
    slug: str
    name: str
    description: str
    split_on_comma: bool
    is_default: bool


@dataclass(frozen=True)
class ArchiveEntry:
    id: int
    archive_id: int
    category: str
    value: str
    source: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class AuditEvent:
    id: int
    created_at: str
    source: str
    action: str
    archive_id: int | None
    details: dict[str, object]


DEFAULT_ARCHIVES: tuple[dict[str, object], ...] = (
    {
        "slug": "genres",
        "name": "Genres",
        "description": "Genrebegriffe für Geschichten, Medien, Projekte und kreative Einordnungen.",
        "split_on_comma": True,
    },
    {
        "slug": "stimmungen",
        "name": "Stimmungen",
        "description": "Atmosphären, emotionale Wirkungen und gewünschte Grundstimmungen.",
        "split_on_comma": True,
    },
    {
        "slug": "besondere-effekte",
        "name": "Besondere Effekte",
        "description": "Visuelle, akustische, erzählerische oder technische Spezialeffekte.",
        "split_on_comma": True,
    },
    {
        "slug": "favoriten",
        "name": "Favoriten",
        "description": "Bevorzugte Begriffe, Ideen, Bausteine und häufig verwendete Einträge.",
        "split_on_comma": True,
    },
    {
        "slug": "basis-entwicklungs-strukturen",
        "name": "Basis-Entwicklungs-Strukturen",
        "description": "Grundstrukturen, Abläufe, Muster und wiederverwendbare Entwicklungsbausteine.",
        "split_on_comma": False,
    },
    {
        "slug": "brainstorm",
        "name": "Brainstorm",
        "description": "Freie, noch nicht abschließend bewertete Ideen und zusammenhängende Gedanken.",
        "split_on_comma": False,
    },
    {
        "slug": "linux",
        "name": "Linux",
        "description": "Linux-Befehle, Werkzeuge, Lösungen, Konfigurationen und Merkhilfen.",
        "split_on_comma": True,
    },
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def text_key(value: str) -> str:
    if not isinstance(value, str):
        raise ArchiveStorageError("Der Textwert muss eine Zeichenkette sein.")
    normalized = unicodedata.normalize("NFKC", value)
    normalized = " ".join(normalized.strip().split())
    return normalized.casefold()


def slugify(value: str) -> str:
    key = unicodedata.normalize("NFKD", value)
    key = "".join(char for char in key if not unicodedata.combining(char))
    key = re.sub(r"[^a-zA-Z0-9]+", "-", key).strip("-").lower()
    if not key:
        raise ArchiveStorageError("Aus dem Archivnamen konnte keine gültige Kennung gebildet werden.")
    return key


class ArchiveRepository:
    """Kleine SQLite-Schicht mit atomaren Schreibvorgängen und Audit-Protokoll."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path).expanduser()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        try:
            connection = sqlite3.connect(self.database_path, timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute("PRAGMA journal_mode = WAL")
            yield connection
            connection.commit()
        except sqlite3.Error as exc:
            raise ArchiveStorageError(f"Archivdatenbank konnte nicht verarbeitet werden: {exc}") from exc
        finally:
            connection_object = locals().get("connection")
            if connection_object is not None:
                connection_object.close()

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS archives (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    name TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    description TEXT NOT NULL DEFAULT '',
                    split_on_comma INTEGER NOT NULL DEFAULT 1 CHECK(split_on_comma IN (0, 1)),
                    is_default INTEGER NOT NULL DEFAULT 0 CHECK(is_default IN (0, 1)),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archive_id INTEGER NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    name_key TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(archive_id, name_key)
                );

                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    archive_id INTEGER NOT NULL REFERENCES archives(id) ON DELETE CASCADE,
                    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                    value TEXT NOT NULL,
                    value_key TEXT NOT NULL,
                    source TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(archive_id, value_key)
                );

                CREATE INDEX IF NOT EXISTS idx_entries_archive_category
                    ON entries(archive_id, category_id);
                CREATE INDEX IF NOT EXISTS idx_entries_archive_value
                    ON entries(archive_id, value_key);

                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    action TEXT NOT NULL,
                    archive_id INTEGER REFERENCES archives(id) ON DELETE SET NULL,
                    details_json TEXT NOT NULL
                );
                """
            )
            now = utc_now()
            for item in DEFAULT_ARCHIVES:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO archives
                        (slug, name, description, split_on_comma, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    """,
                    (
                        item["slug"],
                        item["name"],
                        item["description"],
                        int(bool(item["split_on_comma"])),
                        now,
                        now,
                    ),
                )
            archive_rows = connection.execute("SELECT id FROM archives").fetchall()
            for row in archive_rows:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO categories (archive_id, name, name_key, created_at)
                    VALUES (?, 'Allgemein', 'allgemein', ?)
                    """,
                    (int(row["id"]), now),
                )

    def list_archives(self) -> list[Archive]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, slug, name, description, split_on_comma, is_default
                FROM archives
                ORDER BY is_default DESC, name COLLATE NOCASE
                """
            ).fetchall()
        return [self._archive_from_row(row) for row in rows]

    def get_archive(self, identifier: int | str) -> Archive:
        with self._connect() as connection:
            if isinstance(identifier, int) and not isinstance(identifier, bool):
                row = connection.execute(
                    """SELECT id, slug, name, description, split_on_comma, is_default
                       FROM archives WHERE id = ?""",
                    (identifier,),
                ).fetchone()
            elif isinstance(identifier, str) and identifier.strip():
                value = identifier.strip()
                row = connection.execute(
                    """SELECT id, slug, name, description, split_on_comma, is_default
                       FROM archives WHERE slug = ? COLLATE NOCASE OR name = ? COLLATE NOCASE""",
                    (value, value),
                ).fetchone()
            else:
                raise ArchiveStorageError("Archivkennung ist leer oder ungültig.")
        if row is None:
            raise ArchiveStorageError(f"Archiv wurde nicht gefunden: {identifier}")
        return self._archive_from_row(row)

    def create_archive(
        self,
        name: str,
        description: str,
        split_on_comma: bool,
        *,
        source: str,
    ) -> Archive:
        cleaned_name = " ".join(str(name).strip().split())
        cleaned_description = " ".join(str(description).strip().split())
        if not cleaned_name:
            raise ArchiveStorageError("Der Archivname darf nicht leer sein.")
        if not isinstance(split_on_comma, bool):
            raise ArchiveStorageError("Der Komma-Modus muss ein Wahrheitswert sein.")
        slug = slugify(cleaned_name)
        now = utc_now()
        with self._connect() as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO archives
                        (slug, name, description, split_on_comma, is_default, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 0, ?, ?)
                    """,
                    (slug, cleaned_name, cleaned_description, int(split_on_comma), now, now),
                )
            except sqlite3.IntegrityError as exc:
                raise ArchiveStorageError("Ein Archiv mit diesem Namen oder dieser Kennung existiert bereits.") from exc
            archive_id = int(cursor.lastrowid)
            connection.execute(
                """INSERT INTO categories (archive_id, name, name_key, created_at)
                   VALUES (?, 'Allgemein', 'allgemein', ?)""",
                (archive_id, now),
            )
            self._audit_in_connection(
                connection,
                source=source,
                action="archive_created",
                archive_id=archive_id,
                details={"name": cleaned_name, "split_on_comma": split_on_comma},
            )
        return self.get_archive(archive_id)

    def update_archive(
        self,
        archive_id: int,
        *,
        name: str | None = None,
        description: str | None = None,
        split_on_comma: bool | None = None,
        source: str,
    ) -> Archive:
        current = self.get_archive(archive_id)
        new_name = current.name if name is None else " ".join(name.strip().split())
        new_description = current.description if description is None else " ".join(description.strip().split())
        new_split = current.split_on_comma if split_on_comma is None else split_on_comma
        if not new_name:
            raise ArchiveStorageError("Der Archivname darf nicht leer sein.")
        if not isinstance(new_split, bool):
            raise ArchiveStorageError("Der Komma-Modus muss ein Wahrheitswert sein.")
        new_slug = current.slug if current.is_default else slugify(new_name)
        with self._connect() as connection:
            try:
                connection.execute(
                    """
                    UPDATE archives
                    SET slug = ?, name = ?, description = ?, split_on_comma = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (new_slug, new_name, new_description, int(new_split), utc_now(), archive_id),
                )
            except sqlite3.IntegrityError as exc:
                raise ArchiveStorageError("Ein Archiv mit diesem Namen oder dieser Kennung existiert bereits.") from exc
            self._audit_in_connection(
                connection,
                source=source,
                action="archive_updated",
                archive_id=archive_id,
                details={
                    "name": new_name,
                    "description": new_description,
                    "split_on_comma": new_split,
                },
            )
        return self.get_archive(archive_id)

    def delete_archive(self, archive_id: int, *, source: str) -> None:
        archive = self.get_archive(archive_id)
        if archive.is_default:
            raise ArchiveStorageError("Ein Standardarchiv kann nicht gelöscht werden.")
        with self._connect() as connection:
            self._audit_in_connection(
                connection,
                source=source,
                action="archive_deleted",
                archive_id=archive_id,
                details={"name": archive.name},
            )
            connection.execute("DELETE FROM archives WHERE id = ?", (archive_id,))

    def list_categories(self, archive_id: int) -> list[str]:
        self.get_archive(archive_id)
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT name FROM categories WHERE archive_id = ? ORDER BY name COLLATE NOCASE""",
                (archive_id,),
            ).fetchall()
        return [str(row["name"]) for row in rows]

    def ensure_category(self, archive_id: int, name: str, connection: sqlite3.Connection | None = None) -> int:
        cleaned = " ".join(str(name).strip().split()) or "Allgemein"
        key = text_key(cleaned)

        def operation(active: sqlite3.Connection) -> int:
            active.execute(
                """INSERT OR IGNORE INTO categories (archive_id, name, name_key, created_at)
                   VALUES (?, ?, ?, ?)""",
                (archive_id, cleaned, key, utc_now()),
            )
            row = active.execute(
                "SELECT id FROM categories WHERE archive_id = ? AND name_key = ?",
                (archive_id, key),
            ).fetchone()
            if row is None:
                raise ArchiveStorageError("Kategorie konnte nicht angelegt oder gefunden werden.")
            return int(row["id"])

        if connection is not None:
            return operation(connection)
        with self._connect() as active_connection:
            return operation(active_connection)

    def existing_keys(self, archive_id: int, keys: Sequence[str]) -> set[str]:
        if not keys:
            return set()
        placeholders = ",".join("?" for _ in keys)
        with self._connect() as connection:
            rows = connection.execute(
                f"SELECT value_key FROM entries WHERE archive_id = ? AND value_key IN ({placeholders})",
                (archive_id, *keys),
            ).fetchall()
        return {str(row["value_key"]) for row in rows}

    def insert_entries(
        self,
        archive_id: int,
        category: str,
        values: Iterable[str],
        *,
        source: str,
    ) -> list[ArchiveEntry]:
        archive = self.get_archive(archive_id)
        prepared = [(" ".join(value.strip().split()), text_key(value)) for value in values]
        prepared = [(value, key) for value, key in prepared if value]
        if not prepared:
            return []
        inserted_ids: list[int] = []
        now = utc_now()
        with self._connect() as connection:
            category_id = self.ensure_category(archive.id, category, connection)
            for value, key in prepared:
                try:
                    cursor = connection.execute(
                        """
                        INSERT INTO entries
                            (archive_id, category_id, value, value_key, source, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (archive.id, category_id, value, key, source, now, now),
                    )
                except sqlite3.IntegrityError:
                    continue
                inserted_ids.append(int(cursor.lastrowid))
            self._audit_in_connection(
                connection,
                source=source,
                action="entries_added",
                archive_id=archive.id,
                details={
                    "category": category or "Allgemein",
                    "requested": len(prepared),
                    "inserted": len(inserted_ids),
                    "values": [value for value, _key in prepared],
                },
            )
        if not inserted_ids:
            return []
        placeholders = ",".join("?" for _ in inserted_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT e.id, e.archive_id, c.name AS category, e.value, e.source,
                       e.created_at, e.updated_at
                FROM entries e JOIN categories c ON c.id = e.category_id
                WHERE e.id IN ({placeholders}) ORDER BY e.id
                """,
                inserted_ids,
            ).fetchall()
        return [self._entry_from_row(row) for row in rows]

    def list_entries(
        self,
        archive_id: int,
        *,
        category: str | None = None,
        query: str = "",
    ) -> list[ArchiveEntry]:
        self.get_archive(archive_id)
        clauses = ["e.archive_id = ?"]
        parameters: list[object] = [archive_id]
        if category and category != "Alle Kategorien":
            clauses.append("c.name_key = ?")
            parameters.append(text_key(category))
        cleaned_query = " ".join(query.strip().split())
        if cleaned_query:
            clauses.append("e.value LIKE ? COLLATE NOCASE")
            parameters.append(f"%{cleaned_query}%")
        where = " AND ".join(clauses)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT e.id, e.archive_id, c.name AS category, e.value, e.source,
                       e.created_at, e.updated_at
                FROM entries e JOIN categories c ON c.id = e.category_id
                WHERE {where}
                ORDER BY c.name COLLATE NOCASE, e.value COLLATE NOCASE
                """,
                parameters,
            ).fetchall()
        return [self._entry_from_row(row) for row in rows]

    def get_entry(self, entry_id: int) -> ArchiveEntry:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT e.id, e.archive_id, c.name AS category, e.value, e.source,
                       e.created_at, e.updated_at
                FROM entries e JOIN categories c ON c.id = e.category_id
                WHERE e.id = ?
                """,
                (entry_id,),
            ).fetchone()
        if row is None:
            raise ArchiveStorageError(f"Archiveintrag wurde nicht gefunden: {entry_id}")
        return self._entry_from_row(row)

    def update_entry(
        self,
        entry_id: int,
        *,
        value: str,
        category: str,
        source: str,
    ) -> ArchiveEntry:
        current = self.get_entry(entry_id)
        cleaned = " ".join(value.strip().split())
        if not cleaned:
            raise ArchiveStorageError("Der Eintrag darf nicht leer sein.")
        key = text_key(cleaned)
        with self._connect() as connection:
            category_id = self.ensure_category(current.archive_id, category, connection)
            try:
                connection.execute(
                    """
                    UPDATE entries
                    SET category_id = ?, value = ?, value_key = ?, source = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (category_id, cleaned, key, source, utc_now(), entry_id),
                )
            except sqlite3.IntegrityError as exc:
                raise ArchiveStorageError("Dieser Eintrag ist im Archiv bereits vorhanden.") from exc
            self._audit_in_connection(
                connection,
                source=source,
                action="entry_updated",
                archive_id=current.archive_id,
                details={"entry_id": entry_id, "old_value": current.value, "new_value": cleaned},
            )
        return self.get_entry(entry_id)

    def delete_entry(self, entry_id: int, *, source: str) -> None:
        current = self.get_entry(entry_id)
        with self._connect() as connection:
            connection.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
            self._audit_in_connection(
                connection,
                source=source,
                action="entry_deleted",
                archive_id=current.archive_id,
                details={"entry_id": entry_id, "value": current.value},
            )

    def record_event(
        self,
        *,
        source: str,
        action: str,
        archive_id: int | None,
        details: dict[str, object],
    ) -> None:
        with self._connect() as connection:
            self._audit_in_connection(
                connection,
                source=source,
                action=action,
                archive_id=archive_id,
                details=details,
            )

    def list_audit_events(self, limit: int = 100) -> list[AuditEvent]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            raise ArchiveStorageError("Das Audit-Limit muss eine positive Ganzzahl sein.")
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, created_at, source, action, archive_id, details_json
                   FROM audit_events ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            AuditEvent(
                id=int(row["id"]),
                created_at=str(row["created_at"]),
                source=str(row["source"]),
                action=str(row["action"]),
                archive_id=None if row["archive_id"] is None else int(row["archive_id"]),
                details=json.loads(str(row["details_json"])),
            )
            for row in rows
        ]

    @staticmethod
    def _audit_in_connection(
        connection: sqlite3.Connection,
        *,
        source: str,
        action: str,
        archive_id: int | None,
        details: dict[str, object],
    ) -> None:
        connection.execute(
            """
            INSERT INTO audit_events (created_at, source, action, archive_id, details_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (utc_now(), source, action, archive_id, json.dumps(details, ensure_ascii=False, sort_keys=True)),
        )

    @staticmethod
    def _archive_from_row(row: sqlite3.Row) -> Archive:
        return Archive(
            id=int(row["id"]),
            slug=str(row["slug"]),
            name=str(row["name"]),
            description=str(row["description"]),
            split_on_comma=bool(row["split_on_comma"]),
            is_default=bool(row["is_default"]),
        )

    @staticmethod
    def _entry_from_row(row: sqlite3.Row) -> ArchiveEntry:
        return ArchiveEntry(
            id=int(row["id"]),
            archive_id=int(row["archive_id"]),
            category=str(row["category"]),
            value=str(row["value"]),
            source=str(row["source"]),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )
