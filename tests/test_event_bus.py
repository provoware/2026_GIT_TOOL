import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import event_bus


class EventBusTests(unittest.TestCase):
    def test_emit_calls_subscribers(self) -> None:
        bus = event_bus.EventBus()
        received = []

        def handler(evt: event_bus.Event) -> None:
            received.append(evt)

        bus.subscribe("demo_event", handler)
        bus.emit("demo_event", {"ok": True}, source="test")

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].name, "demo_event")
        self.assertEqual(received[0].payload["ok"], True)
        self.assertEqual(received[0].source, "test")

    def test_wildcard_receives_all_events(self) -> None:
        bus = event_bus.EventBus()
        received = []

        def handler(evt: event_bus.Event) -> None:
            received.append(evt.name)

        bus.subscribe("*", handler)
        bus.emit("one", {})
        bus.emit("two", {})

        self.assertEqual(received, ["one", "two"])


if __name__ == "__main__":
    unittest.main()
