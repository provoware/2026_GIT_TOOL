import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from undo_redo import UndoRedoAction, UndoRedoManager


class UndoRedoTests(unittest.TestCase):
    def test_undo_redo_runs_actions(self):
        manager = UndoRedoManager(limit=3)
        state = {"value": 0}

        def set_value(value: int) -> None:
            state["value"] = value

        manager.record(
            UndoRedoAction(
                name="Wert auf 1",
                undo=lambda: set_value(0),
                redo=lambda: set_value(1),
                metadata={"from": 0, "to": 1},
            )
        )
        set_value(1)
        action = manager.undo()
        self.assertEqual("Wert auf 1", action.name)
        self.assertEqual(0, state["value"])

        action = manager.redo()
        self.assertEqual("Wert auf 1", action.name)
        self.assertEqual(1, state["value"])


if __name__ == "__main__":
    unittest.main()
