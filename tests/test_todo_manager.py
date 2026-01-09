import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from todo_manager import (
    Progress,
    archive_completed_tasks,
    calculate_progress,
    write_progress_report,
)


class TodoManagerTests(unittest.TestCase):
    def test_calculate_progress_handles_done_and_open_lines(self):
        lines = ["[ ] Erste Aufgabe\n", "[x] Erledigt\n", "Hinweis ohne Status\n"]
        progress = calculate_progress(lines)
        self.assertEqual(progress.total, 2)
        self.assertEqual(progress.done, 1)
        self.assertEqual(progress.percent, 50.0)

    def test_archive_completed_tasks_moves_done_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            todo_path = base / "todo.txt"
            archive_path = base / "archive.txt"
            todo_path.write_text("[x] Fertig\n[ ] Offen\n", encoding="utf-8")

            archived, remaining = archive_completed_tasks(todo_path, archive_path)

            self.assertEqual(archived, 1)
            self.assertEqual(remaining, 1)
            self.assertIn("[ ] Offen", todo_path.read_text(encoding="utf-8"))
            archive_content = archive_path.read_text(encoding="utf-8")
            self.assertIn("Fertig", archive_content)
            self.assertIn("archiviert", archive_content)

    def test_write_progress_report_creates_progress_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "PROGRESS.md"
            progress = Progress(total=5, done=2)

            write_progress_report(progress, progress_path)

            content = progress_path.read_text(encoding="utf-8")
            self.assertIn("- Gesamt: 5 Tasks", content)
            self.assertIn("- Erledigt: 2 Tasks", content)
            self.assertIn("- Offen: 3 Tasks", content)
