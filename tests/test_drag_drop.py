import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from drag_drop import parse_drop_data


class DragDropTests(unittest.TestCase):
    def test_parse_drop_data_handles_braces(self):
        raw = "{/tmp/Test Datei} /tmp/zweite.txt"
        paths = parse_drop_data(raw)
        self.assertEqual(2, len(paths))
        self.assertEqual(Path("/tmp/Test Datei"), paths[0])
        self.assertEqual(Path("/tmp/zweite.txt"), paths[1])


if __name__ == "__main__":
    unittest.main()
