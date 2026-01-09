import unittest
from pathlib import Path

from src.core.agent_assignment import assign_agent, load_agent_rules
from src.core.errors import AgentConflictError, AgentNotFoundError, TodoFormatError
from src.core.todo_parser import parse_todo_line


class AgentAssignmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ruleset = load_agent_rules(Path("config/agent_rules.json"))

    def test_parse_todo_line_valid(self) -> None:
        line = (
            "[ ] 2026-01-07 | Steuerung | To-Do logisch zu Agent zuordnen | "
            "fertig wenn: genau ein Agent entsteht"
        )
        item = parse_todo_line(line)
        self.assertEqual(item.area, "Steuerung")
        self.assertEqual(item.status, " ")

    def test_parse_todo_line_invalid(self) -> None:
        with self.assertRaises(TodoFormatError):
            parse_todo_line("Ungültiges Format")

    def test_assign_agent_single_match(self) -> None:
        line = (
            "[ ] 2026-01-07 | Steuerung | To-Do logisch zu Agent zuordnen | "
            "fertig wenn: genau ein Agent entsteht"
        )
        item = parse_todo_line(line)
        rule = assign_agent(item, self.ruleset)
        self.assertEqual(rule.agent_id, "agent_steuerung")

    def test_assign_agent_conflict(self) -> None:
        line = "[ ] 2026-01-07 | UI | UI und Logs verbessern | " "fertig wenn: klare Meldungen"
        item = parse_todo_line(line)
        with self.assertRaises(AgentConflictError):
            assign_agent(item, self.ruleset)

    def test_assign_agent_no_match(self) -> None:
        line = "[ ] 2026-01-07 | Sonstiges | Ohne Schlüsselwort | " "fertig wenn: passt"
        item = parse_todo_line(line)
        with self.assertRaises(AgentNotFoundError):
            assign_agent(item, self.ruleset)


if __name__ == "__main__":
    unittest.main()
