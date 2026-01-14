import sys
import tempfile
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from doc_updater import update_docs


class DocUpdaterTests(unittest.TestCase):
    def test_update_docs_rewrites_status_block(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "README.md").write_text(
                "# README\n\n<!-- AUTO-STATUS:START -->\nAlt\n<!-- AUTO-STATUS:END -->\n",
                encoding="utf-8",
            )
            (root / "DEV_DOKU.md").write_text(
                "# DEV\n\n<!-- AUTO-STATUS:START -->\nAlt\n<!-- AUTO-STATUS:END -->\n",
                encoding="utf-8",
            )
            (root / "PROGRESS.md").write_text(
                "\n".join(
                    [
                        "# PROGRESS",
                        "",
                        "Stand: 2026-01-28",
                        "",
                        "- Gesamt: 4 Tasks",
                        "- Erledigt: 3 Tasks",
                        "- Offen: 1 Tasks",
                        "- Fortschritt: 75,00 %",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            changed = update_docs(root, write=True)

            self.assertEqual({root / "README.md", root / "DEV_DOKU.md"}, set(changed))
            content = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("Gesamt: 4 Tasks", content)


if __name__ == "__main__":
    unittest.main()
