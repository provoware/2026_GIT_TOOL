import unittest
from datetime import date, datetime

from src.core.data_model import (
    CharacterProfile,
    DataModelError,
    NoteEntry,
    TodoItem,
    TodoStatus,
    make_character_id,
    make_note_id,
    make_todo_id,
    parse_iso_date,
    parse_iso_datetime,
)


class DataModelTests(unittest.TestCase):
    def test_parse_iso_date_valid(self):
        parsed = parse_iso_date("2026-01-09", "planned_date")
        self.assertEqual(parsed, date(2026, 1, 9))

    def test_parse_iso_date_invalid(self):
        with self.assertRaises(DataModelError):
            parse_iso_date("2026/01/09", "planned_date")

    def test_make_todo_id_slugifies_title(self):
        item_id = make_todo_id("Planung Modul", date(2026, 1, 9))
        self.assertEqual(item_id, "20260109-planung-modul")

    def test_todo_item_roundtrip(self):
        item = TodoItem(
            item_id="20260109-test",
            title="Testaufgabe",
            planned_date=date(2026, 1, 9),
            status=TodoStatus.GEPLANT,
            done_date=None,
            notes="",
            source="test",
        )
        payload = item.to_dict()
        rebuilt = TodoItem.from_dict(payload)
        self.assertEqual(rebuilt.item_id, item.item_id)
        self.assertEqual(rebuilt.title, item.title)
        self.assertEqual(rebuilt.status, item.status)

    def test_parse_iso_datetime_valid(self):
        parsed = parse_iso_datetime("2026-01-09T10:30:00", "created_at")
        self.assertEqual(parsed, datetime(2026, 1, 9, 10, 30, 0))

    def test_parse_iso_datetime_invalid(self):
        with self.assertRaises(DataModelError):
            parse_iso_datetime("2026/01/09 10:00", "created_at")

    def test_note_entry_roundtrip(self):
        now = datetime(2026, 1, 9, 10, 30, 0)
        entry = NoteEntry(
            note_id=make_note_id("Testnotiz", now),
            title="Testnotiz",
            body="Inhalt",
            tags=["roman", "test"],
            created_at=now,
            updated_at=now,
            favorite=False,
            template_id="roman-idee",
            custom_fields={"quelle": "intern"},
        )
        payload = entry.to_dict()
        rebuilt = NoteEntry.from_dict(payload)
        self.assertEqual(rebuilt.note_id, entry.note_id)
        self.assertEqual(rebuilt.title, entry.title)
        self.assertEqual(rebuilt.tags, entry.tags)

    def test_character_profile_roundtrip(self):
        now = datetime(2026, 1, 9, 9, 0, 0)
        profile = CharacterProfile(
            character_id=make_character_id("Alex", now),
            name="Alex",
            role="Protagonist",
            archetype="Held",
            biography="Kurzvita",
            appearance="Beschreibung",
            traits=["mutig"],
            goals=["Ziel"],
            conflicts=["Konflikt"],
            relationships=["Partnerin"],
            voice_notes="Ruhige Stimme",
            tags=["hauptfigur"],
            favorite=True,
            template_id="roman-protagonist",
            custom_fields={"sprache": "Deutsch"},
            created_at=now,
            updated_at=now,
        )
        payload = profile.to_dict()
        rebuilt = CharacterProfile.from_dict(payload)
        self.assertEqual(rebuilt.character_id, profile.character_id)
        self.assertEqual(rebuilt.name, profile.name)
        self.assertEqual(rebuilt.tags, profile.tags)


if __name__ == "__main__":
    unittest.main()
