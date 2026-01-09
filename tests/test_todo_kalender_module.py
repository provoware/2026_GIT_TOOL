import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "modules" / "todo_kalender" / "module.py"
    spec = importlib.util.spec_from_file_location("todo_kalender_module", module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TodoKalenderModuleTests(unittest.TestCase):
    def test_add_complete_and_calendar(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            config_path = base / "todo_kalender.json"
            data_path = base / "data.json"
            config_path.write_text(
                json.dumps(
                    {
                        "data_path": str(data_path),
                        "default_theme": "hell",
                        "themes": {
                            "hell": {
                                "planned": {
                                    "icon": "○",
                                    "color": "blau",
                                    "label": "Geplant",
                                },
                                "done": {
                                    "icon": "●",
                                    "color": "grün",
                                    "label": "Erledigt",
                                },
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

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

            complete_result = module.run({"action": "complete", "id": item_id, "context": context})
            self.assertEqual(complete_result["status"], "ok")
            self.assertEqual(complete_result["data"]["status"], "erledigt")


if __name__ == "__main__":
    unittest.main()
