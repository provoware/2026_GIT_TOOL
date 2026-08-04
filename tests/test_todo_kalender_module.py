import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
for import_path in (ROOT, ROOT / "system"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))


def load_module():
    module_path = ROOT / "modules" / "todo_kalender" / "module.py"
    spec = importlib.util.spec_from_file_location("todo_kalender_module", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_config(base: Path) -> tuple[Path, Path]:
    config_path = base / "todo_kalender.json"
    data_path = base / "data.json"
    config_path.write_text(
        json.dumps(
            {
                "data_path": str(data_path),
                "default_theme": "hell",
                "reminder_poll_seconds": 60,
                "themes": {
                    "hell": {
                        "planned": {"icon": "○", "color": "blau", "label": "Geplant"},
                        "done": {"icon": "●", "color": "grün", "label": "Erledigt"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path, data_path


class TodoKalenderModuleTests(unittest.TestCase):
    def test_add_complete_and_calendar(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path, _data_path = write_config(Path(tmpdir))
            context = {"config_path": str(config_path)}
            module.init(context)

            add_result = module.run(
                {
                    "action": "add",
                    "title": "Planung",
                    "planned_date": "2026-01-10",
                    "context": context,
                }
            )
            self.assertEqual(add_result["status"], "ok")
            item_id = add_result["data"]["id"]

            calendar_result = module.run(
                {
                    "action": "calendar",
                    "view": "monat",
                    "reference_date": "2026-01-10",
                    "context": context,
                }
            )
            self.assertEqual(calendar_result["status"], "ok")
            self.assertEqual(len(calendar_result["data"]["entries"]), 1)
            self.assertEqual(len(calendar_result["data"]["legend"]), 5)

            complete_result = module.run(
                {"action": "complete", "id": item_id, "context": context}
            )
            self.assertEqual(complete_result["status"], "ok")
            self.assertEqual(complete_result["data"]["status"], "erledigt")

    def test_colors_appointments_and_reminders_share_one_store(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path, data_path = write_config(Path(tmpdir))
            context = {"config_path": str(config_path)}
            module.init(context)
            legend = [
                {"id": "farbe-1", "title": "Arbeit", "color": "#2563eb"},
                {"id": "farbe-2", "title": "Familie", "color": "#16a34a"},
                {"id": "farbe-3", "title": "Wichtig", "color": "#dc2626"},
                {"id": "farbe-4", "title": "Gesundheit", "color": "#f59e0b"},
                {"id": "farbe-5", "title": "Freizeit", "color": "#9333ea"},
            ]
            legend_result = module.run(
                {"action": "set_legend", "legend": legend, "context": context}
            )
            self.assertEqual(legend_result["status"], "ok")

            marker_result = module.run(
                {
                    "action": "set_day_colors",
                    "date": "2026-08-04",
                    "color_ids": ["farbe-1", "farbe-2", "farbe-3", "farbe-4"],
                    "context": context,
                }
            )
            self.assertEqual(marker_result["status"], "ok")
            self.assertEqual(marker_result["data"]["summary"], "Arbeit · Familie · Wichtig · Gesundheit")

            too_many = module.run(
                {
                    "action": "set_day_colors",
                    "date": "2026-08-05",
                    "color_ids": [item["id"] for item in legend],
                    "context": context,
                }
            )
            self.assertEqual(too_many["status"], "error")

            appointment = module.run(
                {
                    "action": "add_appointment",
                    "title": "Besprechung",
                    "date": "2026-08-04",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "location": "Büro",
                    "color_id": "farbe-1",
                    "reminder_minutes": 30,
                    "context": context,
                }
            )
            self.assertEqual(appointment["status"], "ok")
            appointment_id = appointment["data"]["id"]
            self.assertEqual(appointment["data"]["reminder_at"], "2026-08-04T09:30:00")

            calendar_result = module.run(
                {
                    "action": "calendar",
                    "view": "monat",
                    "reference_date": "2026-08-04",
                    "now": "2026-08-04T09:45:00",
                    "context": context,
                }
            )
            data = calendar_result["data"]
            self.assertEqual(data["day_markers"][0]["color_ids"], ["farbe-1", "farbe-2", "farbe-3", "farbe-4"])
            self.assertEqual(data["appointments"][0]["title"], "Besprechung")
            self.assertEqual(data["reminders"]["due"][0]["id"], appointment_id)

            acknowledged = module.run(
                {"action": "acknowledge_reminder", "id": appointment_id, "context": context}
            )
            self.assertEqual(acknowledged["status"], "ok")
            reminders = module.run(
                {
                    "action": "list_reminders",
                    "now": "2026-08-04T09:45:00",
                    "context": context,
                }
            )
            self.assertEqual(reminders["data"]["due"], [])
            persisted = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(len(persisted["legend"]), 5)
            self.assertEqual(len(persisted["appointments"]), 1)


if __name__ == "__main__":
    unittest.main()
