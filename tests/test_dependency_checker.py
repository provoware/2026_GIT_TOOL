import tempfile
import unittest
from pathlib import Path

from system import dependency_checker


class DependencyCheckerTests(unittest.TestCase):
    def test_read_requirements_strips_inline_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            req_path = Path(tmp_dir) / "requirements.txt"
            req_path.write_text(
                "\n".join(
                    [
                        "# Kopfkommentar",
                        "ruff==0.1.0 # Inline-Kommentar",
                        "black>=23.0",
                        "",
                    ]
                ),
                encoding="utf-8",
            )

            requirements = dependency_checker._read_requirements(req_path)

            self.assertEqual(requirements, ["ruff==0.1.0", "black>=23.0"])


if __name__ == "__main__":
    unittest.main()
