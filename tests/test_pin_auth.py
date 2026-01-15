import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

from pin_auth import PinConfig, check_pin, save_state


class PinAuthTests(unittest.TestCase):
    def test_check_pin_disabled(self):
        config = PinConfig(
            enabled=False,
            pin_hint="",
            pin_hash="hash",
            salt="salt",
            max_attempts=3,
            lock_min_seconds=1,
            lock_max_seconds=2,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "pin_state.json"
            result = check_pin(config, state_path)
            self.assertEqual(result, 0)

    def test_check_pin_correct(self):
        config = PinConfig(
            enabled=True,
            pin_hint="",
            pin_hash="51438668b2cd007966b2f9887140fb75e5712fb53b42ae8f80eaed2ed32e2c6c",
            salt="provoware_default",
            max_attempts=3,
            lock_min_seconds=1,
            lock_max_seconds=2,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "pin_state.json"
            with patch("builtins.input", return_value="0000"):
                result = check_pin(config, state_path)
            self.assertEqual(result, 0)

    def test_check_pin_locked(self):
        config = PinConfig(
            enabled=True,
            pin_hint="",
            pin_hash="hash",
            salt="salt",
            max_attempts=3,
            lock_min_seconds=1,
            lock_max_seconds=2,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            state_path = Path(tmpdir) / "pin_state.json"
            locked_until = datetime.now(timezone.utc) + timedelta(seconds=30)
            save_state(
                state_path,
                {"failed_attempts": 2, "locked_until": locked_until.isoformat()},
            )
            result = check_pin(config, state_path)
            self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
