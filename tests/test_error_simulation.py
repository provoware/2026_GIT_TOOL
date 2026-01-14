import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "system"))

import error_simulation


class ErrorSimulationTests(unittest.TestCase):
    def test_simulations_return_cases(self):
        results = error_simulation.run_simulations()
        self.assertGreaterEqual(len(results), 3)
        for result in results:
            self.assertEqual("ok", result.status)
            self.assertTrue(result.message)
            self.assertTrue(result.hint)


if __name__ == "__main__":
    unittest.main()
