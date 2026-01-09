import unittest
from datetime import date

from src.core.data_model import (
    DataModelError,
    TodoItem,
    TodoStatus,
    make_todo_id,
    parse_iso_date,
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


if __name__ == "__main__":
    unittest.main()
